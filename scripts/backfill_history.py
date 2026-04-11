"""히스토리 백필: 최근 7일치 데이터를 history.json에 채운다. 1회성 스크립트."""
import os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fredapi import Fred
import yfinance as yf
import requests

DATA_DIR = Path(__file__).parent.parent / "data"
FRED_KEY = os.environ.get("FRED_API_KEY", "")
BOK_KEY = os.environ.get("BOK_API_KEY", "")
BOK_API = "https://ecos.bok.or.kr/api"

FRED_SERIES = {
    "vix": "VIXCLS", "us10y": "DGS10", "us2y": "DGS2",
    "spread_2_10": "T10Y2Y", "tga": "WTREGEN",
    "rrp": "RRPONTSYD", "m2": "M2SL", "fed_balance": "WALCL",
    "fed_rate": "DFEDTARU",
    "us_cc_delinq": "DRCCLACBS", "us_auto_delinq": "DRALACBN",
    "us_mortgage_delinq": "DRSFRMACBS", "us_saving_rate": "PSAVERT",
}

YF_TICKERS = {
    "sp500": "^GSPC", "nasdaq": "^IXIC", "dxy": "DX-Y.NYB",
    "gold": "GC=F", "wti": "CL=F", "copper": "HG=F",
}

BOK_STAT = {
    "kospi":  ("802Y001", "0001000"),
    "kr2y":   ("817Y002", "010195000"),
    "kr10y":  ("817Y002", "010210000"),
    "usdkrw": ("731Y001", "0000001"),
}

# KeyStatisticList에서 가져올 지표 (backfill은 시계열 없으므로 최신 1건만)
BOK_KEY_STAT = {
    "kr_rate": "한국은행 기준금리",
}


def backfill_fred(fred: Fred, days: int = 10) -> dict:
    out = {}
    for key, sid in FRED_SERIES.items():
        try:
            s = fred.get_series(sid).dropna().tail(days)
            out[key] = [
                {"date": idx.strftime("%Y-%m-%d"), "value": round(float(val), 4)}
                for idx, val in s.items()
            ]
            print(f"[FRED] {key}: {len(out[key])} days")
        except Exception as e:
            print(f"[FRED] {key} failed: {e}")
    return out


def backfill_yahoo(days: int = 10) -> dict:
    out = {}
    for key, tk in YF_TICKERS.items():
        try:
            hist = yf.Ticker(tk).history(period=f"{days}d")
            out[key] = [
                {"date": idx.strftime("%Y-%m-%d"), "value": round(float(row["Close"]), 2)}
                for idx, row in hist.iterrows()
            ]
            print(f"[YF] {key}: {len(out[key])} days")
        except Exception as e:
            print(f"[YF] {key} failed: {e}")
    return out


def backfill_bok(days: int = 10) -> dict:
    if not BOK_KEY:
        return {}
    out = {}
    now = datetime.now()
    start = (now - timedelta(days=days + 5)).strftime("%Y%m%d")
    end = now.strftime("%Y%m%d")

    for key, (stat_code, item_code) in BOK_STAT.items():
        try:
            url = f"{BOK_API}/StatisticSearch/{BOK_KEY}/json/kr/1/100/{stat_code}/D/{start}/{end}/{item_code}"
            resp = requests.get(url, timeout=15)
            data = resp.json()
            if "StatisticSearch" not in data:
                print(f"[BOK] {key}: {data.get('RESULT', {}).get('MESSAGE', '?')}")
                continue
            rows = data["StatisticSearch"]["row"]
            out[key] = [
                {"date": f"{r['TIME'][:4]}-{r['TIME'][4:6]}-{r['TIME'][6:8]}",
                 "value": round(float(r["DATA_VALUE"].replace(",", "")), 4)}
                for r in rows if r.get("DATA_VALUE")
            ]
            print(f"[BOK] {key}: {len(out[key])} days")
        except Exception as e:
            print(f"[BOK] {key} failed: {e}")
    return out


def main():
    history_path = DATA_DIR / "history.json"
    try:
        history = json.loads(history_path.read_text())
        if not isinstance(history, dict):
            history = {}
    except Exception:
        history = {}

    # FRED
    if FRED_KEY:
        fred = Fred(api_key=FRED_KEY)
        fred_hist = backfill_fred(fred)
    else:
        fred_hist = {}

    yf_hist = backfill_yahoo()
    bok_hist = backfill_bok()

    # 병합: 기존 데이터 유지하면서 백필 데이터 추가
    for source in [fred_hist, yf_hist, bok_hist]:
        for key, entries in source.items():
            if key not in history:
                history[key] = []

            existing_dates = {e["date"] for e in history[key]}
            for entry in entries:
                if entry["date"] not in existing_dates:
                    history[key].append(entry)

            history[key].sort(key=lambda e: e["date"])

    DATA_DIR.mkdir(exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False))

    total = sum(len(v) for v in history.values())
    print(f"✓ Backfilled history: {len(history)} indicators, {total} total data points")


if __name__ == "__main__":
    main()
