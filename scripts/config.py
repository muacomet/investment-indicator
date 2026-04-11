"""판정 임계값 상수. 운영하며 숫자만 바꾸면 로직 전체에 반영."""

# ── VIX 4단계 ────────────────────────────────────────────
VIX_STABLE  = 20   # 🟢 안정
VIX_CAUTION = 25   # 🟡 불안
VIX_WARNING = 30   # 🟠 위험
VIX_PANIC   = 60   # 🆘 패닉

# ── TGA (billion USD) ────────────────────────────────────
TGA_HIGH = 1000           # 자금 흡수 중
TGA_LOW  = 500            # 재충전 필요
TGA_DROP_4W = -0.20       # 4주 -20% → releasing (매수 신호)

# ── RRP (billion USD) ────────────────────────────────────
RRP_HIGH = 2000           # 자금 대기
RRP_LOW  = 500            # 대기 자금 소진

# ── 금리 스프레드 ────────────────────────────────────────
US10Y_FED_SPREAD_HEALTHY = 0.5   # 10년-기준금리 > 0.5 → 경기 확장
US10Y_DAILY_DROP_BP = -10        # 일간 -10bp 급락

# ── 종합 판정 임계값 ────────────────────────────────────
SCORE_STRONG_BUY = 4
SCORE_BUY        = 2
SCORE_NEUTRAL    = 0
SCORE_CAUTION    = -2
