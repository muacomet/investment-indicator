# 투자 지표 확인 (Investment Indicator)

개인용 매크로 시장 대시보드. FRED + Yahoo Finance 데이터를 GitHub Actions로 주기 수집 → JSON 저장 → React 앱이 GitHub Pages에서 서빙.

## 핵심 목표
"공포에 사라" 타이밍 자동 해석. 주요 지수·금리·원자재·유동성 지표를 종합해 적극매수/매수/중립/주의/관망 국면을 판정.

## 아키텍처
```
FRED API + Yahoo Finance
  ↓ (GitHub Actions cron)
scripts/fetch_data.py → data/latest.json + history.json
  ↓ (git commit)
web/ (React) → GitHub Pages → 모바일 브라우저
```

**서버 없음.** GitHub Actions가 스케줄러 역할. 운영비 0원.

## 갱신 주기
- 미장 중 (22:30~05:00 KST): 5분
- 장 전후: 15분
- 주말/공휴일: 1일 1회
- FRED 유동성 지표 (TGA/RRP/M2): 1일 1회

## 데이터 소스

### FRED API (무료, 키 필요)
| 지표 | Series ID | 비고 |
|---|---|---|
| VIX | VIXCLS | |
| 미 10년물 | DGS10 | |
| 미 2년물 | DGS2 | |
| 2-10 스프레드 | T10Y2Y | |
| 미국 기준금리 | DFEDTARU | FOMC 상단 |
| TGA | WTREGEN | millions → billions 변환 |
| RRP | RRPONTSYD | |
| M2 | M2SL | |
| 연준 대차대조표 | WALCL | millions → billions 변환 |
| 신용카드 연체율 | DRCCLACBS | 분기 |
| 자동차 할부 연체율 | DRALACBN | 분기 |
| 주담대 연체율 | DRSFRMACBS | 분기 |
| 개인 저축률 | PSAVERT | 월간 |

### 한국은행 ECOS API
| 지표 | 조회 방식 |
|---|---|
| KOSPI | StatisticSearch 802Y001 |
| 국고채 2년 | StatisticSearch 817Y002 |
| 국고채 10년 | StatisticSearch 817Y002 |
| 원/달러 환율 | StatisticSearch 731Y001 |
| 한국 기준금리 | KeyStatisticList "한국은행 기준금리" |
| 가계대출 연체율 | KeyStatisticList "연체율" |

### Yahoo Finance (yfinance)
| 지표 | Ticker |
|---|---|
| S&P 500 | ^GSPC |
| NASDAQ | ^IXIC |
| DXY | DX-Y.NYB |
| 금 | GC=F |
| WTI | CL=F |
| 구리 | HG=F |

## 데이터 스키마 (data/latest.json)
```json
{
  "updated_at": "2026-04-10T14:30:00Z",
  "phase": {
    "status": "strong_buy" | "buy" | "neutral" | "caution" | "wait",
    "score": 3,
    "reasons": ["VIX 30+ 극도 공포", "S&P 200일선 하회"]
  },
  "indicators": {
    "vix": {
      "value": 21.0,
      "change": -4.7,
      "change_pct": -18.4,
      "signal": "yellow",
      "note": "20 이하 안정 / 30+ 위험"
    }
  }
}
```

history.json은 지표별 {date, value} 배열. 최근 90일 유지.

## 국면 판정 로직 (scripts/calculate.py)
Multi-factor scoring. score 범위 -3 ~ 6+.

### 판정 팩터 (10개)
1. **VIX 4단계**: 패닉(60+) +3 / 위험(30+) +2 / 불안(25+) 0 / 안정(<20) -1
2. **TGA 4주 추세**: 4주 -20% 급감 +2 / 1조$+ -1 / 5천억$- +1
3. **RRP 추세**: 소진(500B-) +1 / 대기(2조+) -1 / 4주 -10% +1
4. **TGA+RRP 복합**: TGA 방출 + RRP 소진 동시 → +1 (쌍둥이 유동성)
5. **US10Y vs 기준금리 스프레드**: 정상(+0.5%) +1 / 역전 -1
6. **US10Y 일간 급락**: -10bp 이상 +1
7. **2-10 스프레드 역전**: 역전 시 -1
8. **금·국채 안전자산**: 금↑ + 금리↓ 동시 +1
9. **M2 추세**: 증가 +1 / 감소(-1%+) -1
10. **S&P 500 급락**: -2%+ 급락 +1

### 종합 판정 (config.py 상수)
- score >= 4 → 🟢🟢 strong_buy (적극 매수)
- score >= 2 → 🟢 buy (매수)
- score >= 0 → ⚪ neutral (중립)
- score >= -2 → 🟡 caution (주의)
- score < -2 → 🔴 wait (관망)

**임계값은 `scripts/config.py`에서 상수로 관리.**

## 화면 구성 (web/)
1. 상단 고정: 종합 국면 판정 패널
2. 지표 카드 리스트 (스크린샷 레이아웃 기준 — 동현님 원본 소스 없음, 새로 구성)
3. 카드 탭 시 7일/30일 히스토리 차트 확장 (필수)
4. 유동성 섹션 분리 (주간 갱신)

### UI 규칙
- 모바일 우선 반응형
- 다크 테마
- 신호등: 🟢 green / 🟡 yellow / 🔴 red
- Recharts 사용 (React)

## GitHub Secrets
- `FRED_API_KEY`: FRED API 키
- `BOK_API_KEY`: 한국은행 ECOS API 키

## 주의사항
- FRED 키 절대 커밋 금지
- history.json은 90일 넘으면 오래된 것 삭제
- yfinance는 비공식 라이브러리 — 실패 시 재시도 로직 필수
- GitHub Actions 무료 티어 월 2000분 한도 감안 (5분 간격 = 월 8640회 호출, 각 1분 이내 완료 필요)
- 한국 시간(KST) 기준으로 cron 설정 시 UTC 변환 주의

## 구현 우선순위
1. scripts/fetch_data.py — FRED + yfinance 호출, latest.json 생성
2. scripts/calculate.py — 국면 판정
3. .github/workflows/fetch-data.yml — 스케줄러
4. web/ — React 앱 (Vite + Recharts)
5. GitHub Pages 배포 설정
