"""한국은행 ECOS API 데이터 수집"""
import os
import requests
from datetime import datetime, timedelta

BOK_KEY = os.environ.get("BOK_API_KEY", "")
BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"
MAX_RETRIES = 3

# {key: (STAT_CODE, ITEM_CODE1, ITEM_CODE2, FREQ)}
# FREQ: D=일별, M=월별, Q=분기
BOK_SERIES = {
    "kospi":              ("802Y001", "0001000",    None,      "D"),
    "kr10y":              ("817Y002", "010210000",  None,      "D"),
    "kr2y":               ("817Y002", "010200000",  None,      "D"),
    "krw_usd":            ("731Y001", "0000001",    "0000200", "D"),
    "kr_household_delinq":("901Y009", "BECBLA02A",  None,      "M"),
    "kr_saving_rate":     ("200Y004", "10114",      None,      "Q"),
}

SIGNAL_RULES = {
    "kospi":          lambda v, c: "green" if c > 0 else "red",
    "krw_usd":        lambda v, c: "red" if c > 1 else "yellow" if c > 0 else "green",
    "kr10y":          lambda v, c: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr2y":           lambda v, c: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr_household_delinq": lambda v, c: "red" if v > 1 else "yellow" if v > 0.5 else "green",
    "kr_saving_rate": lambda v, c: "red" if v < 30 else "yellow" if v < 35 else "green",
}

NOTES = {
    "kospi": "",
    "krw_usd": "환율 상승 = 원화 약세",
    "kr10y": "",
    "kr2y": "",
    "kr_household_delinq": "1%+ 경고",
    "kr_saving_rate": "국민계정 기준 분기",
}


def _date_range(freq: str) -> tuple[str, str]:
    """주기에 맞는 조회 기간 반환."""
    now = datetime.now()
    if freq == "D":
        start = now - timedelta(days=30)
        return start.strftime("%Y%m%d"), now.strftime("%Y%m%d")
    elif freq == "M":
        start = now - timedelta(days=180)
        return start.strftime("%Y%m"), now.strftime("%Y%m")
    else:  # Q
        start = now - timedelta(days=730)
        return start.strftime("%Y%mQ%q").replace("Q%q", "Q1"), now.strftime("%Y%mQ%q").replace("Q%q", "Q4")


def _format_date(freq: str) -> tuple[str, str]:
    """주기별 시작/종료 날짜 문자열."""
    now = datetime.now()
    if freq == "D":
        start = now - timedelta(days=30)
        return start.strftime("%Y%m%d"), now.strftime("%Y%m%d")
    elif freq == "M":
        start = now - timedelta(days=180)
        return start.strftime("%Y%m"), now.strftime("%Y%m")
    else:  # Q
        year = now.year
        return f"{year - 2}Q1", f"{year}Q4"


def _fetch_one(key: str, stat_code: str, item1: str, item2: str | None, freq: str) -> dict | None:
    """ECOS API에서 단일 지표 조회."""
    start, end = _format_date(freq)

    # URL 구성: /StatisticSearch/{key}/json/kr/1/100/{stat}/{freq}/{start}/{end}/{item1}[/{item2}]
    url_parts = [BASE_URL, BOK_KEY, "json", "kr", "1", "100", stat_code, freq, start, end, item1]
    if item2:
        url_parts.append(item2)
    url = "/".join(url_parts)

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()

            if "StatisticSearch" not in data:
                err = data.get("RESULT", {}).get("MESSAGE", "Unknown error")
                print(f"[BOK] {key}: {err}")
                return None

            rows = data["StatisticSearch"]["row"]
            if len(rows) < 2:
                return None

            # 최신 2개 값으로 변동 계산
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


def fetch_bok() -> dict:
    """모든 한국 지표를 수집하여 dict로 반환."""
    if not BOK_KEY:
        print("⚠ BOK_API_KEY not set, skipping Korean indicators")
        return {}

    out = {}
    for key, (stat_code, item1, item2, freq) in BOK_SERIES.items():
        result = _fetch_one(key, stat_code, item1, item2, freq)
        if result:
            out[key] = result

    print(f"[BOK] Fetched {len(out)}/{len(BOK_SERIES)} Korean indicators")
    return out


if __name__ == "__main__":
    result = fetch_bok()
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
