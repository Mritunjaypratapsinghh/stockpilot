'use client';
import { useState, useEffect } from 'react';
import { api } from '../../lib/api';

const fmt = n => n?.toLocaleString('en-IN') || '0';
const fmtCr = n => n >= 10000000 ? `₹${(n / 10000000).toFixed(1)}Cr` : `₹${fmt(n)}`;

const s = {
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 1000, margin: '0 auto', padding: 0 },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  title: { fontSize: 18, fontWeight: 600, margin: '0 0 24px 0', padding: 0 },
  label: { fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 8px 0', padding: 0, display: 'block' },
  input: { width: '100%', padding: '12px 16px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 14, color: 'var(--text-primary)' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 8px 0', padding: 0 },
  slider: { width: '100%', height: 6, margin: '8px 0', padding: 0, accentColor: 'var(--accent)' },
  section: { margin: '0 0 20px 0', padding: 0 },
  gridHalf: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, margin: 0, padding: 0 },
  cta: { background: 'var(--accent)', borderRadius: 12, padding: 20, margin: '24px 0 0 0', color: '#fff' },
  ctaLabel: { fontSize: 12, opacity: 0.8, margin: '0 0 4px 0', padding: 0 },
  ctaValue: { fontSize: 28, fontWeight: 700, margin: '0 0 12px 0', padding: 0 },
  statCard: { background: 'var(--bg-tertiary)', borderRadius: 8, padding: 12, margin: 0 },
  statLabel: { fontSize: 11, color: 'var(--text-muted)', margin: '0 0 4px 0', padding: 0 },
  statValue: { fontSize: 18, fontWeight: 600, margin: 0, padding: 0 },
  shortfall: { padding: 12, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, textAlign: 'center', margin: '16px 0 0 0', color: '#ef4444', fontWeight: 500 },
};

export default function RetirementPlanner() {
  const [age, setAge] = useState(30);
  const [retireAge, setRetireAge] = useState(60);
  const [expenses, setExpenses] = useState(50000);
  const [savings, setSavings] = useState(1000000);
  const [inflation, setInflation] = useState(6);
  const [returns, setReturns] = useState(10);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/retirement?current_age=${age}&retirement_age=${retireAge}&monthly_expenses=${expenses}&current_savings=${savings}&inflation=${inflation}&expected_return=${returns}`)
      .then(setResult).catch(console.error);
  }, [age, retireAge, expenses, savings, inflation, returns]);

  return (
    <div style={s.grid}>
      <div style={s.card}>
        <h2 style={s.title}>Retirement Plan</h2>
        
        <div style={s.section}>
          <div style={s.gridHalf}>
            <div>
              <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Age</span><span style={{ fontSize: 13, fontWeight: 500 }}>{age}</span></div>
              <input type="range" min="20" max="55" value={age} onChange={e => setAge(+e.target.value)} style={s.slider} />
            </div>
            <div>
              <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Retire at</span><span style={{ fontSize: 13, fontWeight: 500 }}>{retireAge}</span></div>
              <input type="range" min="45" max="70" value={retireAge} onChange={e => setRetireAge(+e.target.value)} style={s.slider} />
            </div>
          </div>
        </div>

        <div style={s.section}>
          <label style={s.label}>Current Monthly Expenses (₹)</label>
          <input type="number" value={expenses} onChange={e => setExpenses(+e.target.value)} style={s.input} />
        </div>

        <div style={s.section}>
          <label style={s.label}>Current Savings (₹)</label>
          <input type="number" value={savings} onChange={e => setSavings(+e.target.value)} style={s.input} />
        </div>

        <div style={s.gridHalf}>
          <div>
            <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Inflation</span><span style={{ fontSize: 13, fontWeight: 500 }}>{inflation}%</span></div>
            <input type="range" min="3" max="10" value={inflation} onChange={e => setInflation(+e.target.value)} style={s.slider} />
          </div>
          <div>
            <div style={s.row}><span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Return</span><span style={{ fontSize: 13, fontWeight: 500 }}>{returns}%</span></div>
            <input type="range" min="6" max="15" value={returns} onChange={e => setReturns(+e.target.value)} style={s.slider} />
          </div>
        </div>

        {result && (
          <div style={s.cta}>
            <div style={s.ctaLabel}>Target Corpus Needed</div>
            <div style={s.ctaValue}>{fmtCr(result.corpus_needed)}</div>
            <div style={{ fontSize: 13 }}>To reach this, start an SIP of</div>
            <div style={{ fontSize: 22, fontWeight: 600 }}>₹{fmt(result.sip_needed)}<span style={{ fontSize: 13, fontWeight: 400 }}>/month</span></div>
          </div>
        )}
      </div>

      <div style={s.card}>
        <h2 style={s.title}>Retirement Goal Progress</h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '0 0 24px 0' }}>Are you on track for your golden years?</p>

        {result && (
          <>
            <div style={{ display: 'flex', justifyContent: 'center', margin: '0 0 24px 0' }}>
              <div style={{ position: 'relative', width: 160, height: 160 }}>
                <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
                  <circle cx="80" cy="80" r="70" stroke="var(--bg-tertiary)" strokeWidth="12" fill="none" />
                  <circle cx="80" cy="80" r="70" stroke="var(--accent)" strokeWidth="12" fill="none"
                    strokeDasharray={`${result.achievement_pct * 4.4} 440`} strokeLinecap="round" />
                </svg>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: 32, fontWeight: 700, color: 'var(--accent)' }}>{result.achievement_pct}%</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>ACHIEVED</span>
                </div>
              </div>
            </div>

            <div style={s.gridHalf}>
              <div style={s.statCard}>
                <div style={s.statLabel}>Projected Corpus</div>
                <div style={s.statValue}>{fmtCr(result.projected_savings)}</div>
              </div>
              <div style={s.statCard}>
                <div style={s.statLabel}>Target Needed</div>
                <div style={s.statValue}>{fmtCr(result.corpus_needed)}</div>
              </div>
            </div>

            {result.shortfall > 0 && (
              <div style={s.shortfall}>Shortfall: {fmtCr(result.shortfall)}</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
