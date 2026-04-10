"""국면 판정 로직. 수치는 운영하며 튜닝 예정."""

# 튜닝 가능한 임계값
VIX_FEAR = 30
M2_TREND_WINDOW = 3  # 최근 3개월


def judge_phase(ind: dict) -> dict:
    score = 0
    reasons = []

    vix = ind.get("vix", {}).get("value", 0)
    if vix > VIX_FEAR:
        score += 1
        reasons.append(f"VIX {vix:.1f} (극도 공포)")

    # S&P 200일선 하회 판정은 history.json 필요 → 임시로 변동률로 대체
    sp_chg = ind.get("sp500", {}).get("change_pct", 0)
    if sp_chg < -1:
        score += 1
        reasons.append("S&P 500 급락")

    gold_chg = ind.get("gold", {}).get("change_pct", 0)
    us10_chg = ind.get("us10y", {}).get("change", 0)
    if gold_chg > 0 and us10_chg < 0:  # 금리↓ = 국채가격↑
        score += 1
        reasons.append("금·국채 동반 상승 (안전자산 선호)")

    # M2 trend: history 필요, 임시 생략
    # TODO: history 연동 후 활성화

    if score >= 3:
        status = "buy"
    elif score == 2:
        status = "mixed"
    else:
        status = "wait"

    return {"status": status, "score": score, "reasons": reasons}
