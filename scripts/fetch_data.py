"""FRED + Yahoo Finance 데이터 수집 → data/latest.json, history.json 갱신"""
import os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fredapi import Fred
import yfinance as yf
from config import (
    VIX_STABLE, VIX_CAUTION, VIX_WARNING, VIX_PANIC,
    TGA_HIGH, TGA_LOW, RRP_HIGH, RRP_LOW,
)
from calculate import judge_phase
from fetch_bok import fetch_bok

DATA_DIR = Path(__file__).parent.parent / "data"
FRED_KEY = os.environ.get("FRED_API_KEY", "")

FRED_SERIES = {
    "vix": "VIXCLS", "us10y": "DGS10", "us2y": "DGS2",
    "spread_2_10": "T10Y2Y", "tga": "WTREGEN",
    "rrp": "RRPONTSYD", "m2": "M2SL", "fed_balance": "WALCL",
    "fed_rate": "DFEDTARU",
    # 신용·가계 건전성
    "us_cc_delinq": "DRCCLACBS",
    "us_auto_delinq": "DRALACBN",
    "us_mortgage_delinq": "DRSFRMACBS",
    "us_saving_rate": "PSAVERT",
}

# TGA(WTREGEN): millions → billions, RRP(RRPONTSYD): billions 그대로
# WALCL: millions → billions, M2SL: billions 그대로
UNIT_CONVERSIONS = {
    "tga": 1e-3,         # millions → billions
    "fed_balance": 1e-3, # millions → billions
}

YF_TICKERS = {
    "sp500": "^GSPC", "nasdaq": "^IXIC",
    "qqq": "QQQ", "schd": "SCHD",
    "dxy": "DX-Y.NYB",
    "gold": "GC=F", "wti": "CL=F", "copper": "HG=F",
}

# 신호 판정 기준
SIGNAL_RULES = {
    "vix":          lambda v, _: "red" if v >= VIX_WARNING else "orange" if v >= VIX_CAUTION else "yellow" if v > VIX_STABLE else "green",
    "sp500":        lambda _, c: "green" if c > 0 else "red",
    "nasdaq":       lambda _, c: "green" if c > 0 else "red",
    "qqq":          lambda _, c: "green" if c > 0 else "red",
    "schd":         lambda _, c: "green" if c > 0 else "red",
    "dxy":          lambda _, c: "yellow" if abs(c) > 1 else "green",
    "us10y":        lambda v, _: "red" if v > 5 else "yellow" if v > 4 else "green",
    "us2y":         lambda v, _: "red" if v > 5 else "yellow" if v > 4 else "green",
    "spread_2_10":  lambda v, _: "red" if v < 0 else "green",
    "fed_rate":     lambda v, _: "yellow",
    "gold":         lambda _, c: "green" if c > 0 else "yellow",
    "wti":          lambda _, c: "yellow" if abs(c) > 3 else "green",
    "copper":       lambda _, c: "green" if c > 0 else "yellow",
    "tga":          lambda v, _: "red" if v > TGA_HIGH else "yellow" if v < TGA_LOW else "green",
    "rrp":          lambda v, _: "red" if v > RRP_HIGH else "yellow" if v <= RRP_LOW else "green",
    "m2":           lambda _, c: "green" if c > 0 else "yellow",
    "fed_balance":  lambda _, c: "yellow" if c < 0 else "green",
    "us_cc_delinq":       lambda v, _: "red" if v > 3 else "yellow" if v > 2 else "green",
    "us_auto_delinq":     lambda v, _: "red" if v > 3 else "yellow" if v > 2 else "green",
    "us_mortgage_delinq": lambda v, _: "red" if v > 4 else "yellow" if v > 2.5 else "green",
    "us_saving_rate":     lambda v, _: "red" if v < 3 else "yellow" if v < 5 else "green",
}

NOTES = {
    "vix": f"20 안정 / 25 불안 / 30 위험 / 60 패닉",
    "sp500": "",
    "nasdaq": "",
    "qqq": "나스닥100 추종 ETF",
    "schd": "미국 배당성장 ETF",
    "dxy": "6개 주요 통화 대비 달러 가치",
    "us10y": "기준금리 +0.5~1%가 정상",
    "us2y": "",
    "spread_2_10": "역전 시 경기침체 경고",
    "fed_rate": "FOMC 정책금리 상단",
    "gold": "안전자산 선호 시 상승",
    "wti": "",
    "copper": "경기 선행 지표",
    "tga": "5천억~1조 정상 / 1조+ 흡수 / 5천억- 재충전 (단위: B$)",
    "rrp": "역사적 고점 2.5조 (단위: B$)",
    "m2": "M2 증가 = 유동성 확대",
    "fed_balance": "QT 진행 중 (단위: B$)",
    "us_cc_delinq": "3%+ 경고",
    "us_auto_delinq": "3%+ 경고",
    "us_mortgage_delinq": "4%+ 위험",
    "us_saving_rate": "5% 이상 건전",
}

