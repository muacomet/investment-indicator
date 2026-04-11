import React from 'react';

const SIGNAL_COLORS = {
  green: '#4ade80',
  yellow: '#facc15',
  orange: '#fb923c',
  red: '#f87171',
};

const ICONS = {
  vix: '⚡', sp500: '🇺🇸', nasdaq: '🖥️', dxy: '💲',
  fed_rate: '🏛️', us10y: '📉', us2y: '📈', spread_2_10: '⊕',
  gold: '🥇', wti: '🛢️', copper: '🔶', tga: '🏦', rrp: '🔄',
  m2: '💰', fed_balance: '📊',
  kospi: '🇰🇷', usdkrw: '💱', kr_rate: '🏛️', kr10y: '📉', kr2y: '📈',
  us_cc_delinq: '💳', us_auto_delinq: '🚗', us_mortgage_delinq: '🏠',
  us_saving_rate: '🐖', kr_delinquency: '🇰🇷',
};

const SUBTITLES = {
  vix: '공포지수', sp500: '미국 대형주', nasdaq: '기술주', dxy: '달러인덱스',
  fed_rate: 'FOMC 상단', us10y: '국채 금리', us2y: '국채 금리',
  spread_2_10: '장단기 금리차', gold: 'Gold Spot', wti: 'Crude Oil',
  copper: '경기선행', tga: '재무부 계정', rrp: '역레포', m2: '통화량',
  fed_balance: 'QT/QE', kospi: '한국 종합', usdkrw: '환율',
  kr_rate: '기준금리', kr10y: '국고채', kr2y: '국고채',
  us_cc_delinq: '신용카드', us_auto_delinq: '자동차할부',
  us_mortgage_delinq: '주담대', us_saving_rate: '저축률',
  kr_delinquency: '가계대출',
};

const DESCRIPTIONS = {
  vix: '20 이하 안정 / 30+ 위험',
  sp500: '200일선 위 = 강세장',
  nasdaq: 'S&P500 대비 상대강도 확인',
  dxy: '100 이상 = 달러 강세',
  fed_rate: '금리 인하 시 유동성 확대',
  us10y: '4% 이상 = 주식 밸류 압박',
  us2y: '기준금리 방향 선행',
  spread_2_10: '0bp 이하 역전 = 침체 신호',
  gold: '상승 = 안전자산 선호',
  wti: '고유가 = 인플레·연준 매파',
  copper: '상승 = 경기 확장 신호',
  tga: '감소 = 유동성 방출',
  rrp: '감소 = 유동성 시장 유입',
  m2: '증가 = 유동성 확대',
  fed_balance: '증가 = QE / 감소 = QT',
  kospi: '',
  usdkrw: '상승 = 원화 약세',
  kr_rate: '',
  kr10y: '',
  kr2y: '',
  us_cc_delinq: '3%+ 경고',
  us_auto_delinq: '3%+ 경고',
  us_mortgage_delinq: '4%+ 위험',
  us_saving_rate: '5% 이상 건전',
  kr_delinquency: '1%+ 경고',
};

