'use client';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { api } from '../../lib/api';

const fmt = n => n?.toLocaleString('en-IN') || '0';

const s = {
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 1100, margin: '0 auto', padding: 0 },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  title: { fontSize: 18, fontWeight: 600, margin: '0 0 4px 0', padding: 0 },
  subtitle: { fontSize: 13, color: 'var(--text-muted)', margin: '0 0 24px 0', padding: 0 },
  label: { fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 8px 0', padding: 0, display: 'block' },
  input: { width: '100%', padding: '12px 16px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 14, color: 'var(--text-primary)' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 8px 0', padding: 0 },
  slider: { width: '100%', height: 6, margin: '8px 0', padding: 0, accentColor: 'var(--accent)' },
  sliderLabels: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', margin: '0 0 4px 0', padding: 0 },
  section: { margin: '0 0 20px 0', padding: 0 },
  hint: { fontSize: 11, color: 'var(--text-muted)', margin: '4px 0 0 0', padding: 0 },
  summary: { background: 'var(--bg-tertiary)', borderRadius: 8, padding: 16, margin: '20px 0 0 0' },
  summaryTitle: { fontSize: 12, fontWeight: 600, margin: '0 0 12px 0', padding: 0 },
  summaryRow: { display: 'flex', justifyContent: 'space-between', fontSize: 13, margin: '0 0 8px 0', padding: 0 },
  status: { borderRadius: 12, padding: 20, margin: '0 0 16px 0', color: '#fff' },
  statusTitle: { fontSize: 12, opacity: 0.8, margin: '0 0 4px 0', padding: 0 },
  statusValue: { fontSize: 24, fontWeight: 700, margin: '0 0 8px 0', padding: 0 },
  statusDesc: { fontSize: 13, opacity: 0.9, margin: 0, padding: 0 },
};

export default function SWPCalculator() {
  const [corpus, setCorpus] = useState(5000000);
  const [withdrawal, setWithdrawal] = useState(30000);
  const [stepup, setStepup] = useState(0);
  const [returns, setReturns] = useState(10);
  const [years, setYears] = useState(20);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/swp?corpus=${corpus}&monthly_withdrawal=${withdrawal}&annual_stepup=${stepup}&expected_return=${returns}&years=${years}`)
      .then(setResult).catch(console.error);
  }, [corpus, withdrawal, stepup, returns, years]);

  const chartData = result?.trajectory.map(t => ({ year: `${t.year}y`, balance: t.end_balance, withdrawn: t.withdrawn })) || [];

  return (
    <div style={s.grid}>
      <div style={s.card}>
        <h2 style={s.title}>SWP Configuration</h2>
        <p style={s.subtitle}>Plan your regular income with inflation</p>
        
        <div style={s.section}>
          <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Total Investment</span><span style={{ fontSize: 13 }}>₹{fmt(corpus)}</span></div>
          <input type="range" min="100000" max="100000000" step="100000" value={corpus} onChange={e => setCorpus(+e.target.value)} style={s.slider} />
          <div style={s.sliderLabels}><span>₹1L</span><span>₹10Cr</span></div>
        </div>

        <div style={s.section}>
          <label style={s.label}>Monthly Withdrawal (₹)</label>
          <input type="number" value={withdrawal} onChange={e => setWithdrawal(+e.target.value)} style={s.input} />
        </div>

        <div style={s.section}>
          <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Annual Step-up</span><span style={{ fontSize: 13 }}>{stepup}%</span></div>
          <input type="range" min="0" max="15" value={stepup} onChange={e => setStepup(+e.target.value)} style={s.slider} />
          <p style={s.hint}>Increase withdrawal annually to match inflation</p>
        </div>

        <div style={s.section}>
          <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Expected Return</span><span style={{ fontSize: 13 }}>{returns}%</span></div>
          <input type="range" min="5" max="15" value={returns} onChange={e => setReturns(+e.target.value)} style={s.slider} />
        </div>

        <div style={s.section}>
          <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Time Period</span><span style={{ fontSize: 13 }}>{years} Yrs</span></div>
          <input type="range" min="5" max="40" value={years} onChange={e => setYears(+e.target.value)} style={s.slider} />
        </div>

        {result && (
          <div style={s.summary}>
            <div style={s.summaryTitle}>SUMMARY</div>
            <div style={s.summaryRow}><span style={{ color: 'var(--text-muted)' }}>Total Withdrawn</span><span style={{ color: 'var(--accent)' }}>₹{fmt(result.total_withdrawn)}</span></div>
            <div style={s.summaryRow}><span style={{ color: 'var(--text-muted)' }}>Final Balance</span><span style={{ color: result.final_balance > 0 ? '#10b981' : '#ef4444' }}>₹{fmt(result.final_balance)}</span></div>
          </div>
        )}
      </div>

      <div>
        {result && (
          <>
            <div style={{ ...s.status, background: result.sustainable ? '#10b981' : '#ef4444' }}>
              <div style={s.statusTitle}>Plan Status: {result.sustainable ? 'Sustainable' : 'Unsustainable'}</div>
              <div style={s.statusValue}>Corpus safe for {result.safe_years} years</div>
              <p style={s.statusDesc}>
                {result.sustainable 
                  ? `Your portfolio continues to grow to ₹${fmt(result.final_balance)} whilst providing regular income.`
                  : `Your corpus will be exhausted after ${result.safe_years} years. Consider reducing withdrawal.`}
              </p>
            </div>

            <div style={s.card}>
              <div style={{ fontSize: 13, fontWeight: 500, margin: '0 0 16px 0' }}>CORPUS TRAJECTORY</div>
              <div style={{ height: 250, margin: 0, padding: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                    <YAxis tickFormatter={v => `₹${(v/100000).toFixed(0)}L`} tick={{ fontSize: 11 }} stroke="var(--text-muted)" />
                    <Tooltip formatter={v => `₹${fmt(v)}`} contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8 }} />
                    <Legend />
                    <Line type="monotone" dataKey="balance" name="Portfolio Balance" stroke="#10b981" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="withdrawn" name="Year Withdrawal" stroke="#6366f1" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
