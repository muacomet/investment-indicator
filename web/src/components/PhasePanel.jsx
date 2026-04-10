import React from 'react';

const PHASE_CONFIG = {
  buy: {
    emoji: '🟢',
    label: '매수 국면',
    color: 'var(--green)',
    bg: 'var(--green-bg)',
    border: 'rgba(74, 222, 128, 0.25)',
  },
  mixed: {
    emoji: '⚠️',
    label: '혼조 국면',
    color: 'var(--yellow)',
    bg: 'var(--yellow-bg)',
    border: 'rgba(250, 204, 21, 0.25)',
  },
  wait: {
    emoji: '🔴',
    label: '관망 국면',
    color: 'var(--red)',
    bg: 'var(--red-bg)',
    border: 'rgba(248, 113, 113, 0.25)',
  },
};

export default function PhasePanel({ phase }) {
  if (!phase) return null;

  const config = PHASE_CONFIG[phase.status] || PHASE_CONFIG.wait;

  return (
    <div
      style={{
        background: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: 14,
        padding: 18,
        margin: '0 16px 16px',
      }}
    >
      <div
        style={{
          fontSize: 20,
          fontWeight: 700,
          color: config.color,
          marginBottom: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span>{config.emoji}</span>
        <span>{config.label}</span>
        <span
          style={{
            fontSize: 13,
            fontWeight: 500,
            opacity: 0.8,
            marginLeft: 'auto',
          }}
        >
          {phase.score}/4
        </span>
      </div>
      {phase.reasons && phase.reasons.length > 0 && (
        <ul
          style={{
            listStyle: 'none',
            padding: 0,
            margin: 0,
          }}
        >
          {phase.reasons.map((reason, i) => (
            <li
              key={i}
              style={{
                fontSize: 13,
                color: 'var(--dim)',
                padding: '4px 0',
                paddingLeft: 16,
                position: 'relative',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  left: 0,
                  color: config.color,
                }}
              >
                •
              </span>
              {reason}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