MAX_RETRIES = 3


def fetch_fred(fred: Fred) -> dict:
    out = {}
    for key, sid in FRED_SERIES.items():
        for attempt in range(MAX_RETRIES):
            try:
                s = fred.get_series(sid).dropna()
                prev, curr = float(s.iloc[-2]), float(s.iloc[-1])

                # 단위 변환
                conv = UNIT_CONVERSIONS.get(key, 1)
                curr *= conv
                prev *= conv

                change_pct = round((curr - prev) / prev * 100, 2) if prev else 0
                signal_fn = SIGNAL_RULES.get(key, lambda v, c: "yellow")

                value = round(curr, 4) if conv == 1 else round(curr, 2)
                out[key] = {
                    "value": value,
                    "change": round(curr - prev, 4),
                    "change_pct": change_pct,
                    "signal": signal_fn(value, change_pct),
                    "note": NOTES.get(key, ""),
                }

                # Sanity check for TGA/RRP
                if key == "tga" and not (100 < value < 2000):
                    print(f"[WARN] TGA value {value}B$ outside expected 100-2000 range")
                if key == "rrp" and value > 3000:
                    print(f"[WARN] RRP value {value}B$ unusually high")

                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"[FRED] {key} failed after {MAX_RETRIES} retries: {e}")
    return out


def fetch_yahoo() -> dict:
    """yf.download()로 일괄 다운로드 후 개별 지표 추출."""
    out = {}
    tickers_str = " ".join(YF_TICKERS.values())

    for attempt in range(MAX_RETRIES):
        try:
            # yf.download: group_by='ticker', 복수 티커 일괄 다운로드
            df = yf.download(tickers_str, period="1mo", progress=False, timeout=30)
            if df.empty:
                print(f"[YF] download returned empty (attempt {attempt+1})")
                continue

            for key, tk in YF_TICKERS.items():
                try:
                    # 복수 티커: MultiIndex columns (ticker, field)
                    if len(YF_TICKERS) > 1:
                        close = df[("Close", tk)].dropna()
                    else:
                        close = df["Close"].dropna()

                    if len(close) < 2:
                        print(f"[YF] {key} ({tk}): insufficient data ({len(close)} rows)")
                        continue

                    prev, curr = float(close.iloc[-2]), float(close.iloc[-1])
                    change_pct = round((curr - prev) / prev * 100, 2)
                    signal_fn = SIGNAL_RULES.get(key, lambda v, c: "yellow")
                    out[key] = {
                        "value": round(curr, 2),
                        "change": round(curr - prev, 2),
                        "change_pct": change_pct,
                        "signal": signal_fn(round(curr, 2), change_pct),
                        "note": NOTES.get(key, ""),
                    }
                except Exception as e:
                    print(f"[YF] {key} ({tk}) parse error: {e}")
            break  # 성공 시 재시도 불필요
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"[YF] download failed after {MAX_RETRIES} retries: {e}")

    print(f"[YF] Fetched {len(out)}/{len(YF_TICKERS)} Yahoo Finance indicators")
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
        existing = [e for e in history[key] if e["date"] == today]
        if existing:
            existing[0]["value"] = data["value"]
        else:
            history[key].append({"date": today, "value": data["value"]})
        history[key] = [e for e in history[key] if e["date"] >= cutoff]
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

    # history 먼저 로드 (calculate에서 4주 추세 계산에 필요)
    history = update_history(indicators)

    phase = judge_phase(indicators, history)

    latest = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "indicators": indicators,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "latest.json").write_text(
        json.dumps(latest, indent=2, ensure_ascii=False)
    )
    (DATA_DIR / "history.json").write_text(
        json.dumps(history, indent=2, ensure_ascii=False)
    )

    print(f"✓ Updated {len(indicators)} indicators, phase={phase['status']} (score={phase['score']})")


if __name__ == "__main__":
    main()
