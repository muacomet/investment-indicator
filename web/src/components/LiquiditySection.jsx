import React from 'react';
import IndicatorCard from './IndicatorCard';

const LIQUIDITY_KEYS = [
  { key: 'tga', name: 'TGA (재무부 일반계정)' },
  { key: 'rrp', name: 'RRP (역레포)' },
  { key: 'm2', name: 'M2 통화량' },
  { key: 'fed_balance', name: '연준 대차대조표' },
];

export default function LiquiditySection({ indicators, history }) {
  const hasAny = LIQUIDITY_KEYS.some((lk) => indicators?.[lk.key]);
  if (!hasAny) return null;

  return (
    <div style={{ padding: '0 16px' }}>
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: 'var(--dim)',
          textTransform: 'uppercase',
          letterSpacing: 1,
          marginBottom: 10,
          marginTop: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        💧 유동성 지표
        <span
          style={{
            fontSize: 11,
            fontWeight: 400,
            color: 'var(--dim)',
            opacity: 0.6,
          }}
        >
          주간 갱신
        </span>
      </div>
      {LIQUIDITY_KEYS.map(
        (lk) =>
          indicators[lk.key] && (
            <IndicatorCard
              key={lk.key}
              name={lk.name}
              indicator={indicators[lk.key]}
              history={history?.[lk.key]}
            />
          )
      )}
    </div>
  );
}
