import React, { useEffect, useState } from 'react';
import PhasePanel from './components/PhasePanel';
import IndicatorCard from './components/IndicatorCard';
import LiquiditySection from './components/LiquiditySection';

const MARKET_KEYS = [
  { key: 'vix', name: 'VIX (변동성 지수)' },
  { key: 'sp500', name: 'S&P 500' },
  { key: 'nasdaq', name: 'NASDAQ' },
  { key: 'dxy', name: 'DXY (달러 인덱스)' },
  { key: 'us10y', name: '미국 10년물 금리' },
  { key: 'us2y', name: '미국 2년물 금리' },
  { key: 'spread_2_10', name: '2-10 스프레드' },
  { key: 'gold', name: '금 (Gold)' },
  { key: 'wti', name: 'WTI 원유' },
  { key: 'copper', name: '구리 (Copper)' },
];

// 데모 데이터 — fetch_data.py가 실제 데이터를 생성하면 이 fallback은 사용되지 않음
function generateDemoHistory(base, volatility, days = 30) {
  const result = [];
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const noise = (Math.random() - 0.5) * volatility * 2;
    result.push({
      date: d.toISOString().slice(0, 10),
      value: +(base + noise).toFixed(2),
    });
    base = base + noise * 0.3;
  }
  return result;
}

const DEMO_DATA = {
  updated_at: new Date().toISOString(),
  phase: {
    status: 'mixed',
    score: 2,
    reasons: [
      'VIX 25 수준 — 불안정',
      'S&P 500 200일선 근접',
      'M2 증가 추세 확인',
    ],
  },
  indicators: {
    vix: { value: 25.3, change: -2.1, change_pct: -7.66, signal: 'yellow', note: '20 이하 안정 / 30+ 위험' },
    sp500: { value: 5124.5, change: 45.2, change_pct: 0.89, signal: 'green', note: '200일선: 5,050' },
    nasdaq: { value: 16032.1, change: 189.3, change_pct: 1.19, signal: 'green', note: '' },
    dxy: { value: 104.32, change: -0.45, change_pct: -0.43, signal: 'yellow', note: '달러 약세 시 위험자산 유리' },
    us10y: { value: 4.35, change: -0.08, change_pct: -1.81, signal: 'yellow', note: '금리 하락 = 채권 가격 상승' },
    us2y: { value: 4.72, change: -0.05, change_pct: -1.05, signal: 'yellow', note: '' },
    spread_2_10: { value: -0.37, change: 0.03, change_pct: 7.5, signal: 'red', note: '역전 시 경기침체 경고' },
    gold: { value: 2345.6, change: 18.3, change_pct: 0.79, signal: 'green', note: '안전자산 선호 시 상승' },
    wti: { value: 78.45, change: -1.2, change_pct: -1.51, signal: 'yellow', note: '' },
    copper: { value: 4.12, change: 0.05, change_pct: 1.23, signal: 'green', note: '경기 선행 지표' },
    tga: { value: 750.2, change: -12.5, change_pct: -1.64, signal: 'green', note: 'TGA 감소 = 유동성 공급' },
    rrp: { value: 438.1, change: -25.3, change_pct: -5.46, signal: 'green', note: 'RRP 감소 = 유동성 증가' },
    m2: { value: 21050.0, change: 120.0, change_pct: 0.57, signal: 'green', note: 'M2 증가 = 유동성 확대' },
    fed_balance: { value: 7420.5, change: -15.2, change_pct: -0.2, signal: 'yellow', note: 'QT 진행 중' },
  },
};

const DEMO_HISTORY = {
  vix: generateDemoHistory(25, 3),
  sp500: generateDemoHistory(5100, 80),
  nasdaq: generateDemoHistory(15900, 250),
  dxy: generateDemoHistory(104, 1),
  us10y: generateDemoHistory(4.3, 0.1),
  us2y: generateDemoHistory(4.7, 0.1),
  spread_2_10: generateDemoHistory(-0.4, 0.05),
  gold: generateDemoHistory(2300, 30),
  wti: generateDemoHistory(79, 3),
  copper: generateDemoHistory(4.1, 0.15),
  tga: generateDemoHistory(760, 20),
  rrp: generateDemoHistory(460, 30),
  m2: generateDemoHistory(21000, 100),
  fed_balance: generateDemoHistory(7430, 20),
};

function formatTime(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())} KST`;
}

export default function App() {
  const [data, setData] = useState(null);
  const [history, setHistory] = useState(null);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const [latestRes, historyRes] = await Promise.all([
          fetch('./data/latest.json').then((r) => r.json()),
          fetch('./data/history.json').then((r) => r.json()),
        ]);

        const hasData = latestRes?.indicators && Object.keys(latestRes.indicators).length > 0;
        if (hasData) {
          setData(latestRes);
          setHistory(historyRes);
        } else {
          setData(DEMO_DATA);
          setHistory(DEMO_HISTORY);
          setIsDemo(true);
        }
      } catch {
        setData(DEMO_DATA);
        setHistory(DEMO_HISTORY);
        setIsDemo(true);
      }
    }

    fetchData();
  }, []);

  if (!data) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          color: 'var(--dim)',
          fontSize: 14,
        }}
      >
        로딩 중…
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          background: 'rgba(15, 17, 23, 0.85)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderBottom: '1px solid var(--border)',
          padding: '14px 20px',
        }}
      >
        <h1 style={{ fontSize: 18, fontWeight: 700 }}>📊 투자 지표 확인</h1>
        <div
          style={{
            fontSize: 12,
            color: 'var(--dim)',
            marginTop: 2,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>{formatTime(data.updated_at)}</span>
          {isDemo && (
            <span
              style={{
                fontSize: 10,
                background: 'rgba(250,204,21,0.15)',
                color: 'var(--yellow)',
                padding: '2px 8px',
                borderRadius: 6,
              }}
            >
              DEMO
            </span>
          )}
        </div>
      </header>

      {/* Phase Panel */}
      <div style={{ padding: '16px 0 0' }}>
        <PhasePanel phase={data.phase} />
      </div>

      {/* Market Indicators */}
      <div style={{ padding: '0 16px' }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 700,
            color: 'var(--dim)',
            textTransform: 'uppercase',
            letterSpacing: 1,
            marginBottom: 10,
          }}
        >
          📈 시장 지표
        </div>
        {MARKET_KEYS.map(
          (mk) =>
            data.indicators[mk.key] && (
              <IndicatorCard
                key={mk.key}
                name={mk.name}
                indicator={data.indicators[mk.key]}
                history={history?.[mk.key]}
              />
            )
        )}
      </div>

      {/* Liquidity Section */}
      <LiquiditySection indicators={data.indicators} history={history} />
    </>
  );
}
