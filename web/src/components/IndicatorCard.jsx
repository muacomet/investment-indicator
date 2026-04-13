import React, { useState } from 'react';
import HistoryChart from './HistoryChart';

const SIGNAL_COLORS = {
  green: { color: 'var(--green)', bg: 'var(--green-bg)' },
  yellow: { color: 'var(--yellow)', bg: 'var(--yellow-bg)' },
  orange: { color: '#fb923c', bg: 'rgba(251, 146, 60, 0.08)' },
  red: { color: 'var(--red)', bg: 'var(--red-bg)' },
};

const CHART_COLORS = {
  green: '#4ade80',
  yellow: '#facc15',
  orange: '#fb923c',
  red: '#f87171',
};

export default function IndicatorCard({ name, desc, indicator, history }) {
  const [expanded, setExpanded] = useState(false);

  if (!indicator) return null;

  const signal = SIGNAL_COLORS[indicator.signal] || SIGNAL_COLORS.yellow;
  const chartColor = CHART_COLORS[indicator.signal] || '#60a5fa';

  const changePct = indicator.change_pct;
  const changeSign = changePct > 0 ? '+' : '';
  const changeColor =
    changePct > 0 ? 'var(--green)' : changePct < 0 ? 'var(--red)' : 'var(--dim)';

  const handleToggle = () => setExpanded(!expanded);

  return (
    <div
      style={{
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: 14,
        padding: 16,
        marginBottom: 10,
      }}
    >
      {/* 헤더 영역 — 터치하면 열림/닫힘 */}
      <div
        onClick={handleToggle}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: signal.color,
              boxShadow: `0 0 6px ${signal.color}`,
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: 14, fontWeight: 600 }}>{name}</span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              fontFamily: "'SF Mono', monospace",
            }}
          >
            {typeof indicator.value === 'number'
              ? indicator.value.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })
              : indicator.value}
          </div>
          <div
            style={{
              fontSize: 12,
              color: changeColor,
              fontFamily: "'SF Mono', monospace",
            }}
          >
            {changeSign}
            {changePct?.toFixed(2)}%
          </div>
        </div>
      </div>

      {(indicator.note || desc) && (
        <div
          onClick={handleToggle}
          style={{
            fontSize: 11,
            color: 'var(--dim)',
            marginTop: 8,
            cursor: 'pointer',
          }}
        >
          {indicator.note}
          {indicator.note && desc && ' · '}
          {desc && <span style={{ color: 'var(--blue)', opacity: 0.7 }}>{desc}</span>}
        </div>
      )}

      {expanded && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            borderTop: '1px solid var(--border)',
            marginTop: 12,
            paddingTop: 4,
          }}
        >
          <HistoryChart data={history} color={chartColor} />
          {(!history || history.length === 0) && (
            <div
              style={{
                fontSize: 12,
                color: 'var(--dim)',
                textAlign: 'center',
                padding: '20px 0',
              }}
            >
              히스토리 데이터 없음
            </div>
          )}
        </div>
      )}

      {/* 접기/펼치기 버튼 */}
      <div
        onClick={handleToggle}
        style={{
          textAlign: 'center',
          marginTop: 8,
          fontSize: 10,
          color: 'var(--dim)',
          opacity: 0.5,
          cursor: 'pointer',
        }}
      >
        {expanded ? '▲ 접기' : '▼ 차트 보기'}
      </div>
    </div>
  );
}
