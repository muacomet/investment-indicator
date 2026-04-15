import React from 'react';

const NAMES = { sp500: 'S&P 500', qqq: 'QQQ', schd: 'SCHD' };

function formatVol(n) {
  if (!n) return '-';
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`;
  return n.toLocaleString();
}

function MomentumRow({ name, indicator, momentum, volume }) {
  if (!indicator) return null;

  const chgPct = indicator.change_pct || 0;
  const chgColor = chgPct > 0 ? 'var(--green)' : chgPct < 0 ? 'var(--red)' : 'var(--dim)';
  const chgSign = chgPct > 0 ? '+' : '';

  const consec = momentum?.consecutive_up;
  const athPct = momentum?.ath_distance_pct;

  const volRatio = volume?.volume_ratio;
  const upVol = volume?.up_day_avg_vol;
  const downVol = volume?.down_day_avg_vol;

  return (
    <div style={{
      background: 'var(--card)', border: '1px solid var(--border)',
      borderRadius: 12, padding: 14, marginBottom: 8,
    }}>
      {/* 상단: 이름 + 가격 + 등락 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span style={{ fontSize: 14, fontWeight: 700 }}>{name}</span>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: 16, fontWeight: 800, fontFamily: "'SF Mono', monospace" }}>
            {indicator.value?.toLocaleString(undefined, { maximumFractionDigits: 1 })}
          </span>
          <span style={{ fontSize: 13, color: chgColor, fontFamily: "'SF Mono', monospace", marginLeft: 8 }}>
            {chgSign}{chgPct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* 지표 그리드 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
        {/* 연속 상승일 */}
        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: 'var(--dim)', marginBottom: 4 }}>연속 상승</div>
          <div style={{
            fontSize: 18, fontWeight: 800,
            color: consec > 0 ? 'var(--green)' : 'var(--dim)',
            fontFamily: "'SF Mono', monospace",
          }}>
            {consec != null ? `${consec}일` : '-'}
          </div>
        </div>

        {/* 전고점 대비 */}
        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: 'var(--dim)', marginBottom: 4 }}>전고점 대비</div>
          <div style={{
            fontSize: 18, fontWeight: 800,
            color: athPct === 0 ? 'var(--green)' : athPct > -5 ? 'var(--yellow)' : 'var(--red)',
            fontFamily: "'SF Mono', monospace",
          }}>
            {athPct != null ? `${athPct.toFixed(1)}%` : '-'}
          </div>
        </div>

        {/* 거래량 비율 */}
        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: 'var(--dim)', marginBottom: 4 }}>거래량 비율</div>
          <div style={{
            fontSize: 18, fontWeight: 800,
            color: volRatio > 1.2 ? 'var(--green)' : volRatio < 0.8 ? 'var(--red)' : 'var(--dim)',
            fontFamily: "'SF Mono', monospace",
          }}>
            {volRatio != null ? `${volRatio}x` : '-'}
          </div>
        </div>
      </div>

      {/* 거래량 상세 */}
      {volume && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 11, color: 'var(--dim)' }}>
          <span>당일 {formatVol(volume.volume)}</span>
          <span>20일평균 {formatVol(volume.volume_avg_20d)}</span>
          <span style={{ color: upVol > downVol ? 'var(--green)' : 'var(--red)' }}>
            상승일 {formatVol(upVol)} / 하락일 {formatVol(downVol)}
          </span>
        </div>
      )}
    </div>
  );
}

export default function MomentumPanel({ indicators, momentum, volume }) {
  if (!indicators) return null;

  const keys = ['sp500', 'qqq', 'schd'];
  const hasData = keys.some(k => indicators[k]);
  if (!hasData) return null;

  return (
    <div style={{ padding: '0 16px' }}>
      {keys.map(key => (
        <MomentumRow
          key={key}
          name={NAMES[key]}
          indicator={indicators[key]}
          momentum={momentum?.[key]}
          volume={volume?.[key]}
        />
      ))}

      {/* NQ 선물 */}
      {indicators.nq_futures && (
        <div style={{
          background: 'var(--card)', border: '1px solid var(--border)',
          borderRadius: 12, padding: 14,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div>
            <span style={{ fontSize: 14, fontWeight: 700 }}>NQ 선물</span>
            <span style={{ fontSize: 11, color: 'var(--dim)', marginLeft: 6 }}>나스닥100 선물</span>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: 16, fontWeight: 800, fontFamily: "'SF Mono', monospace" }}>
              {indicators.nq_futures.value?.toLocaleString()}
            </span>
            {(() => {
              const c = indicators.nq_futures.change_pct || 0;
              const color = c > 0 ? 'var(--green)' : c < 0 ? 'var(--red)' : 'var(--dim)';
              const arrow = c > 0 ? '▲' : c < 0 ? '▼' : '—';
              return (
                <span style={{ fontSize: 13, color, marginLeft: 8, fontWeight: 700 }}>
                  {arrow} {c > 0 ? '+' : ''}{c.toFixed(2)}%
                </span>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
