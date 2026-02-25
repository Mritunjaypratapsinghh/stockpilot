'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { api } from '../../lib/api';

const fmt = n => n?.toLocaleString('en-IN') || '0';

const s = {
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 1000, margin: '0 auto', padding: 0 },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  title: { fontSize: 18, fontWeight: 600, margin: '0 0 24px 0', padding: 0 },
  label: { fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 8px 0', padding: 0, display: 'block' },
  input: { width: '100%', padding: '12px 16px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 16, color: 'var(--text-primary)' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 8px 0', padding: 0 },
  slider: { width: '100%', height: 6, margin: '8px 0', padding: 0, accentColor: 'var(--accent)' },
  section: { margin: '0 0 20px 0', padding: 0 },
  btn: { width: '100%', padding: '12px', margin: 0, border: '1px solid var(--accent)', borderRadius: 8, background: 'transparent', color: 'var(--accent)', fontSize: 13, fontWeight: 500, cursor: 'pointer' },
  statCard: { background: 'var(--bg-tertiary)', borderRadius: 8, padding: 12, margin: 0 },
  statLabel: { fontSize: 11, color: 'var(--text-muted)', margin: '0 0 4px 0', padding: 0, textTransform: 'uppercase' },
  statValue: { fontSize: 18, fontWeight: 600, margin: 0, padding: 0 },
  green: { color: '#10b981' },
  gridStats: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, margin: 0, padding: 0 },
  compareCard: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 16, margin: '16px 0 0 0' },
};

export default function SIPStepup() {
  const [amount, setAmount] = useState(10000);
  const [returns, setReturns] = useState(12);
  const [years, setYears] = useState(10);
  const [stepup, setStepup] = useState(10);
  const [result, setResult] = useState(null);
  const [showBreakdown, setShowBreakdown] = useState(false);

  useEffect(() => {
    api(`/api/v1/calculators/sip-stepup?monthly_amount=${amount}&expected_return=${returns}&years=${years}&annual_stepup=${stepup}`)
      .then(setResult).catch(console.error);
  }, [amount, returns, years, stepup]);

  const chartData = result ? [
    { name: 'Invested', value: result.stepup.total_invested },
    { name: 'Gains', value: result.stepup.wealth_gained },
  ] : [];

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: 0 }}>
      <div style={s.grid}>
        <div style={s.card}>
          <h2 style={s.title}>SIP Configuration</h2>
          
          <div style={s.section}>
            <label style={s.label}>Monthly Investment (₹)</label>
            <input type="number" value={amount} onChange={e => setAmount(+e.target.value)} style={s.input} />
          </div>

          <div style={s.section}>
            <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Expected Return</span><span style={{ fontSize: 13, fontWeight: 500 }}>{returns}%</span></div>
            <input type="range" min="6" max="20" value={returns} onChange={e => setReturns(+e.target.value)} style={s.slider} />
          </div>

          <div style={s.section}>
            <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Time Period</span><span style={{ fontSize: 13, fontWeight: 500 }}>{years} Years</span></div>
            <input type="range" min="1" max="30" value={years} onChange={e => setYears(+e.target.value)} style={s.slider} />
          </div>

          <div style={s.section}>
            <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Annual Step-up</span><span style={{ fontSize: 13, fontWeight: 500 }}>{stepup}%</span></div>
            <input type="range" min="0" max="25" value={stepup} onChange={e => setStepup(+e.target.value)} style={s.slider} />
          </div>

          <button onClick={() => setShowBreakdown(!showBreakdown)} style={s.btn}>
            {showBreakdown ? 'Hide' : 'View'} Yearly Breakdown →
          </button>
        </div>

        <div>
          {result && (
            <>
              <div style={s.card}>
                <div style={{ height: 180, margin: '0 0 16px 0', padding: 0 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={chartData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value">
                        <Cell fill="#6366f1" />
                        <Cell fill="#10b981" />
                      </Pie>
                      <text x="50%" y="45%" textAnchor="middle" style={{ fontSize: 11, fill: 'var(--text-muted)' }}>TOTAL VALUE</text>
                      <text x="50%" y="58%" textAnchor="middle" style={{ fontSize: 16, fontWeight: 600, fill: 'var(--text-primary)' }}>₹{fmt(result.stepup.corpus)}</text>
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div style={s.gridStats}>
                  <div style={s.statCard}>
                    <div style={s.statLabel}>Total Invested</div>
                    <div style={s.statValue}>₹{fmt(result.stepup.total_invested)}</div>
                  </div>
                  <div style={{ ...s.statCard, background: 'rgba(16,185,129,0.1)' }}>
                    <div style={{ ...s.statLabel, color: '#10b981' }}>Wealth Gained</div>
                    <div style={{ ...s.statValue, ...s.green }}>₹{fmt(result.stepup.wealth_gained)}</div>
                  </div>
                </div>

                <div style={{ ...s.statCard, margin: '12px 0 0 0', display: 'flex', justifyContent: 'space-between' }}>
                  <div><div style={s.statLabel}>Maturity Value</div><div style={{ fontSize: 16, fontWeight: 600, color: 'var(--accent)' }}>₹{fmt(result.stepup.corpus)}</div></div>
                  <div style={{ textAlign: 'right' }}><div style={s.statLabel}>Last Monthly SIP</div><div style={{ fontSize: 16, fontWeight: 600 }}>₹{fmt(result.stepup.last_monthly_sip)}</div></div>
                </div>
              </div>

              <div style={s.compareCard}>
                <div style={{ fontSize: 13, fontWeight: 500, margin: '0 0 12px 0' }}>Flat SIP vs Step-up SIP</div>
                <div style={s.gridStats}>
                  <div style={s.statCard}><div style={s.statLabel}>Flat SIP Corpus</div><div style={{ fontSize: 14, fontWeight: 600 }}>₹{fmt(result.flat.corpus)}</div></div>
                  <div style={{ ...s.statCard, background: 'rgba(99,102,241,0.1)' }}><div style={{ ...s.statLabel, color: 'var(--accent)' }}>Step-up Advantage</div><div style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent)' }}>+₹{fmt(result.stepup.corpus - result.flat.corpus)}</div></div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {showBreakdown && result && (
        <div style={{ ...s.card, margin: '24px auto 0', maxWidth: 1000 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 16px 0' }}>Yearly Breakdown</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead><tr style={{ textAlign: 'left', color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>
              <th style={{ padding: '8px 0' }}>Year</th><th style={{ padding: '8px 0' }}>Monthly SIP</th><th style={{ padding: '8px 0' }}>Year Invested</th><th style={{ padding: '8px 0' }}>Cumulative</th>
            </tr></thead>
            <tbody>
              {result.yearly_breakdown.map(row => (
                <tr key={row.year} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '8px 0' }}>{row.year}</td>
                  <td style={{ padding: '8px 0' }}>₹{fmt(row.monthly_sip)}</td>
                  <td style={{ padding: '8px 0' }}>₹{fmt(row.year_invested)}</td>
                  <td style={{ padding: '8px 0' }}>₹{fmt(row.cumulative_invested)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
