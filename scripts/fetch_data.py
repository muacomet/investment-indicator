"""FRED + Yahoo Finance 데이터 수집 → data/latest.json, history.json 갱신"""
import os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fredapi import Fred
import yfinance as yf
from calculate import judge_phase
from fetch_bok import fetch_bok

DATA_DIR = Path(__file__).parent.parent / "data"
FRED_KEY = os.environ.get("FRED_API_KEY", "")

FRED_SERIES = {
    "vix": "VIXCLS", "us10y": "DGS10", "us2y": "DGS2",
    "spread_2_10": "T10Y2Y", "tga": "WTREGEN",
    "rrp": "RRPONTSYD", "m2": "M2SL", "fed_balance": "WALCL",
    # 신용·가계 건전성 (분기)
    "us_cc_delinq": "DRCCLACBS",
    "us_auto_delinq": "DRALACBN",
    "us_mortgage_delinq": "DRSFRMACBS",
    "us_saving_rate": "PSAVERT",
}
YF_TICKERS = {
    "sp500": "^GSPC", "nasdaq": "^IXIC", "dxy": "DX-Y.NYB",
    "gold": "GC=F", "wti": "CL=F", "copper": "HG=F",
}

# 신호 판정 기준
SIGNAL_RULES = {
    "vix":          lambda v, _: "red" if v > 30 else "yellow" if v > 20 else "green",
    "sp500":        lambda _, c: "green" if c > 0 else "red",
    "nasdaq":       lambda _, c: "green" if c > 0 else "red",
    "dxy":          lambda _, c: "yellow" if abs(c) > 1 else "green",
    "us10y":        lambda v, _: "red" if v > 5 else "yellow" if v > 4 else "green",
    "us2y":         lambda v, _: "red" if v > 5 else "yellow" if v > 4 else "green",
    "spread_2_10":  lambda v, _: "red" if v < 0 else "green",
    "gold":         lambda _, c: "green" if c > 0 else "yellow",
    "wti":          lambda _, c: "yellow" if abs(c) > 3 else "green",
    "copper":       lambda _, c: "green" if c > 0 else "yellow",
    "tga":          lambda _, c: "green" if c < 0 else "yellow",
    "rrp":          lambda _, c: "green" if c < 0 else "yellow",
    "m2":           lambda _, c: "green" if c > 0 else "yellow",
    "fed_balance":  lambda _, c: "yellow" if c < 0 else "green",
    # 신용·가계 건전성
    "us_cc_delinq":       lambda v, _: "red" if v > 3 else "yellow" if v > 2 else "green",
    "us_auto_delinq":     lambda v, _: "red" if v > 3 else "yellow" if v > 2 else "green",
    "us_mortgage_delinq": lambda v, _: "red" if v > 4 else "yellow" if v > 2.5 else "green",
    "us_saving_rate":     lambda v, _: "red" if v < 3 else "yellow" if v < 5 else "green",
    # 한국 지표
    "kospi":          lambda _, c: "green" if c > 0 else "red",
    "krw_usd":        lambda _, c: "red" if c > 1 else "yellow" if c > 0 else "green",
    "kr10y":          lambda v, _: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr2y":           lambda v, _: "red" if v > 4 else "yellow" if v > 3 else "green",
    "kr_household_delinq": lambda v, _: "red" if v > 1 else "yellow" if v > 0.5 else "green",
    "kr_saving_rate": lambda v, _: "red" if v < 30 else "yellow" if v < 35 else "green",
}

