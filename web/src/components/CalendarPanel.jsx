import React from 'react';

const EVENT_STYLES = {
  FOMC: { emoji: '🏛️', color: '#f87171', bg: 'rgba(248, 113, 113, 0.1)' },
  CPI: { emoji: '📊', color: '#facc15', bg: 'rgba(250, 204, 21, 0.1)' },
  '고용': { emoji: '👷', color: '#60a5fa', bg: 'rgba(96, 165, 250, 0.1)' },
};

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
  const wd = weekdays[d.getDay()];
  return `${month}/${day} (${wd})`;
}

function daysLabel(days) {
  if (days === 0) return '오늘';
  if (days === 1) return '내일';
  return `${days}일 후`;
}

export default function CalendarPanel({ events }) {
  const items = events || [];

  if (items.length === 0) {
    return (
      <div style={{ padding: '0 16px' }}>
        <div style={{
          background: 'var(--card)', border: '1px solid var(--border)',
          borderRadius: 12, padding: 20, textAlign: 'center',
          fontSize: 13, color: 'var(--dim)',
        }}>
          향후 30일 이내 예정된 주요 경제 이벤트가 없습니다.
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '0 16px' }}>
      <div style={{
        background: 'var(--card)', border: '1px solid var(--border)',
        borderRadius: 12, overflow: 'hidden',
      }}>
        {items.map((ev, i) => {
          const style = EVENT_STYLES[ev.event] || EVENT_STYLES.CPI;
          const isUrgent = ev.days_until <= 2;

          return (
            <div
              key={i}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 14px',
                borderBottom: i < items.length - 1 ? '1px solid var(--border)' : 'none',
                background: isUrgent ? style.bg : 'transparent',
              }}
            >
              {/* 이벤트 아이콘 + 뱃지 */}
              <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: style.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, flexShrink: 0,
              }}>
                {style.emoji}
              </div>

              {/* 이벤트 정보 */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: style.color }}>{ev.event}</span>
                  <span style={{ fontSize: 12, color: 'var(--dim)' }}>{ev.desc}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--dim)', marginTop: 2 }}>
                  {formatDate(ev.date)}
                </div>
              </div>

              {/* D-day */}
              <div style={{
                fontSize: 13, fontWeight: 700,
                color: isUrgent ? style.color : 'var(--dim)',
                flexShrink: 0,
                padding: isUrgent ? '2px 8px' : 0,
                borderRadius: 6,
                background: isUrgent ? style.bg : 'transparent',
              }}>
                {daysLabel(ev.days_until)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
