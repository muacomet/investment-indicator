"""종합 국면 판정 로직 (Multi-factor scoring).

규칙 기반 점수제. config.py의 상수로 튜닝 가능.
score 범위: -3 ~ 6+
  >= SCORE_STRONG_BUY (4) → strong_buy
  >= SCORE_BUY       (2) → buy
  >= SCORE_NEUTRAL   (0) → neutral
  >= SCORE_CAUTION  (-2) → caution
  <  SCORE_CAUTION       → wait
"""
from config import (
    VIX_STABLE, VIX_CAUTION, VIX_WARNING, VIX_PANIC,
    TGA_HIGH, TGA_LOW, TGA_DROP_4W,
    RRP_HIGH, RRP_LOW,
    US10Y_FED_SPREAD_HEALTHY, US10Y_DAILY_DROP_BP,
    SCORE_STRONG_BUY, SCORE_BUY, SCORE_NEUTRAL, SCORE_CAUTION,
)


def _get_val(ind, key, field="value", default=0):
    return ind.get(key, {}).get(field, default)


def _calc_4w_change(history, key):
    """history에서 최근 4주(28일) 변화율 계산. 데이터 없으면 None."""
    entries = history.get(key, [])
    if len(entries) < 2:
        return None
    # 최신 값
    latest = entries[-1]["value"]
    # 28일 전 근처 값 찾기
    target_idx = max(0, len(entries) - 28)
    old = entries[target_idx]["value"]
    if old == 0:
        return None
    return (latest - old) / old


def judge_phase(ind: dict, history: dict = None) -> dict:
    """종합 국면 판정. ind=indicators dict, history=history dict."""
    if history is None:
        history = {}

    score = 0
    reasons = []

    # ── 1. VIX 4단계 ──────────────────────────────────────
    vix = _get_val(ind, "vix")
    if vix >= VIX_PANIC:
        score += 3
        reasons.append(f"VIX {vix:.1f} 패닉 (역발상 매수 기회)")
    elif vix >= VIX_WARNING:
        score += 2
        reasons.append(f"VIX {vix:.1f} 위험 (공포 매수 구간)")
    elif vix >= VIX_CAUTION:
        score += 0
        reasons.append(f"VIX {vix:.1f} 불안")
    elif vix > 0:
        score -= 1
        reasons.append(f"VIX {vix:.1f} 안정 (추가 하락 여력 제한)")

    # ── 2. TGA 4주 추세 ──────────────────────────────────
    tga = _get_val(ind, "tga")
    tga_4w = _calc_4w_change(history, "tga")
    if tga_4w is not None and tga_4w <= TGA_DROP_4W:
        score += 2
        reasons.append(f"TGA 4주 {tga_4w*100:.1f}% 급감 → 유동성 방출")
    elif tga > TGA_HIGH:
        score -= 1
        reasons.append(f"TGA {tga:.0f}B$ 높음 (유동성 흡수)")
    elif tga < TGA_LOW:
        score += 1
        reasons.append(f"TGA {tga:.0f}B$ 낮음 (재충전 → 향후 흡수 가능)")

    # ── 3. RRP 추세 ──────────────────────────────────────
    rrp = _get_val(ind, "rrp")
    rrp_4w = _calc_4w_change(history, "rrp")
    if rrp <= RRP_LOW:
        score += 1
        reasons.append(f"RRP {rrp:.0f}B$ 소진 (유동성 시장 유입)")
    elif rrp > RRP_HIGH:
        score -= 1
        reasons.append(f"RRP {rrp:.0f}B$ 대기 (유동성 미방출)")
    elif rrp_4w is not None and rrp_4w < -0.10:
        score += 1
        reasons.append(f"RRP 4주 {rrp_4w*100:.1f}% 감소 → 유동성 유입 중")

    # ── 4. TGA + RRP 복합 ────────────────────────────────
    if tga_4w is not None and tga_4w <= TGA_DROP_4W and rrp <= RRP_LOW:
        score += 1
        reasons.append("TGA 방출 + RRP 소진 → 쌍둥이 유동성 신호")

    # ── 5. US10Y vs Fed Rate 스프레드 ────────────────────
    us10y = _get_val(ind, "us10y")
    fed_rate = _get_val(ind, "fed_rate")
    if us10y > 0 and fed_rate > 0:
        spread = us10y - fed_rate
        if spread >= US10Y_FED_SPREAD_HEALTHY:
            score += 1
            reasons.append(f"10Y-기준금리 스프레드 {spread:.2f}% 정상 (경기 확장)")
        elif spread < 0:
            score -= 1
            reasons.append(f"10Y-기준금리 스프레드 {spread:.2f}% 역전 (경기 둔화)")

    # 10Y 일간 급락
    us10y_change = _get_val(ind, "us10y", "change", 0)
    if us10y_change * 100 <= US10Y_DAILY_DROP_BP:
        score += 1
        reasons.append(f"10Y 금리 일간 {us10y_change*100:.0f}bp 급락 (안전자산 쏠림)")

    # ── 6. 2-10 스프레드 ─────────────────────────────────
    spread_2_10 = _get_val(ind, "spread_2_10")
    if spread_2_10 < 0:
        score -= 1
        reasons.append(f"2-10 스프레드 {spread_2_10:.2f}% 역전 (경기침체 경고)")

    # ── 7. 금 + 국채 안전자산 선호 ────────────────────────
    gold_chg = _get_val(ind, "gold", "change_pct", 0)
    us10y_chg = _get_val(ind, "us10y", "change", 0)
    if gold_chg > 0 and us10y_chg < 0:  # 금리↓ = 국채가격↑
        score += 1
        reasons.append("금·국채 동반 상승 (안전자산 선호 → 바닥 신호)")

    # ── 8. M2 추세 ───────────────────────────────────────
    m2_chg = _get_val(ind, "m2", "change_pct", 0)
    if m2_chg > 0:
        score += 1
        reasons.append("M2 증가 추세 (유동성 확대)")
    elif m2_chg < -1:
        score -= 1
        reasons.append("M2 감소 (유동성 긴축)")

    # ── 9. S&P 500 동향 ──────────────────────────────────
    sp_chg = _get_val(ind, "sp500", "change_pct", 0)
    if sp_chg < -2:
        score += 1
        reasons.append(f"S&P 500 {sp_chg:.1f}% 급락 (공포 매수 구간)")
    elif sp_chg < -1:
        reasons.append(f"S&P 500 {sp_chg:.1f}% 하락")

    # ── 10. 연준 대차대조표 (QT/QE) ──────────────────────
    fed_bal_chg = _get_val(ind, "fed_balance", "change_pct", 0)
    if fed_bal_chg > 0.5:
        score += 1
        reasons.append("연준 자산 증가 (QE 전환 신호)")

    # ── 종합 판정 ────────────────────────────────────────
    if score >= SCORE_STRONG_BUY:
        status = "strong_buy"
    elif score >= SCORE_BUY:
        status = "buy"
    elif score >= SCORE_NEUTRAL:
        status = "neutral"
    elif score >= SCORE_CAUTION:
        status = "caution"
    else:
        status = "wait"

    return {"status": status, "score": score, "reasons": reasons}
