import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

const RANGE_OPTIONS = [
  { label: '7일', days: 7 },
  { label: '30일', days: 30 },
];

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: '#1a1d28',
        border: '1px solid #252836',
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: 12,
      }}
    >
      <div style={{ color: '#8b8da3', marginBottom: 4 }}>{label}</div>
      <div style={{ color: '#e4e4e7', fontWeight: 600 }}>
        {payload[0].value?.toLocaleString(undefined, {
          maximumFractionDigits: 2,
        })}
      </div>
    </div>
  );
}

export default function HistoryChart({ data, color = 'var(--blue)' }) {
  const [range, setRange] = useState(7);

  if (!data || data.length === 0) return null;

  const filtered = data.slice(-range).map((d) => ({
    ...d,
    dateLabel: formatDate(d.date),
  }));

  return (
    <div style={{ marginTop: 12 }}>
      <div
        style={{
          display: 'flex',
          gap: 6,
          marginBottom: 10,
          justifyContent: 'flex-end',
        }}
      >
        {RANGE_OPTIONS.map((opt) => (
          <button
            key={opt.days}
            onClick={(e) => {
              e.stopPropagation();
              setRange(opt.days);
            }}
            style={{
              background:
                range === opt.days ? 'rgba(96, 165, 250, 0.15)' : 'transparent',
              border: `1px solid ${range === opt.days ? 'rgba(96, 165, 250, 0.4)' : 'var(--border)'}`,
              borderRadius: 8,
              padding: '4px 12px',
              fontSize: 12,
              color: range === opt.days ? 'var(--blue)' : 'var(--dim)',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={140}>
        <LineChart data={filtered}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.04)"
            vertical={false}
          />
          <XAxis
            dataKey="dateLabel"
            tick={{ fill: '#8b8da3', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#8b8da3', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={45}
            domain={['auto', 'auto']}
            tickFormatter={(v) =>
              v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v
            }
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: color }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