NOTES = {
    "vix": "20 이하 안정 / 30+ 위험",
    "sp500": "200일선 대비 확인 필요",
    "nasdaq": "",
    "dxy": "달러 약세 시 위험자산 유리",
    "us10y": "금리 하락 = 채권 가격 상승",
    "us2y": "",
    "spread_2_10": "역전 시 경기침체 경고",
    "gold": "안전자산 선호 시 상승",
    "wti": "",
    "copper": "경기 선행 지표",
    "tga": "TGA 감소 = 유동성 공급",
    "rrp": "RRP 감소 = 유동성 증가",
    "m2": "M2 증가 = 유동성 확대",
    "fed_balance": "QT 진행 중",
    # 신용·가계 건전성
    "us_cc_delinq": "3%+ 경고",
    "us_auto_delinq": "3%+ 경고",
    "us_mortgage_delinq": "4%+ 위험",
    "us_saving_rate": "5% 이상 건전",
    # 한국 지표
    "kospi": "",
    "krw_usd": "환율 상승 = 원화 약세",
    "kr10y": "",
    "kr2y": "",
    "kr_household_delinq": "1%+ 경고",
    "kr_saving_rate": "국민계정 기준 분기",
}

MAX_RETRIES = 3


def fetch_fred(fred: Fred) -> dict:
    out = {}
    for key, sid in FRED_SERIES.items():
        for attempt in range(MAX_RETRIES):
            try:
                s = fred.get_series(sid).dropna()
                prev, curr = float(s.iloc[-2]), float(s.iloc[-1])
                change_pct = round((curr - prev) / prev * 100, 2) if prev else 0
                signal_fn = SIGNAL_RULES.get(key, lambda v, c: "yellow")
                out[key] = {
                    "value": curr,
                    "change": round(curr - prev, 4),
                    "change_pct": change_pct,
                    "signal": signal_fn(curr, change_pct),
                    "note": NOTES.get(key, ""),
                }
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"[FRED] {key} failed after {MAX_RETRIES} retries: {e}")
    return out


def fetch_yahoo() -> dict:
    out = {}
    for key, tk in YF_TICKERS.items():
        for attempt in range(MAX_RETRIES):
            try:
                hist = yf.Ticker(tk).history(period="5d")
                if len(hist) < 2:
                    break
                prev, curr = float(hist["Close"].iloc[-2]), float(hist["Close"].iloc[-1])
                change_pct = round((curr - prev) / prev * 100, 2)
                signal_fn = SIGNAL_RULES.get(key, lambda v, c: "yellow")
                out[key] = {
                    "value": round(curr, 2),
                    "change": round(curr - prev, 2),
                    "change_pct": change_pct,
                    "signal": signal_fn(curr, change_pct),
                    "note": NOTES.get(key, ""),
                }
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"[YF] {key} failed after {MAX_RETRIES} retries: {e}")
    return out


def update_history(indicators: dict) -> dict:
    """history.json에 오늘 데이터 추가, 90일 초과분 삭제."""
    history_path = DATA_DIR / "history.json"
    try:
        history = json.loads(history_path.read_text())
        if not isinstance(history, dict):
            history = {}
    except (json.JSONDecodeError, FileNotFoundError):
        history = {}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")

    for key, data in indicators.items():
        if key not in history:
            history[key] = []

        # 오늘 날짜 이미 있으면 업데이트, 없으면 추가
        existing = [e for e in history[key] if e["date"] == today]
        if existing:
            existing[0]["value"] = data["value"]
        else:
            history[key].append({"date": today, "value": data["value"]})

        # 90일 초과 삭제
        history[key] = [e for e in history[key] if e["date"] >= cutoff]
        # 날짜순 정렬
        history[key].sort(key=lambda e: e["date"])

    return history


def main():
    if not FRED_KEY:
        print("⚠ FRED_API_KEY not set, fetching Yahoo Finance data only")
        fred_data = {}
    else:
        fred = Fred(api_key=FRED_KEY)
        fred_data = fetch_fred(fred)

    yf_data = fetch_yahoo()
    bok_data = fetch_bok()
    indicators = {**fred_data, **yf_data, **bok_data}

    if not indicators:
        print("✗ No data fetched, skipping update")
        return

    phase = judge_phase(indicators)

    latest = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "indicators": indicators,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "latest.json").write_text(
        json.dumps(latest, indent=2, ensure_ascii=False)
    )

    history = update_history(indicators)
    (DATA_DIR / "history.json").write_text(
        json.dumps(history, indent=2, ensure_ascii=False)
    )

    print(f"✓ Updated {len(indicators)} indicators, phase={phase['status']}")


if __name__ == "__main__":
    main()
