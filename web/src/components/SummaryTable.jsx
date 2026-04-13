import React from 'react';

const SIGNAL_COLORS = {
  green: '#4ade80',
  yellow: '#facc15',
  orange: '#fb923c',
  red: '#f87171',
};

// 테이블용 짧은 이름
const SHORT_NAMES = {
  vix: 'VIX', sp500: 'S&P 500', nasdaq: 'NASDAQ',
  qqq: 'QQQ', schd: 'SCHD', dxy: 'DXY',
  fed_rate: '기준금리', us10y: '10년물', us2y: '2년물',
  spread_2_10: '2-10 스프레드', gold: '금', wti: 'WTI',
  copper: '구리', tga: 'TGA', rrp: 'RRP',
  m2: 'M2', fed_balance: '연준 B/S',
  kospi: 'KOSPI', usdkrw: '원/달러', kr_rate: '기준금리',
  kr10y: '10년물', kr2y: '2년물',
  us_cc_delinq: 'CC 연체', us_auto_delinq: 'Auto 연체',
  us_mortgage_delinq: '주담대', us_saving_rate: '저축률',
  kr_delinquency: '가계 연체',
};

const ICONS = {
  vix: '⚡', sp500: '🇺🇸', nasdaq: '🖥️',
  qqq: '📈', schd: '💎', dxy: '💲',
  fed_rate: '🏛️', us10y: '📉', us2y: '📈', spread_2_10: '⊕',
  gold: '🥇', wti: '🛢️', copper: '🔶', tga: '🏦', rrp: '🔄',
  m2: '💰', fed_balance: '📊',
  kospi: '🇰🇷', usdkrw: '💱', kr_rate: '🏛️', kr10y: '📉', kr2y: '📈',
  us_cc_delinq: '💳', us_auto_delinq: '🚗', us_mortgage_delinq: '🏠',
  us_saving_rate: '🐖', kr_delinquency: '🇰🇷',
};

const SUBTITLES = {
  vix: '공포지수', sp500: '미국 대형주', nasdaq: '기술주',
  qqq: '나스닥100 ETF', schd: '배당성장 ETF', dxy: '달러인덱스',
  fed_rate: 'FOMC 상단', us10y: '국채 금리', us2y: '국채 금리',
  spread_2_10: '장단기 금리차', gold: 'Gold Spot', wti: 'Crude Oil',
  copper: '경기선행', tga: '재무부 계정', rrp: '역레포', m2: '통화량',
  fed_balance: 'QT/QE', kospi: '한국 종합', usdkrw: '환율',
  kr_rate: '기준금리', kr10y: '국고채', kr2y: '국고채',
  us_cc_delinq: '신용카드', us_auto_delinq: '자동차할부',
  us_mortgage_delinq: '주담대', us_saving_rate: '개인저축',
  kr_delinquency: '가계대출',
};

