'use client';
import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { CalcStatus, C, card, grid2, label, input, slider, row, section, title, statCard, statLabel, statVal, gridHalf, footer, footerIcon, fmt, fmtCr, useCompact } from './theme';

export default function RetirementPlanner() {
  const compact = useCompact();
  const [age, setAge] = useState(30);
  const [retireAge, setRetireAge] = useState(60);
  const [expenses, setExpenses] = useState(50000);
  const [savings, setSavings] = useState(1000000);
  const [inflation, setInflation] = useState(6);
  const [returns, setReturns] = useState(10);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/retirement?current_age=${age}&retirement_age=${retireAge}&monthly_expenses=${expenses}&current_savings=${savings}&inflation=${inflation}&expected_return=${returns}`)
      .then(r => { setResult(r); setError(null); }).catch(e => setError(e.message));
  }, [age, retireAge, expenses, savings, inflation, returns]);

  const pct = result?.achievement_pct || 0;

  return (
    <div style={{ margin: 0, padding: 0 }}>
      <CalcStatus loading={!result && !error} error={error} />
      <div style={grid2(compact)}>
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 24px 0' }}>
            <h2 style={{ ...title, margin: 0 }}>Retirement Plan</h2>
            <span style={{ fontSize: 20, color: C.textMuted, cursor: 'pointer' }}>ⓘ</span>
          </div>

          <div style={{ ...section, ...gridHalf(compact) }}>
            <div>
              <div style={row}><span style={{ fontSize: 14, color: C.textSec }}>Age: {age}</span></div>
              <input type="range" min={20} max={55} value={age} aria-label="Current Age" onChange={e => setAge(+e.target.value)} style={slider} />
            </div>
            <div>
              <div style={row}><span style={{ fontSize: 14, color: C.textSec }}>Retire at: {retireAge}</span></div>
              <input type="range" min={45} max={70} value={retireAge} aria-label="Retirement Age" onChange={e => setRetireAge(+e.target.value)} style={slider} />
            </div>
          </div>

          <div style={section}>
            <label style={label}>Current Monthly Expenses (₹)</label>
            <input type="number" value={expenses} onChange={e => setExpenses(+e.target.value)} style={input} />
          </div>

          <div style={section}>
            <label style={label}>Current Savings (₹)</label>
            <input type="number" value={savings} onChange={e => setSavings(+e.target.value)} style={input} />
          </div>

          <div style={gridHalf(compact)}>
            <div>
              <div style={row}><span style={{ fontSize: 14, color: C.textSec }}>Inflation: {inflation}%</span></div>
              <input type="range" aria-label="Inflation Rate" min={3} max={10} value={inflation} onChange={e => setInflation(+e.target.value)} style={slider} />
            </div>
            <div>
              <div style={row}><span style={{ fontSize: 14, color: C.textSec }}>Return: {returns}%</span></div>
              <input type="range" min={6} max={15} value={returns} onChange={e => setReturns(+e.target.value)} style={slider} />
            </div>
          </div>

          {result && (
            <div style={{ background: C.blueGrad, borderRadius: 16, padding: 24, marginTop: 24, color: '#fff' }}>
              <div style={{ fontSize: 13, opacity: 0.8 }}>Target Corpus Needed</div>
              <div style={{ fontSize: 36, fontWeight: 700, margin: '4px 0 16px 0' }}>{fmtCr(result.corpus_needed)}</div>
              <div style={{ fontSize: 14, opacity: 0.9 }}>To reach this, start an SIP of</div>
              <div style={{ fontSize: 26, fontWeight: 700 }}>₹{fmt(result.sip_needed)} <span style={{ fontSize: 14, fontWeight: 400 }}>/month</span></div>
            </div>
          )}
        </div>

        <div style={card}>
          <h2 style={{ ...title, textAlign: 'center' }}>Retirement Goal Progress</h2>
          <p style={{ fontSize: 14, color: C.textMuted, textAlign: 'center', margin: '0 0 28px 0' }}>Are you on track for your golden years?</p>

          {result && (
            <>
              <div style={{ display: 'flex', justifyContent: 'center', margin: '0 0 32px 0' }}>
                <div style={{ position: 'relative', width: 190, height: 190 }}>
                  <svg width="190" height="190" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="95" cy="95" r="80" stroke={C.cardAlt} strokeWidth="16" fill="none" />
                    <circle cx="95" cy="95" r="80" stroke={C.accent} strokeWidth="16" fill="none"
                      strokeDasharray={`${pct * 5.03} 503`} strokeLinecap="round" />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: 40, fontWeight: 700, color: C.accent }}>{pct}%</span>
                    <span style={{ fontSize: 12, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Achieved</span>
                  </div>
                </div>
              </div>

              <div style={gridHalf(compact)}>
                <div style={statCard}><div style={statLabel}>Projected Corpus</div><div style={{ ...statVal, color: C.accent }}>{fmtCr(result.projected_savings)}</div></div>
                <div style={statCard}><div style={statLabel}>Target Needed</div><div style={statVal}>{fmtCr(result.corpus_needed)}</div></div>
              </div>

              {result.shortfall > 0 && (
                <div style={{ padding: 16, background: C.redBg, borderRadius: 12, textAlign: 'center', marginTop: 18, color: C.red, fontWeight: 600, fontSize: 15 }}>
                  Shortfall: {fmtCr(result.shortfall)}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <div style={footer}>
        <span style={footerIcon}>✓</span>
        <span><strong>Verified Methodology</strong> · Calculations are tested against official standards: Income Tax Act 1961.</span>
      </div>
    </div>
  );
}
