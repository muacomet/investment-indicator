import React from 'react';

export default function SectionHeader({ icon, title, subtitle }) {
  return (
    <div
      style={{
        fontSize: 13,
        fontWeight: 700,
        color: 'var(--dim)',
        letterSpacing: 0.5,
        marginBottom: 10,
        marginTop: 24,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <span>{icon}</span>
      <span>{title}</span>
      {subtitle && (
        <span
          style={{
            fontSize: 11,
            fontWeight: 400,
            color: 'var(--dim)',
            opacity: 0.6,
          }}
        >
          {subtitle}
        </span>
      )}
    </div>
  );
}
