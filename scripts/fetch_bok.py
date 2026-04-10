"""한국은행 ECOS API 데이터 수집.

항목코드 오류 시 StatisticItemList로 후보를 조회해 로그에 출력한다.
네트워크 실패 시 기존 latest.json의 해당 지표 값을 유지한다.
"""
import os, json, requests
from datetime import datetime, timedelta
from pathlib import Path

BOK_KEY = os.environ.get("BOK_API_KEY", "")
API_BASE = "https://ecos.bok.or.kr/api"
MAX_RETRIES = 3
DATA_DIR = Path(__file__).parent.parent / "data"

# ── 지표 정의 ────────────────────────────────────────────
# key: (STAT_CODE, ITEM_CODE1, FREQ)
# ITEM_CODE1 이 None 이면 StatisticItemList 로 자동 탐색
BOK_SERIES = {
    "kospi":           ("802Y001", "0001000",   "D"),
    "kr2y":            ("817Y002", "010195000", "D"),
    "kr10y":           ("817Y002", "010210000", "D"),
    "usdkrw":          ("731Y001", "0000001",   "D"),
    "kr_delinquency":  ("901Y014", None,        "M"),   # 항목코드 미확정 → 자동 탐색
}

SIGNAL_RULES = {
    "kospi":          lambda v, c: "green" if c > 0 else "red",
    "usdkrw":         lambda v, c: "red" if c > 1 else "yellow" if c > 0 else "green",
    "kr10y":          lambda v, c: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr2y":           lambda v, c: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr_delinquency": lambda v, c: "red" if v > 1 else "yellow" if v > 0.5 else "green",
}

NOTES = {
    "kospi":          "",
    "usdkrw":         "환율 상승 = 원화 약세",
    "kr10y":          "",
    "kr2y":           "",
    "kr_delinquency": "1%+ 경고",
}


# ── 날짜 유틸 ────────────────────────────────────────────

def _date_range(freq: str) -> tuple[str, str]:
    """주기별 조회 시작/종료 문자열."""
    now = datetime.now()
    if freq == "D":
        start = now - timedelta(days=30)
        return start.strftime("%Y%m%d"), now.strftime("%Y%m%d")
    elif freq == "M":
        start = now - timedelta(days=365)
        return start.strftime("%Y%m"), now.strftime("%Y%m")
    else:  # Q
        return f"{now.year - 2}Q1", f"{now.year}Q4"


# ── StatisticItemList 로 항목코드 탐색 ────────────────────

def _lookup_item_codes(stat_code: str, keyword: str = "가계") -> list[dict]:
    """통계표의 항목 목록을 조회하고, keyword 가 포함된 항목을 반환."""
    url = f"{API_BASE}/StatisticItemList/{BOK_KEY}/json/kr/1/100/{stat_code}"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        if "StatisticItemList" not in data:
            err = data.get("RESULT", {}).get("MESSAGE", "Unknown")
            print(f"[BOK] ItemList {stat_code} error: {err}")
            return []

        rows = data["StatisticItemList"]["row"]
        matches = [r for r in rows if keyword in r.get("ITEM_NAME", "")]

        # 로그에 후보 출력
        print(f"[BOK] ItemList for {stat_code} — {len(rows)} items total, {len(matches)} matches for '{keyword}':")
        for r in matches[:10]:
            print(f"  → {r['ITEM_CODE']} : {r['ITEM_NAME']}")
        if not matches:
            print(f"  (no match for '{keyword}', showing first 5)")
            for r in rows[:5]:
                print(f"  → {r['ITEM_CODE']} : {r['ITEM_NAME']}")

        return matches
    except Exception as e:
        print(f"[BOK] ItemList lookup failed: {e}")
        return []


# ── 단일 지표 조회 ───────────────────────────────────────

def _fetch_one(key: str, stat_code: str, item_code: str | None, freq: str) -> dict | None:
    """ECOS StatisticSearch 로 단일 지표를 조회한다."""

    # 항목코드 미확정이면 자동 탐색
    if item_code is None:
        matches = _lookup_item_codes(stat_code, keyword="가계")
        if matches:
            item_code = matches[0]["ITEM_CODE"]
            print(f"[BOK] {key}: auto-selected item_code={item_code}")
        else:
            print(f"[BOK] {key}: no matching item_code found, skipping")
            return None

    start, end = _date_range(freq)
    url = f"{API_BASE}/StatisticSearch/{BOK_KEY}/json/kr/1/100/{stat_code}/{freq}/{start}/{end}/{item_code}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()

            if "StatisticSearch" not in data:
                err = data.get("RESULT", {}).get("MESSAGE", "Unknown error")
                if attempt == MAX_RETRIES - 1:
                    print(f"[BOK] {key}: {err}")
                    # 항목코드 오류 같으면 후보 출력
                    if "해당하는 데이터가 없습니다" in err:
                        _lookup_item_codes(stat_code)
                return None

            rows = data["StatisticSearch"]["row"]
            if len(rows) < 2:
                print(f"[BOK] {key}: insufficient data ({len(rows)} rows)")
                return None

            curr_val = float(rows[-1]["DATA_VALUE"].replace(",", ""))
            prev_val = float(rows[-2]["DATA_VALUE"].replace(",", ""))
            change = round(curr_val - prev_val, 4)
            change_pct = round(change / prev_val * 100, 2) if prev_val else 0

            signal_fn = SIGNAL_RULES.get(key, lambda v, c: "yellow")
            return {
                "value": round(curr_val, 2),
                "change": change,
                "change_pct": change_pct,
                "signal": signal_fn(curr_val, change_pct),
                "note": NOTES.get(key, ""),
            }
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"[BOK] {key} failed after {MAX_RETRIES} retries: {e}")
    return None


# ── 기존 값 fallback ─────────────────────────────────────

def _load_existing() -> dict:
    """기존 latest.json 에서 indicators 를 읽어온다."""
    try:
        latest = json.loads((DATA_DIR / "latest.json").read_text())
        return latest.get("indicators", {})
    except Exception:
        return {}


# ── 메인 ─────────────────────────────────────────────────

def fetch_bok() -> dict:
    """모든 한국 지표를 수집하여 dict 로 반환.
    실패한 지표는 기존 latest.json 값으로 fallback."""
    if not BOK_KEY:
        print("⚠ BOK_API_KEY not set, skipping Korean indicators")
        return {}

    existing = _load_existing()
    out = {}

    for key, (stat_code, item_code, freq) in BOK_SERIES.items():
        result = _fetch_one(key, stat_code, item_code, freq)
        if result:
            out[key] = result
        elif key in existing:
            print(f"[BOK] {key}: using cached value from latest.json")
            out[key] = existing[key]

    print(f"[BOK] Fetched {len(out)}/{len(BOK_SERIES)} Korean indicators")
    return out


if __name__ == "__main__":
    result = fetch_bok()
    print(json.dumps(result, indent=2, ensure_ascii=False))
