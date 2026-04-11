"""한국은행 ECOS API 데이터 수집.

StatisticSearch API: KOSPI, 국고채, 환율 등 일반 지표
KeyStatisticList API: 100대 통계지표 (가계대출 연체율 K051 등)

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

# ── StatisticSearch 지표 ─────────────────────────────────
# key: (STAT_CODE, ITEM_CODE, FREQ)
BOK_SERIES = {
    "kospi":  ("802Y001", "0001000",   "D"),
    "kr2y":   ("817Y002", "010195000", "D"),
    "kr10y":  ("817Y002", "010210000", "D"),
    "usdkrw": ("731Y001", "0000001",   "D"),
}

# ── KeyStatisticList 지표 (100대 핵심 통계) ────────────────
# key: KEYSTAT_NAME (지표 이름으로 매칭)
KEY_STAT_SERIES = {
    "kr_delinquency": "연체율",       # "가계대출 연체율" 또는 "연체율" 포함 항목 매칭
    "kr_rate":        "한국은행 기준금리",  # 한국은행 기준금리
}

# ── 신호 판정 / 노트 ─────────────────────────────────────
SIGNAL_RULES = {
    "kospi":          lambda v, c: "green" if c > 0 else "red",
    "usdkrw":         lambda v, c: "red" if c > 1 else "yellow" if c > 0 else "green",
    "kr10y":          lambda v, c: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr2y":           lambda v, c: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr_delinquency": lambda v, c: "red" if v > 1 else "yellow" if v > 0.5 else "green",
    "kr_rate":        lambda v, c: "yellow",
}

NOTES = {
    "kospi":          "",
    "usdkrw":         "환율 상승 = 원화 약세",
    "kr10y":          "",
    "kr2y":           "",
    "kr_delinquency": "1%+ 경고",
    "kr_rate":        "한국은행 기준금리",
}


# ── 날짜 유틸 ────────────────────────────────────────────

def _date_range(freq: str) -> tuple[str, str]:
    now = datetime.now()
    if freq == "D":
        start = now - timedelta(days=30)
        return start.strftime("%Y%m%d"), now.strftime("%Y%m%d")
    elif freq == "M":
        start = now - timedelta(days=365)
        return start.strftime("%Y%m"), now.strftime("%Y%m")
    else:
        return f"{now.year - 2}Q1", f"{now.year}Q4"


# ── StatisticSearch 조회 ─────────────────────────────────

def _fetch_stat(key: str, stat_code: str, item_code: str, freq: str) -> dict | None:
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


# ── KeyStatisticList 조회 (100대 핵심 통계) ────────────────

def _fetch_key_stat(key: str, keyword: str) -> dict | None:
    """KeyStatisticList API에서 KEYSTAT_NAME에 keyword가 포함된 지표를 조회."""
    url = f"{API_BASE}/KeyStatisticList/{BOK_KEY}/json/kr/1/100/"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()

            if "KeyStatisticList" not in data:
                err = data.get("RESULT", {}).get("MESSAGE", "Unknown error")
                if attempt == MAX_RETRIES - 1:
                    print(f"[BOK] KeyStat {key}: {err}")
                continue

            rows = data["KeyStatisticList"]["row"]

            # KEYSTAT_NAME에 keyword 포함된 항목 찾기
            matches = [r for r in rows if keyword in r.get("KEYSTAT_NAME", "")]

            if not matches:
                if attempt == MAX_RETRIES - 1:
                    print(f"[BOK] KeyStat {key}: '{keyword}' not found in {len(rows)} items")
                    # 디버그: 전체 KEYSTAT_NAME 출력
                    names = [r.get("KEYSTAT_NAME", "?") for r in rows]
                    print(f"  → available: {names}")
                continue

            row = matches[0]
            print(f"[BOK] KeyStat {key}: matched '{row['KEYSTAT_NAME']}' = {row['DATA_VALUE']} ({row.get('CYCLE', '?')})")

            curr_str = row.get("DATA_VALUE", "0").replace(",", "")
            curr_val = float(curr_str) if curr_str else 0

            signal_fn = SIGNAL_RULES.get(key, lambda v, c: "yellow")
            return {
                "value": round(curr_val, 2),
                "change": 0,
                "change_pct": 0,
                "signal": signal_fn(curr_val, 0),
                "note": NOTES.get(key, ""),
            }
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"[BOK] KeyStat {key} failed after {MAX_RETRIES} retries: {e}")
    return None


# ── 기존 값 fallback ─────────────────────────────────────

def _load_existing() -> dict:
    try:
        latest = json.loads((DATA_DIR / "latest.json").read_text())
        return latest.get("indicators", {})
    except Exception:
        return {}


# ── 메인 ─────────────────────────────────────────────────

def fetch_bok() -> dict:
    """모든 한국 지표를 수집하여 dict 로 반환."""
    if not BOK_KEY:
        print("⚠ BOK_API_KEY not set, skipping Korean indicators")
        return {}

    existing = _load_existing()
    out = {}
    total = len(BOK_SERIES) + len(KEY_STAT_SERIES)

    # StatisticSearch 지표
    for key, (stat_code, item_code, freq) in BOK_SERIES.items():
        result = _fetch_stat(key, stat_code, item_code, freq)
        if result:
            out[key] = result
        elif key in existing:
            print(f"[BOK] {key}: using cached value")
            out[key] = existing[key]

    # KeyStatisticList 지표 (100대 핵심 통계)
    for key, key_stat_code in KEY_STAT_SERIES.items():
        result = _fetch_key_stat(key, key_stat_code)
        if result:
            out[key] = result
        elif key in existing:
            print(f"[BOK] {key}: using cached value")
            out[key] = existing[key]

    print(f"[BOK] Fetched {len(out)}/{total} Korean indicators")
    return out


if __name__ == "__main__":
    result = fetch_bok()
    print(json.dumps(result, indent=2, ensure_ascii=False))
