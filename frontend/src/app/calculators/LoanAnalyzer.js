'use client';
import { useState, useEffect, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { api } from '../../lib/api';
import { Zap, Info, IndianRupee, TrendingDown, Percent, Calendar } from 'lucide-react';
import { C, card, label, slider, section, sCard, CalcStatus, fmt, useCompact } from './theme';

// Client-side amortization for chart visualization only.
// Strategy summary numbers (tenure/interest saved) come from the API.
function amortize(principal, annualRate, tenureYears, { extraEmisPerYear = 0, stepupPct = 0 } = {}) {
  const r = annualRate / 12 / 100;
  const n = tenureYears * 12;
  if (r === 0) return Array.from({ length: tenureYears }, (_, i) => principal * (1 - (i + 1) / tenureYears));
  const emi = principal * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
  let bal = principal, currentEmi = emi;
  const yearly = [];
  for (let yr = 1; yr <= tenureYears; yr++) {
    for (let m = 1; m <= 12; m++) {
      if (bal <= 0) { bal = 0; break; }
      bal = bal * (1 + r) - currentEmi;
      bal = Math.max(0, bal);
    }
    // Extra EMIs applied at year-end (matches API logic)
    if (extraEmisPerYear > 0) bal = Math.max(0, bal - currentEmi * extraEmisPerYear);
    yearly.push(Math.max(0, Math.round(bal)));
    if (stepupPct > 0) currentEmi *= (1 + stepupPct / 100);
  }
  return yearly;
}

export default function LoanAnalyzer() {
  const compact = useCompact();
  const [principal, setPrincipal] = useState(5000000);
  const [rate, setRate] = useState(8.5);
  const [tenure, setTenure] = useState(25);
  const [stepup, setStepup] = useState(7.5);
  const [extraEmis, setExtraEmis] = useState(1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/loan-analyzer?principal=${principal}&interest_rate=${rate}&tenure_years=${tenure}&stepup_pct=${stepup}&extra_emis=${extraEmis}`)
      .then(r => { setResult(r); setError(null); }).catch(e => setError(e.message));
  }, [principal, rate, tenure, stepup, extraEmis]);

  const chartData = useMemo(() => {
    const std = amortize(principal, rate, tenure);
    const extra = amortize(principal, rate, tenure, { extraEmisPerYear: extraEmis });
    const step = amortize(principal, rate, tenure, { stepupPct: stepup });
    const combo = amortize(principal, rate, tenure, { extraEmisPerYear: extraEmis, stepupPct: stepup });
    return Array.from({ length: tenure }, (_, i) => ({
      year: i + 1, standard: std[i], extraEmi: extra[i], stepUp: step[i], combo: combo[i]
    }));
  }, [principal, rate, tenure, stepup, extraEmis]);

  const yr1Total = result ? Math.round(result.standard_emi * 12) : 0;
  const yr1PrinPaid = chartData.length ? principal - chartData[0].standard : 0;
  const yr1 = { principal: yr1PrinPaid, interest: yr1Total - yr1PrinPaid };


  const inlineInput = (lbl, value, onChange, opts = {}) => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, margin: '0 0 8px 0' }}>
      <label style={{ fontSize: 14, fontWeight: 500, color: opts.color || 'var(--text-muted)', margin: 0 }}>{lbl}</label>
      <div style={{ position: 'relative', width: opts.wide ? 128 : 96 }}>
        {opts.prefix && <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', margin: 0 }}>{opts.prefix}</span>}
        <input type="number" value={value} onChange={onChange} step={opts.step}
          style={{ width: '100%', padding: '6px 8px', paddingLeft: opts.prefix ? 24 : 8, paddingRight: opts.suffix ? 24 : 8, textAlign: 'right', background: opts.bg || 'var(--bg-primary)', border: `1px solid ${opts.borderColor || 'var(--border)'}`, borderRadius: 8, fontSize: 14, fontWeight: 600, color: opts.inputColor || 'var(--text-primary)', outline: 'none', margin: 0 }} />
        {opts.suffix === '%' && <Percent style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', width: 12, height: 12, color: opts.suffixColor || 'var(--text-muted)', margin: 0 }} />}
        {opts.suffix === 'cal' && <Calendar style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', width: 12, height: 12, color: 'var(--text-muted)', margin: 0 }} />}
      </div>
    </div>
  );

  return (
    <div style={{ margin: 0, padding: 0 }}>
      <CalcStatus loading={!result && !error} error={error} />
      <style>{`
        @keyframes gradShift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
      `}</style>

      {/* Top: Banner + Reality Check */}
      <div style={{ display: 'grid', gridTemplateColumns: compact ? '1fr' : '2fr 1fr', gap: 24, marginBottom: 32 }}>
        {/* Banner */}
        <div style={{ background: 'linear-gradient(to right, #0f172a, #1e293b)', borderRadius: 24, padding: compact ? 24 : 32, color: '#fff', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: -64, right: -64, width: 256, height: 256, background: 'rgba(16,185,129,0.1)', borderRadius: '50%', filter: 'blur(48px)', pointerEvents: 'none' }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{ fontSize: compact ? 22 : 28, fontWeight: 700, margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: 12, color: '#fff' }}>
                  Smart Loan Repayment Analyzer <Zap style={{ width: 24, height: 24, color: '#facc15' }} />
                </h2>
                <p style={{ color: '#cbd5e1', fontSize: compact ? 14 : 18, margin: 0, maxWidth: 600, lineHeight: 1.5 }}>
                  Discover how small changes in your repayment strategy can save you{' '}
                  <span style={{ color: '#34d399', fontWeight: 700 }}>Lakhs</span>{' '}
                  in interest and cut years off your home loan.
                </p>
              </div>
              <button style={{ background: 'rgba(255,255,255,0.1)', border: 'none', padding: 8, borderRadius: '50%', cursor: 'pointer', margin: 0 }}>
                <Info style={{ width: 24, height: 24, color: '#34d399' }} />
              </button>
            </div>
          </div>
        </div>

        {/* Reality Check */}
        {result && (
          <div style={{ ...sCard, borderRadius: 24, padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <h4 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Calendar style={{ width: 16, height: 16 }} /> Year 1 Reality Check
            </h4>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 16px 0' }}>
              <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>Total Paid (Yr 1)</span>
              <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>₹{fmt(yr1Total)}</span>
            </div>
            <div style={{ height: 16, background: 'var(--bg-tertiary)', borderRadius: 9999, overflow: 'hidden', margin: '0 0 8px 0' }}>
              <div style={{ height: 16, background: '#f87171', borderRadius: 9999, width: `${yr1Total ? (yr1.interest / yr1Total * 100).toFixed(1) : 0}%` }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, margin: '0 0 16px 0' }}>
              <span style={{ color: '#ef4444' }}>Interest: ₹{fmt(yr1.interest)}</span>
              <span style={{ color: '#10b981' }}>Principal: ₹{fmt(yr1.principal)}</span>
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: 'auto 0 0 0', paddingTop: 16, lineHeight: 1.4 }}>Based on standard schedule. Prepayments drastically improve this ratio.</p>
          </div>
        )}
      </div>

      {/* Main: Loan Details + Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: compact ? '1fr' : '4fr 8fr', gap: 32 }}>
        <div>
          <div style={{ ...sCard, borderRadius: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
              <IndianRupee style={{ width: 20, height: 20, color: 'var(--accent)' }} /> Loan Details
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 24, margin: 0 }}>
              {inlineInput('Loan Amount', principal, e => setPrincipal(+e.target.value), { prefix: '₹', wide: true })}

              <div>
                {inlineInput('Interest Rate (%)', rate, e => setRate(+e.target.value), { step: 0.1, suffix: '%' })}
                <input type="range" aria-label="Interest Rate" min={1} max={20} step={0.1} value={rate} onChange={e => setRate(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)' }}><span>1%</span><span>20%</span></div>
              </div>

              <div>
                {inlineInput('Tenure (Years)', tenure, e => setTenure(+e.target.value), { suffix: 'cal' })}
                <input type="range" min={1} max={40} value={tenure} aria-label="Loan Tenure" onChange={e => setTenure(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)' }}><span>1y</span><span>40y</span></div>
              </div>

              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 24, margin: 0 }}>
                <div>
                  {inlineInput('Step-Up Annual Increase (%)', stepup, e => setStepup(+e.target.value), { step: 0.5, suffix: '%', color: '#059669', bg: 'rgba(16,185,129,0.06)', borderColor: 'rgba(16,185,129,0.2)', inputColor: '#059669', suffixColor: '#059669' })}
                  <input type="range" aria-label="Step-up Rate" min={0} max={50} step={0.5} value={stepup} onChange={e => setStepup(+e.target.value)} style={{ ...slider, accentColor: '#059669' }} />
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Used for Method 2 & 3</p>
                </div>

                <div style={{ marginTop: 24 }}>
                  {inlineInput('Extra EMIs per Year', extraEmis, e => setExtraEmis(+e.target.value), { color: '#2563eb', bg: 'rgba(59,130,246,0.06)', borderColor: 'rgba(59,130,246,0.2)', inputColor: '#2563eb' })}
                  <input type="range" aria-label="Extra EMIs per Year" min={0} max={6} value={extraEmis} onChange={e => setExtraEmis(+e.target.value)} style={{ ...slider, accentColor: '#2563eb' }} />
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Used for Method 1 & 3 (Default: 1 represents 13th month pay)</p>
                </div>
              </div>
            </div>

            {result && (
              <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)', borderRadius: 12, padding: 16, marginTop: 32 }}>
                <div style={{ fontSize: 14, color: '#6366f1', fontWeight: 500 }}>Standard Monthly EMI</div>
                <div style={{ fontSize: 30, fontWeight: 700, color: 'var(--text-primary)' }}>₹{fmt(result.standard_emi)}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Chart + Strategy */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {result && (
            <>
              <div style={{ ...sCard, borderRadius: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 24px 0', flexWrap: 'wrap', gap: 8 }}>
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Loan Balance Curve</h3>
                  <div style={{ display: 'flex', gap: 16, fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>
                    {[{ c: '#94a3b8', n: 'Standard' }, { c: '#3b82f6', n: 'Extra EMI' }, { c: '#a855f7', n: 'Step-Up' }, { c: '#10b981', n: 'Combo' }].map(l => (
                      <span key={l.n} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ width: 12, height: 12, borderRadius: '50%', background: l.c, display: 'inline-block' }} />{l.n}
                      </span>
                    ))}
                  </div>
                </div>
                <div style={{ height: compact ? 250 : 350 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                      <defs>
                        <linearGradient id="colorCombo" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.1} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
                      <XAxis dataKey="year" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} stroke="none" label={{ value: 'Years', position: 'insideBottom', offset: -10, style: { fontSize: 12, fill: 'var(--text-muted)' } }} />
                      <YAxis tickFormatter={v => `${(v / 100000).toFixed(0)}`} tick={{ fontSize: 12, fill: 'var(--text-muted)' }} stroke="none" label={{ value: 'Balance (₹ Lakhs)', angle: -90, position: 'insideLeft', offset: 5, style: { fontSize: 12, fill: 'var(--text-muted)' } }} />
                      <Tooltip formatter={v => `₹${fmt(Math.round(v))}`} contentStyle={{ background: 'var(--bg-secondary)', border: 'none', borderRadius: 12, boxShadow: '0 10px 15px rgba(0,0,0,0.1)', color: 'var(--text-primary)' }} />
                      <Area type="monotone" dataKey="standard" name="Standard" stroke="#94a3b8" strokeWidth={2} fill="transparent" animationDuration={800} />
                      <Area type="monotone" dataKey="extraEmi" name="Extra EMI" stroke="#3b82f6" strokeWidth={2} fill="transparent" animationDuration={1000} />
                      <Area type="monotone" dataKey="stepUp" name="Step-Up" stroke="#a855f7" strokeWidth={2} fill="transparent" animationDuration={1200} />
                      <Area type="monotone" dataKey="combo" name="Super Combo" stroke="#10b981" strokeWidth={3} fill="url(#colorCombo)" fillOpacity={0.6} animationDuration={1400} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Strategy Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: compact ? '1fr' : '1fr 1fr 1fr', gap: 16 }}>
                <StrategyCard title={`${extraEmis} Extra EMI/Yr`} Icon={IndianRupee} iconColor="#2563eb" valColor="#2563eb" tenure={result.strategies.extra_emi.tenure_saved} interest={result.strategies.extra_emi.interest_saved} />
                <StrategyCard title={`Step-Up (${stepup}%)`} Icon={TrendingDown} iconColor="#9333ea" valColor="#9333ea" tenure={result.strategies.stepup.tenure_saved} interest={result.strategies.stepup.interest_saved} />
                <StrategyCard title="Super Combo" Icon={Zap} combo tenure={result.strategies.combo.tenure_saved} interest={result.strategies.combo.interest_saved} />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{ ...sCard, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 28, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ width: 28, height: 28, borderRadius: '50%', background: 'rgba(16,185,129,0.12)', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, margin: 0 }}>✓</span>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            <strong style={{ color: 'var(--text-primary)' }}>Verified Methodology</strong> · Calculations tested against official standards: <span style={{ color: 'var(--accent)', textDecoration: 'underline', cursor: 'pointer' }}>Reducing Balance Method (RBI Guidelines)</span>.
          </span>
        </div>
        <span style={{ fontSize: 11, fontWeight: 600, color: '#10b981', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 6, padding: '4px 10px', margin: 0, whiteSpace: 'nowrap' }}>📋 UPDATED: FY 2026-27 (INTERIM BUDGET)</span>
      </div>
    </div>
  );
}

function StrategyCard({ title: t, Icon, iconColor, valColor, tenure, interest, combo }) {

  if (combo) return (
    <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 20, margin: 0, boxShadow: '0 10px 15px rgba(0,0,0,0.1)', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 12, right: 12, opacity: 0.2 }}><Zap style={{ width: 64, height: 64, color: '#facc15' }} /></div>
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom right, rgba(99,102,241,0.1), rgba(168,85,247,0.1))', pointerEvents: 'none' }} />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <h3 style={{ fontWeight: 700, color: '#fff', margin: '0 0 4px 0', display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>{t} <Zap style={{ width: 16, height: 16, color: '#facc15' }} /></h3>
        <div style={{ fontSize: 24, fontWeight: 700, color: '#34d399', margin: '0 0 4px 0' }}>{tenure}</div>
        <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Tenure Saved</div>
        <div style={{ borderTop: '1px solid #1e293b', paddingTop: 16, marginTop: 16 }}>
          <div style={{ fontSize: 14, color: '#94a3b8' }}>Interest Saved</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>₹{fmt(interest)}</div>
        </div>
      </div>
    </div>
  );

  return (
    <div style={{ ...sCard, position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 12, right: 12, opacity: 0.1 }}><Icon style={{ width: 64, height: 64, color: iconColor }} /></div>
      <div style={{ position: 'relative', zIndex: 1 }}>
        <h3 style={{ fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px 0', fontSize: 14 }}>{t}</h3>
        <div style={{ fontSize: 24, fontWeight: 700, color: valColor, margin: '0 0 4px 0' }}>{tenure}</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Tenure Saved</div>
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 16 }}>
          <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>Interest Saved</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>₹{fmt(interest)}</div>
        </div>
      </div>
    </div>
  );
}