const DESCRIPTIONS = {
  vix: '20 이하 안정 / 30+ 위험',
  sp500: '200일선 위 = 강세장',
  nasdaq: 'S&P 대비 상대강도',
  qqq: '나스닥100 추종',
  schd: '배당+성장 ETF',
  dxy: '100 이상 = 달러 강세',
  fed_rate: '인하 시 유동성 확대',
  us10y: '4%↑ = 밸류 압박',
  us2y: '기준금리 방향 선행',
  spread_2_10: '0bp 이하 = 침체 신호',
  gold: '상승 = 안전자산 선호',
  wti: '고유가 = 인플레·매파',
  copper: '상승 = 경기 확장',
  tga: '감소 = 유동성 방출',
  rrp: '감소 = 유동성 유입',
  m2: '증가 = 유동성 확대',
  fed_balance: '증가=QE / 감소=QT',
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
  if (['us10y', 'us2y', 'fed_rate', 'kr10y', 'kr2y', 'kr_rate',
       'us_cc_delinq', 'us_auto_delinq', 'us_mortgage_delinq',
       'us_saving_rate', 'kr_delinquency'].includes(key)) {
    return `${value.toFixed(2)}%`;
  }
  if (key === 'spread_2_10') {
    return `${value > 0 ? '+' : ''}${(value * 100).toFixed(0)}bp`;
  }
  if (['gold', 'wti', 'copper'].includes(key)) {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function formatChange(key, indicator) {
  const change = indicator.change;
  const changePct = indicator.change_pct;
  if (change == null && changePct == null) return null;

  if (key === 'spread_2_10') {
    const bp = change != null ? (change * 100).toFixed(0) : '0';
    return `${change >= 0 ? '+' : ''}${bp}bp`;
  }
  if (['us10y', 'us2y', 'fed_rate', 'kr10y', 'kr2y', 'kr_rate'].includes(key)) {
    const bp = change != null ? Math.round(change * 100) : 0;
    return `${bp >= 0 ? '+' : ''}${bp}bp`;
  }
  if (changePct != null) {
    const sign = changePct >= 0 ? '+' : '';
    return `${sign}${changePct.toFixed(1)}%`;
  }
  return null;
}

function SummaryRow({ itemKey, indicator }) {
  if (!indicator) return null;

  const signal = indicator.signal || 'yellow';
  const signalColor = SIGNAL_COLORS[signal] || SIGNAL_COLORS.yellow;
  const icon = ICONS[itemKey] || '';
  const shortName = SHORT_NAMES[itemKey] || itemKey;
  const subtitle = SUBTITLES[itemKey] || '';
  const desc = indicator.note || DESCRIPTIONS[itemKey] || '';

  const changeStr = formatChange(itemKey, indicator);
  const changeNum = indicator.change_pct || indicator.change || 0;
  const changeColor = changeNum > 0 ? 'var(--green)' : changeNum < 0 ? 'var(--red)' : 'var(--dim)';

  return (
    <div style={{
      display: 'flex', alignItems: 'center',
      padding: '10px 8px', borderBottom: '1px solid var(--border)',
    }}>
      {/* 색상 바 */}
      <div style={{
        width: 3, minHeight: 36, alignSelf: 'stretch',
        borderRadius: 2, background: signalColor, flexShrink: 0,
      }} />

      {/* 이름 블록 */}
      <div style={{ width: 80, flexShrink: 0, paddingLeft: 8, overflow: 'hidden' }}>
        <div style={{
          fontSize: 13, fontWeight: 700, color: signalColor,
          lineHeight: 1.2,
        }}>
          {icon} {shortName}
        </div>
        <div style={{ fontSize: 10, color: 'var(--dim)', marginTop: 2 }}>{subtitle}</div>
      </div>

      {/* 수치 블록 */}
      <div style={{ width: 90, flexShrink: 0, textAlign: 'right', paddingRight: 10 }}>
        <div style={{
          fontSize: 16, fontWeight: 800,
          fontFamily: "'SF Mono', 'Fira Code', monospace",
          letterSpacing: '-0.5px', lineHeight: 1.2,
        }}>
          {formatValue(itemKey, indicator.value)}
        </div>
        {changeStr && (
          <div style={{ fontSize: 11, color: changeColor, fontFamily: "'SF Mono', monospace", marginTop: 1 }}>
            {changeStr}
          </div>
        )}
      </div>

      {/* 신호등 */}
      <div style={{ width: 26, flexShrink: 0, display: 'flex', justifyContent: 'center' }}>
        <div style={{
          width: 18, height: 18, borderRadius: '50%',
          background: signalColor, boxShadow: `0 0 6px ${signalColor}40`,
        }} />
      </div>

      {/* 기준선 설명 */}
      <div style={{
        flex: 1, fontSize: 11, color: 'var(--dim)',
        lineHeight: 1.3, paddingLeft: 8, minWidth: 0,
      }}>
        {desc}
      </div>
    </div>
  );
}

export default function SummaryTable({ sections, indicators }) {
  if (!indicators) return null;

  return (
    <div style={{ padding: '0 4px' }}>
      {/* 컬럼 헤더 */}
      <div style={{
        display: 'flex', alignItems: 'center',
        padding: '6px 8px', fontSize: 10, color: 'var(--dim)',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ width: 3 }} />
        <div style={{ width: 80, paddingLeft: 8 }}>이름</div>
        <div style={{ width: 90, textAlign: 'right', paddingRight: 10 }}>수치</div>
        <div style={{ width: 26 }} />
        <div style={{ flex: 1, paddingLeft: 8 }}>기준선</div>
      </div>

      {sections.map((section, si) => (
        <div key={si}>
          <div style={{
            padding: '8px 11px 6px', fontSize: 12, fontWeight: 700,
            color: 'var(--dim)', background: 'rgba(255,255,255,0.03)',
            borderBottom: '1px solid var(--border)',
          }}>
            {section.icon} {section.title}
          </div>
          {section.keys.map((item) => (
            <SummaryRow key={item.key} itemKey={item.key} indicator={indicators[item.key]} />
          ))}
        </div>
      ))}
    </div>
  );
}
