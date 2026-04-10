import React, { useEffect, useState } from 'react';
import PhasePanel from './components/PhasePanel';
import IndicatorCard from './components/IndicatorCard';
import SectionHeader from './components/SectionHeader';

// ── 섹션 정의 ──────────────────────────────────────────

const US_MARKET_KEYS = [
  { key: 'vix', name: 'VIX (변동성 지수)' },
  { key: 'sp500', name: 'S&P 500' },
  { key: 'nasdaq', name: 'NASDAQ' },
  { key: 'dxy', name: 'DXY (달러 인덱스)', desc: '6개 주요 통화 대비 달러 가치' },
  { key: 'us10y', name: '미국 10년물 금리' },
  { key: 'us2y', name: '미국 2년물 금리' },
  { key: 'spread_2_10', name: '2-10 스프레드' },
  { key: 'gold', name: '금 (Gold)' },
  { key: 'wti', name: 'WTI 원유' },
  { key: 'copper', name: '구리 (Copper)' },
  { key: 'tga', name: 'TGA (재무부 일반계정)' },
  { key: 'rrp', name: 'RRP (역레포)' },
  { key: 'm2', name: 'M2 통화량' },
  { key: 'fed_balance', name: '연준 대차대조표' },
];

const KR_MARKET_KEYS = [
  { key: 'kospi', name: 'KOSPI' },
  { key: 'usdkrw', name: '원/달러 환율', desc: '원화 기준 달러 환율 (DXY와 별개)' },
  { key: 'kr10y', name: '한국 국고채 10년' },
  { key: 'kr2y', name: '한국 국고채 2년' },
];

const HEALTH_KEYS = [
  { key: 'us_cc_delinq', name: '🇺🇸 신용카드 연체율' },
  { key: 'us_auto_delinq', name: '🇺🇸 자동차 할부 연체율' },
  { key: 'us_mortgage_delinq', name: '🇺🇸 주담대 연체율' },
  { key: 'us_saving_rate', name: '🇺🇸 개인 저축률' },
  { key: 'kr_delinquency', name: '🇰🇷 가계대출 연체율' },
];

// ── 데모 데이터 ────────────────────────────────────────

function genHistory(base, vol, days = 30) {
  const r = [];
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const n = (Math.random() - 0.5) * vol * 2;
    r.push({ date: d.toISOString().slice(0, 10), value: +(base + n).toFixed(2) });
    base += n * 0.3;
  }
  return r;
}

const DEMO_DATA = {
  updated_at: new Date().toISOString(),
  phase: { status: 'mixed', score: 2, reasons: ['VIX 25 수준 — 불안정', 'S&P 500 200일선 근접', 'M2 증가 추세 확인'] },
  indicators: {
    vix: { value: 25.3, change: -2.1, change_pct: -7.66, signal: 'yellow', note: '20 이하 안정 / 30+ 위험' },
    sp500: { value: 5124.5, change: 45.2, change_pct: 0.89, signal: 'green', note: '200일선: 5,050' },
    nasdaq: { value: 16032.1, change: 189.3, change_pct: 1.19, signal: 'green', note: '' },
    dxy: { value: 104.32, change: -0.45, change_pct: -0.43, signal: 'yellow', note: '6개 주요 통화 대비 달러 가치' },
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
    kospi: { value: 2654.3, change: 28.1, change_pct: 1.07, signal: 'green', note: '' },
    usdkrw: { value: 1385.2, change: -5.3, change_pct: -0.38, signal: 'green', note: '환율 상승 = 원화 약세' },
    kr10y: { value: 3.42, change: -0.03, change_pct: -0.87, signal: 'yellow', note: '' },
    kr2y: { value: 3.15, change: -0.02, change_pct: -0.63, signal: 'yellow', note: '' },
    us_cc_delinq: { value: 2.98, change: 0.11, change_pct: 3.83, signal: 'yellow', note: '3%+ 경고' },
    us_auto_delinq: { value: 2.85, change: 0.08, change_pct: 2.89, signal: 'yellow', note: '3%+ 경고' },
    us_mortgage_delinq: { value: 1.72, change: -0.03, change_pct: -1.71, signal: 'green', note: '4%+ 위험' },
    us_saving_rate: { value: 4.6, change: -0.2, change_pct: -4.17, signal: 'yellow', note: '5% 이상 건전' },
    kr_delinquency: { value: 0.48, change: 0.02, change_pct: 4.35, signal: 'green', note: '1%+ 경고' },
  },
};

