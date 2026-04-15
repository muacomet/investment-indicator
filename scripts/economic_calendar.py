"""2026 경제 캘린더 — CPI, FOMC, 고용보고서 일정."""
from datetime import datetime, date

# 2026 FOMC 회의 종료일 (결과 발표일)
FOMC_2026 = [
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 5, 6),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 11, 4),
    date(2026, 12, 16),
]

# 2026 CPI 발표일 (BLS, 보통 매월 10~15일)
CPI_2026 = [
    date(2026, 1, 14),
    date(2026, 2, 12),
    date(2026, 3, 11),
    date(2026, 4, 14),
    date(2026, 5, 13),
    date(2026, 6, 10),
    date(2026, 7, 14),
    date(2026, 8, 12),
    date(2026, 9, 11),
    date(2026, 10, 13),
    date(2026, 11, 12),
    date(2026, 12, 10),
]

# 2026 고용보고서 (BLS, 매월 첫째 금요일)
JOBS_2026 = [
    date(2026, 1, 9),
    date(2026, 2, 6),
    date(2026, 3, 6),
    date(2026, 4, 3),
    date(2026, 5, 1),
    date(2026, 6, 5),
    date(2026, 7, 2),
    date(2026, 8, 7),
    date(2026, 9, 4),
    date(2026, 10, 2),
    date(2026, 11, 6),
    date(2026, 12, 4),
]


def get_upcoming_events(days_ahead: int = 14) -> list[dict]:
    """향후 N일 이내 경제 이벤트 목록 반환."""
    today = date.today()
    events = []

    for d in FOMC_2026:
        diff = (d - today).days
        if 0 <= diff <= days_ahead:
            events.append({"date": d.isoformat(), "event": "FOMC", "desc": "FOMC 금리 결정", "days_until": diff})
        elif -1 <= diff < 0:
            events.append({"date": d.isoformat(), "event": "FOMC", "desc": "FOMC 결과 발표됨", "days_until": diff})

    for d in CPI_2026:
        diff = (d - today).days
        if 0 <= diff <= days_ahead:
            month = d.month - 1 or 12
            events.append({"date": d.isoformat(), "event": "CPI", "desc": f"{month}월 소비자물가지수", "days_until": diff})

    for d in JOBS_2026:
        diff = (d - today).days
        if 0 <= diff <= days_ahead:
            events.append({"date": d.isoformat(), "event": "고용", "desc": "비농업 고용·실업률", "days_until": diff})

    # Sort by date
    events.sort(key=lambda e: e["date"])
    return events
