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
from economic_calendar import get_upcoming_events

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
    "nq_futures": "NQ=F",
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
    "nq_futures":   lambda _, c: "green" if c > 0 else "red",
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
    "nq_futures": "나스닥100 선물 실시간",
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
                obs_date = s.index[-1].strftime("%Y-%m-%d")  # 실제 FRED 관측일

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
                    "_obs_date": obs_date,  # history 기록용 (실제 관측일)
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


def _yf_direct_fetch(ticker: str) -> tuple[float, float] | None:
    """Yahoo Finance v8 chart API 직접 호출 (yfinance 실패 시 fallback)."""
    import requests as req
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": "5d", "interval": "1d"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = req.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        # None 값 제거
        closes = [c for c in closes if c is not None]
        if len(closes) < 2:
            # 5d 부족 → 1mo 재시도
            params["range"] = "1mo"
            resp = req.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            closes = [c for c in closes if c is not None]
        if len(closes) >= 2:
            return closes[-2], closes[-1]
    except Exception as e:
        print(f"[YF-direct] {ticker}: {e}")
    return None


def fetch_yahoo() -> dict:
    """yf.download() → 실패 시 v8 API 직접 호출."""
    out = {}

    # 1차: yf.download()
    tickers_str = " ".join(YF_TICKERS.values())
    try:
        df = yf.download(tickers_str, period="1mo", progress=False, timeout=30)
        if not df.empty:
            for key, tk in YF_TICKERS.items():
                try:
                    if len(YF_TICKERS) > 1:
                        close = df[("Close", tk)].dropna()
                    else:
                        close = df["Close"].dropna()
                    if len(close) >= 2:
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
                    print(f"[YF] {key} parse error: {e}")
    except Exception as e:
        print(f"[YF] download error: {e}")

    # 2차: yf.download() 실패한 티커에 대해 v8 API 직접 호출
    missing = [k for k in YF_TICKERS if k not in out]
    if missing:
        print(f"[YF] {len(missing)} tickers missing, trying direct API: {missing}")
        for key in missing:
            tk = YF_TICKERS[key]
            result = _yf_direct_fetch(tk)
            if result:
                prev, curr = result
                change_pct = round((curr - prev) / prev * 100, 2)
                signal_fn = SIGNAL_RULES.get(key, lambda v, c: "yellow")
                out[key] = {
                    "value": round(curr, 2),
                    "change": round(curr - prev, 2),
                    "change_pct": change_pct,
                    "signal": signal_fn(round(curr, 2), change_pct),
                    "note": NOTES.get(key, ""),
                }
            else:
                print(f"[YF-direct] {key} ({tk}): also failed")

    print(f"[YF] Fetched {len(out)}/{len(YF_TICKERS)} Yahoo Finance indicators")
    return out


def _fetch_chart_data(ticker: str, range_str: str = "1mo") -> dict | None:
    """Yahoo v8 chart API에서 close/volume 배열 가져오기."""
    import requests as req
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": range_str, "interval": "1d"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = req.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()
        chart = data["chart"]["result"][0]
        closes = chart["indicators"]["quote"][0]["close"]
        volumes = chart["indicators"]["quote"][0].get("volume", [])
        # None 제거 (close/volume 쌍)
        if volumes:
            pairs = [(c, v) for c, v in zip(closes, volumes) if c is not None and v is not None]
            return {"closes": [p[0] for p in pairs], "volumes": [p[1] for p in pairs]}
        else:
            clean = [c for c in closes if c is not None]
            return {"closes": clean, "volumes": []}
    except Exception as e:
        print(f"[CHART] {ticker}: {e}")
    return None


def fetch_momentum_and_volume() -> tuple[dict, dict]:
    """S&P500, QQQ, SCHD의 모멘텀 + 거래량을 Yahoo API에서 직접 계산."""
    momentum = {}
    volume = {}
    targets = {"sp500": "^GSPC", "qqq": "QQQ", "schd": "SCHD"}

    for key, tk in targets.items():
        chart = _fetch_chart_data(tk, "3mo")
        if not chart or len(chart["closes"]) < 5:
            print(f"[MOM] {key}: insufficient chart data")
            continue

        closes = chart["closes"]
        volumes = chart["volumes"]

        # ── 모멘텀 ──
        # 연속 상승일
        consecutive = 0
        for i in range(len(closes) - 1, 0, -1):
            if closes[i] > closes[i - 1]:
                consecutive += 1
            else:
                break

        # 전고점(ATH) 대비
        ath = max(closes)
        current = closes[-1]
        ath_pct = round((current - ath) / ath * 100, 2) if ath else 0

        # 당일 등락률
        daily_chg = round((closes[-1] - closes[-2]) / closes[-2] * 100, 2) if len(closes) >= 2 else 0

        momentum[key] = {
            "consecutive_up": consecutive,
            "ath": round(ath, 2),
            "ath_distance_pct": ath_pct,
            "daily_change_pct": daily_chg,
        }

        # ── 거래량 ──
        if len(volumes) >= 5:
            today_vol = volumes[-1]
            avg_20 = sum(volumes[-20:]) / min(len(volumes), 20)
            vol_ratio = round(today_vol / avg_20, 2) if avg_20 > 0 else 0

            up_vols, down_vols = [], []
            for i in range(1, len(closes)):
                if i < len(volumes):
                    if closes[i] > closes[i - 1]:
                        up_vols.append(volumes[i])
                    else:
                        down_vols.append(volumes[i])

            volume[key] = {
                "volume": int(today_vol),
                "volume_avg_20d": int(avg_20),
                "volume_ratio": vol_ratio,
                "up_day_avg_vol": int(sum(up_vols) / len(up_vols)) if up_vols else 0,
                "down_day_avg_vol": int(sum(down_vols) / len(down_vols)) if down_vols else 0,
            }

    print(f"[MOM] Calculated momentum for {list(momentum.keys())}")
    return momentum, volume


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
        # FRED weekly/monthly 시리즈는 실제 관측일(_obs_date)을 사용해 중복 방지
        entry_date = data.get("_obs_date") or today
        existing = [e for e in history[key] if e["date"] == entry_date]
        if existing:
            existing[0]["value"] = data["value"]
        else:
            history[key].append({"date": entry_date, "value": data["value"]})
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

    # history 저장 후에는 _obs_date 메타 필드 제거 (latest.json 공개 스키마)
    for data in indicators.values():
        data.pop("_obs_date", None)

    phase = judge_phase(indicators, history)

    # Momentum + Volume (Yahoo API에서 직접 계산)
    momentum, volume = fetch_momentum_and_volume()

    # Calendar
    calendar_events = get_upcoming_events(30)

    latest = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "indicators": indicators,
        "momentum": momentum,
        "volume": volume,
        "calendar": calendar_events,
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
