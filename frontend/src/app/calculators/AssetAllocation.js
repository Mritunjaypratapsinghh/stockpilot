'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';
import { api } from '../../lib/api';

const COLORS = ['#6366f1', '#10b981', '#f59e0b'];
const RISK_LEVELS = ['very_low', 'low', 'moderate', 'high', 'very_high'];
const RISK_LABELS = { very_low: 'Very Low', low: 'Low', moderate: 'Moderate', high: 'High', very_high: 'Very High' };

const s = {
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 1000, margin: '0 auto', padding: 0 },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  title: { fontSize: 18, fontWeight: 600, margin: '0 0 24px 0', padding: 0 },
  label: { fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 8px 0', padding: 0 },
  value: { fontSize: 13, fontWeight: 500, color: 'var(--accent)', margin: 0, padding: 0 },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 8px 0', padding: 0 },
  slider: { width: '100%', height: 6, margin: '8px 0', padding: 0, accentColor: 'var(--accent)' },
  sliderLabels: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', margin: 0, padding: 0 },
  section: { margin: '0 0 24px 0', padding: 0 },
  riskBtns: { display: 'flex', gap: 4, margin: 0, padding: 0 },
  riskBtn: { flex: 1, padding: '8px 4px', margin: 0, border: 'none', borderRadius: 6, fontSize: 11, cursor: 'pointer', transition: 'all 0.15s' },
  breakdown: { background: 'var(--bg-tertiary)', borderRadius: 8, padding: 16, margin: '16px 0 0 0' },
  breakdownTitle: { fontSize: 13, fontWeight: 500, margin: '0 0 12px 0', padding: 0 },
  breakdownRow: { display: 'flex', justifyContent: 'space-between', fontSize: 13, margin: '0 0 6px 0', padding: 0 },
  footer: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--text-muted)', margin: '16px 0 0 0', padding: 0 },
  check: { width: 16, height: 16, borderRadius: '50%', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: 0, padding: 0 },
};

export default function AssetAllocation() {
  const [age, setAge] = useState(30);
  const [risk, setRisk] = useState('moderate');
  const [horizon, setHorizon] = useState(10);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/asset-allocation?age=${age}&risk_appetite=${risk}&horizon=${horizon}`)
      .then(setResult).catch(console.error);
  }, [age, risk, horizon]);

  const chartData = result ? [
    { name: 'Equity', value: result.recommended.equity },
    { name: 'Debt', value: result.recommended.debt },
    { name: 'Gold', value: result.recommended.gold },
  ] : [];

  return (
    <div>
      <div style={s.grid}>
        <div style={s.card}>
          <h2 style={s.title}>Your Profile</h2>
          
          <div style={s.section}>
            <div style={s.row}>
              <span style={s.label}>Your Age</span>
              <span style={s.value}>{age} Yrs</span>
            </div>
            <input type="range" min="18" max="70" value={age} onChange={e => setAge(+e.target.value)} style={s.slider} />
            <div style={s.sliderLabels}><span>18</span><span>70</span></div>
          </div>

          <div style={s.section}>
            <div style={s.row}>
              <span style={s.label}>Risk Appetite</span>
              <span style={s.value}>{RISK_LABELS[risk]}</span>
            </div>
            <div style={s.riskBtns}>
              {RISK_LEVELS.map(r => (
                <button key={r} onClick={() => setRisk(r)}
                  style={{ ...s.riskBtn, background: risk === r ? 'var(--accent)' : 'var(--bg-tertiary)', color: risk === r ? '#fff' : 'var(--text-secondary)' }}>
                  {RISK_LABELS[r].split(' ')[0]}
                </button>
              ))}
            </div>
          </div>

          <div style={s.section}>
            <div style={s.row}>
              <span style={s.label}>Investment Horizon</span>
              <span style={s.value}>{horizon} Yrs</span>
            </div>
            <input type="range" min="1" max="30" value={horizon} onChange={e => setHorizon(+e.target.value)} style={s.slider} />
            <div style={s.sliderLabels}><span>1 Yr</span><span>30 Yrs</span></div>
          </div>
        </div>

        <div style={s.card}>
          <h2 style={s.title}>Recommended Allocation</h2>
          {result && (
            <>
              <div style={{ height: 220, margin: 0, padding: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={chartData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, value }) => `${name} ${value}%`}>
                      {chartData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                    </Pie>
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={s.breakdown}>
                <div style={s.breakdownTitle}>Breakdown</div>
                <div style={s.breakdownRow}><span style={{ color: 'var(--text-muted)' }}>Large Cap</span><span>{result.recommended.breakdown.large_cap}%</span></div>
                <div style={s.breakdownRow}><span style={{ color: 'var(--text-muted)' }}>Mid Cap</span><span>{result.recommended.breakdown.mid_cap}%</span></div>
                <div style={s.breakdownRow}><span style={{ color: 'var(--text-muted)' }}>Small Cap</span><span>{result.recommended.breakdown.small_cap}%</span></div>
                <div style={s.breakdownRow}><span style={{ color: 'var(--text-muted)' }}>Debt</span><span>{result.recommended.breakdown.debt_fund}%</span></div>
              </div>
            </>
          )}
        </div>
      </div>
      <div style={s.footer}>
        <span style={s.check}>✓</span>
        Verified Methodology: Based on Modern Portfolio Theory
      </div>
    </div>
  );
}