function formatValue(key, value) {
  if (value == null) return '-';
  // 금리/퍼센트 지표
  if (['us10y', 'us2y', 'fed_rate', 'kr10y', 'kr2y', 'kr_rate',
       'us_cc_delinq', 'us_auto_delinq', 'us_mortgage_delinq',
       'us_saving_rate', 'kr_delinquency'].includes(key)) {
    return `${value.toFixed(2)}%`;
  }
  // 스프레드 → bp
  if (key === 'spread_2_10') {
    return `${value > 0 ? '+' : ''}${(value * 100).toFixed(0)}bp`;
  }
  // 달러 표시
  if (['gold', 'wti', 'copper'].includes(key)) {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function formatChange(key, indicator) {
  const change = indicator.change;
  const changePct = indicator.change_pct;
  if (change == null && changePct == null) return null;

  // 스프레드 → bp 변화
  if (key === 'spread_2_10') {
    const bp = change != null ? (change * 100).toFixed(0) : '0';
    return `${change >= 0 ? '+' : ''}${bp}bp`;
  }
  // 금리 → bp 변화
  if (['us10y', 'us2y', 'fed_rate', 'kr10y', 'kr2y', 'kr_rate'].includes(key)) {
    const bp = change != null ? Math.round(change * 100) : 0;
    return `${bp >= 0 ? '+' : ''}${bp}bp`;
  }
  // 일반: 절대 변화 + 퍼센트
  if (change != null && changePct != null) {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toLocaleString(undefined, { maximumFractionDigits: 1 })} (${sign}${changePct.toFixed(1)}%)`;
  }
  return null;
}

function SummaryRow({ itemKey, name, indicator }) {
  if (!indicator) return null;

  const signal = indicator.signal || 'yellow';
  const signalColor = SIGNAL_COLORS[signal] || SIGNAL_COLORS.yellow;
  const barColor = signalColor;
  const icon = ICONS[itemKey] || '📌';
  const subtitle = SUBTITLES[itemKey] || '';
  const desc = indicator.note || DESCRIPTIONS[itemKey] || '';

  const changeStr = formatChange(itemKey, indicator);
  const changeNum = indicator.change || 0;
  const changeColor = changeNum > 0 ? 'var(--green)' : changeNum < 0 ? 'var(--red)' : 'var(--dim)';

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '4px 1fr auto auto 1fr',
        gap: 0,
        alignItems: 'center',
        padding: '14px 12px',
        borderBottom: '1px solid var(--border)',
      }}
    >
      {/* 1. 색상 바 */}
      <div
        style={{
          width: 4,
          alignSelf: 'stretch',
          borderRadius: 2,
          background: barColor,
          marginRight: 10,
        }}
      />

      {/* 2. 이름 영역 */}
      <div style={{ minWidth: 0, paddingRight: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: 13 }}>{icon}</span>
          <span style={{ fontSize: 14, fontWeight: 700, color: barColor }}>{name}</span>
        </div>
        {subtitle && (
          <div style={{ fontSize: 11, color: 'var(--dim)', marginTop: 1 }}>{subtitle}</div>
        )}
      </div>

      {/* 3. 수치 */}
      <div style={{ textAlign: 'right', paddingRight: 14 }}>
        <div
          style={{
            fontSize: 18,
            fontWeight: 800,
            fontFamily: "'SF Mono', 'Fira Code', monospace",
            letterSpacing: '-0.5px',
          }}
        >
          {formatValue(itemKey, indicator.value)}
        </div>
        {changeStr && (
          <div
            style={{
              fontSize: 12,
              color: changeColor,
              fontFamily: "'SF Mono', monospace",
              marginTop: 1,
            }}
          >
            {changeStr}
          </div>
        )}
      </div>

      {/* 4. 신호등 */}
      <div style={{ display: 'flex', justifyContent: 'center', paddingRight: 12 }}>
        <div
          style={{
            width: 22,
            height: 22,
            borderRadius: '50%',
            background: signalColor,
            boxShadow: `0 0 8px ${signalColor}40`,
          }}
        />
      </div>

      {/* 5. 기준선 설명 */}
      <div
        style={{
          fontSize: 12,
          color: 'var(--dim)',
          lineHeight: 1.4,
        }}
      >
        {desc}
      </div>
    </div>
  );
}

export default function SummaryTable({ sections, indicators }) {
  if (!indicators) return null;

  return (
    <div style={{ padding: '0 8px' }}>
      {/* 헤더 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '4px 1fr auto auto 1fr',
          gap: 0,
          padding: '8px 12px',
          fontSize: 11,
          color: 'var(--dim)',
          borderBottom: '1px solid var(--border)',
        }}
      >
        <div />
        <div>이름</div>
        <div style={{ textAlign: 'right', paddingRight: 14 }}>수치</div>
        <div style={{ textAlign: 'center', paddingRight: 12 }} />
        <div>기준선</div>
      </div>

      {sections.map((section, si) => (
        <div key={si}>
          {/* 섹션 구분 */}
          <div
            style={{
              padding: '10px 12px 6px',
              fontSize: 13,
              fontWeight: 700,
              color: 'var(--dim)',
              background: 'rgba(255,255,255,0.02)',
              borderBottom: '1px solid var(--border)',
            }}
          >
            {section.icon} {section.title}
          </div>
          {section.keys.map((item) => (
            <SummaryRow
              key={item.key}
              itemKey={item.key}
              name={item.name}
              indicator={indicators[item.key]}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