const DEMO_HISTORY = Object.fromEntries([
  ['vix', genHistory(25, 3)], ['sp500', genHistory(5100, 80)], ['nasdaq', genHistory(15900, 250)],
  ['dxy', genHistory(104, 1)], ['us10y', genHistory(4.3, 0.1)], ['us2y', genHistory(4.7, 0.1)],
  ['spread_2_10', genHistory(-0.4, 0.05)], ['gold', genHistory(2300, 30)], ['wti', genHistory(79, 3)],
  ['copper', genHistory(4.1, 0.15)], ['tga', genHistory(760, 20)], ['rrp', genHistory(460, 30)],
  ['m2', genHistory(21000, 100)], ['fed_balance', genHistory(7430, 20)],
  ['kospi', genHistory(2650, 40)], ['usdkrw', genHistory(1385, 10)],
  ['kr10y', genHistory(3.4, 0.08)], ['kr2y', genHistory(3.15, 0.06)],
  ['us_cc_delinq', genHistory(2.9, 0.1)], ['us_auto_delinq', genHistory(2.8, 0.1)],
  ['us_mortgage_delinq', genHistory(1.7, 0.05)], ['us_saving_rate', genHistory(4.6, 0.3)],
  ['kr_delinquency', genHistory(0.48, 0.03)],
]);

// ── 유틸 ────────────────────────────────────────────────

function formatTime(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())} KST`;
}

function renderSection(keys, indicators, history) {
  return keys.map(
    (item) =>
      indicators[item.key] && (
        <IndicatorCard
          key={item.key}
          name={item.name}
          desc={item.desc}
          indicator={indicators[item.key]}
          history={history?.[item.key]}
        />
      )
  );
}

// ── 앱 ──────────────────────────────────────────────────

export default function App() {
  const [data, setData] = useState(null);
  const [history, setHistory] = useState(null);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const base = import.meta.env.BASE_URL;
        const [latestRes, historyRes] = await Promise.all([
          fetch(`${base}data/latest.json`).then((r) => r.json()),
          fetch(`${base}data/history.json`).then((r) => r.json()),
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
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'var(--dim)', fontSize: 14 }}>
        로딩 중…
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <header
        style={{
          position: 'sticky', top: 0, zIndex: 100,
          background: 'rgba(15, 17, 23, 0.85)',
          backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)',
          borderBottom: '1px solid var(--border)', padding: '14px 20px',
        }}
      >
        <h1 style={{ fontSize: 18, fontWeight: 700 }}>📊 투자 지표 확인</h1>
        <div style={{ fontSize: 12, color: 'var(--dim)', marginTop: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{formatTime(data.updated_at)}</span>
          {isDemo && (
            <span style={{ fontSize: 10, background: 'rgba(250,204,21,0.15)', color: 'var(--yellow)', padding: '2px 8px', borderRadius: 6 }}>
              DEMO
            </span>
          )}
        </div>
      </header>

      {/* Phase Panel */}
      <div style={{ padding: '16px 0 0' }}>
        <PhasePanel phase={data.phase} />
      </div>

      {/* 🇺🇸 미국 시장 */}
      <div style={{ padding: '0 16px' }}>
        <SectionHeader icon="🇺🇸" title="미국 시장" />
        {renderSection(US_MARKET_KEYS, data.indicators, history)}
      </div>

      {/* 🇰🇷 한국 시장 */}
      <div style={{ padding: '0 16px' }}>
        <SectionHeader icon="🇰🇷" title="한국 시장" />
        {renderSection(KR_MARKET_KEYS, data.indicators, history)}
      </div>

      {/* 💳 신용·가계 건전성 */}
      <div style={{ padding: '0 16px' }}>
        <SectionHeader icon="💳" title="신용·가계 건전성" subtitle="분기 갱신" />
        {renderSection(HEALTH_KEYS, data.indicators, history)}
      </div>
    </>
  );
}
