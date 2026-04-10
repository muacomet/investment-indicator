"""FRED + Yahoo Finance 데이터 수집 → data/latest.json, history.json 갱신"""
import os, json
from datetime import datetime, timezone
from pathlib import Path
from fredapi import Fred
import yfinance as yf
from calculate import judge_phase

DATA_DIR = Path(__file__).parent.parent / "data"
FRED_KEY = os.environ["FRED_API_KEY"]

FRED_SERIES = {
    "vix": "VIXCLS", "us10y": "DGS10", "us2y": "DGS2",
    "spread_2_10": "T10Y2Y", "tga": "WTREGEN",
    "rrp": "RRPONTSYD", "m2": "M2SL", "walcl": "WALCL",
}
YF_TICKERS = {
    "sp500": "^GSPC", "nasdaq": "^IXIC", "dxy": "DX-Y.NYB",
    "gold": "GC=F", "wti": "CL=F", "copper": "HG=F",
}


def fetch_fred(fred: Fred) -> dict:
    out = {}
    for key, sid in FRED_SERIES.items():
        try:
            s = fred.get_series(sid).dropna()
            prev, curr = float(s.iloc[-2]), float(s.iloc[-1])
            out[key] = {
                "value": curr,
                "change": round(curr - prev, 4),
                "change_pct": round((curr - prev) / prev * 100, 2) if prev else 0,
            }
        except Exception as e:
            print(f"[FRED] {key} failed: {e}")
    return out


def fetch_yahoo() -> dict:
    out = {}
    for key, tk in YF_TICKERS.items():
        try:
            hist = yf.Ticker(tk).history(period="5d")
            if len(hist) < 2:
                continue
            prev, curr = float(hist["Close"].iloc[-2]), float(hist["Close"].iloc[-1])
            out[key] = {
                "value": round(curr, 2),
                "change": round(curr - prev, 2),
                "change_pct": round((curr - prev) / prev * 100, 2),
            }
        except Exception as e:
            print(f"[YF] {key} failed: {e}")
    return out


def main():
    fred = Fred(api_key=FRED_KEY)
    indicators = {**fetch_fred(fred), **fetch_yahoo()}
    phase = judge_phase(indicators)

    latest = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "indicators": indicators,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "latest.json").write_text(json.dumps(latest, indent=2, ensure_ascii=False))

    # TODO: history.json 갱신 (90일 유지)
    print(f"✓ Updated {len(indicators)} indicators, phase={phase['status']}")


if __name__ == "__main__":
    main()
