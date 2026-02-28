'use client';
import { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { api } from '../../lib/api';
import { CircleArrowDown, Info, TrendingUp, Activity, ShieldCheck, BookOpen } from 'lucide-react';
import { C, slider, sCard, pill, inputBox, suffixBox, CalcStatus, fmt, useCompact } from './theme';

export default function SWPCalculator() {
  const compact = useCompact();
  const [corpus, setCorpus] = useState(5000000);
  const [withdrawal, setWithdrawal] = useState(30000);
  const [stepup, setStepup] = useState(0);
  const [returns, setReturns] = useState(10);
  const [years, setYears] = useState(20);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/swp?corpus=${corpus}&monthly_withdrawal=${withdrawal}&annual_stepup=${stepup}&expected_return=${returns}&years=${years}`)
      .then(r => { setResult(r); setError(null); }).catch(e => setError(e.message));
  }, [corpus, withdrawal, stepup, returns, years]);

  const chartData = result?.trajectory.map(t => ({ year: `${t.year}y`, balance: t.end_balance, withdrawn: t.withdrawn })) || [];


  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 48, margin: 0, padding: 0 }}>
      <CalcStatus loading={!result && !error} error={error} />
      <div style={{ display: 'grid', gridTemplateColumns: compact ? '1fr' : '1fr 1fr', gap: 32 }}>
        {/* Left — Configuration */}
        <div style={{ ...sCard, display: 'flex', flexDirection: 'column', overflow: 'visible' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <div style={{ padding: 12, background: 'rgba(239,68,68,0.1)', borderRadius: 12, color: '#ef4444', display: 'flex' }}>
              <CircleArrowDown style={{ width: 24, height: 24 }} />
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>SWP Configuration</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500, margin: 0 }}>Plan your regular income with inflation</p>
            </div>
            <button style={{ color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, margin: 0 }}>
              <Info style={{ width: 20, height: 20 }} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Total Investment */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', margin: 0 }}>Total Investment</label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 12, fontWeight: 700 }}>₹</span>
                  <input type="number" value={corpus} onChange={e => setCorpus(+e.target.value)} style={inputBox()} />
                </div>
              </div>
              <input type="range" aria-label="Total Investment" min={100000} max={100000000} step={50000} value={corpus} onChange={e => setCorpus(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}><span style={pill}>₹ 1L</span><span style={{ ...pill, marginLeft: 'auto' }}>₹ 10Cr</span></div>
            </div>

            {/* Monthly Withdrawal */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', margin: 0 }}>Monthly Withdrawal</label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 12, fontWeight: 700 }}>₹</span>
                  <input type="number" value={withdrawal} onChange={e => setWithdrawal(+e.target.value)} style={inputBox()} />
                </div>
              </div>
              <input type="range" aria-label="Monthly Withdrawal" min={1000} max={500000} step={500} value={withdrawal} onChange={e => setWithdrawal(+e.target.value)} style={{ ...slider, accentColor: '#ef4444' }} />
            </div>

            {/* Annual Step-up */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <TrendingUp style={{ width: 14, height: 14, color: 'var(--accent)' }} /> Annual Step-up
                </label>
                <div style={{ position: 'relative' }}>
                  <input type="number" value={stepup} onChange={e => setStepup(+e.target.value)} style={suffixBox()} />
                  <span style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 12, fontWeight: 700 }}>%</span>
                </div>
              </div>
              <input type="range" aria-label="Step-up Rate" min={0} max={20} step={1} value={stepup} onChange={e => setStepup(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
              <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '8px 0 0 0' }}>Increase withdrawal annually to match inflation.</p>
            </div>

            {/* Expected Return */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', margin: 0 }}>Expected Return</label>
                <div style={{ position: 'relative' }}>
                  <input type="number" value={returns} onChange={e => setReturns(+e.target.value)} style={suffixBox()} />
                  <span style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 12, fontWeight: 700 }}>%</span>
                </div>
              </div>
              <input type="range" min={1} max={30} step={0.5} value={returns} onChange={e => setReturns(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
            </div>

            {/* Time Period */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', margin: 0 }}>Time Period</label>
                <div style={{ position: 'relative' }}>
                  <input type="number" value={years} onChange={e => setYears(+e.target.value)} style={suffixBox()} />
                  <span style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 12, fontWeight: 700 }}>Yrs</span>
                </div>
              </div>
              <input type="range" min={1} max={50} step={1} value={years} onChange={e => setYears(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
            </div>
          </div>

          {/* Summary */}
          {result && (
            <div style={{ marginTop: 32, padding: 16, background: 'var(--bg-tertiary)', borderRadius: 12, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>Summary</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>Total Withdrawn</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#dc2626' }}>₹ {fmt(result.total_withdrawn)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>Final Balance</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#059669' }}>₹ {fmt(result.final_balance)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Right — Status + Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {result && (
            <>
              {/* Status Banner */}
              <div style={{ padding: 24, borderRadius: 16, boxShadow: '0 10px 15px rgba(0,0,0,0.1)', position: 'relative', overflow: 'hidden', color: '#fff', background: result.sustainable ? '#059669' : '#dc2626' }}>
                <div style={{ position: 'absolute', top: 0, right: 0, padding: 32, opacity: 0.1 }}>
                  <Activity style={{ width: 120, height: 120 }} />
                </div>
                <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 14, fontWeight: 500, margin: '0 0 4px 0', textTransform: 'capitalize' }}>Plan Status: {result.sustainable ? 'Sustainable' : 'Unsustainable'}</p>
                <h2 style={{ fontSize: 30, fontWeight: 700, margin: '0 0 8px 0' }}>Corpus safe for {result.safe_years} years</h2>
                <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: 14, opacity: 0.8, maxWidth: 384, margin: 0, lineHeight: 1.5 }}>
                  {result.sustainable
                    ? `Your portfolio continues to grow to ₹ ${fmt(result.final_balance)} whilst providing regular income.`
                    : `Your corpus will be exhausted after ${result.safe_years} years. Consider reducing withdrawal.`}
                </p>
              </div>

              {/* Chart */}
              <div style={{ ...sCard, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 300 }}>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'center', margin: '0 0 16px 0' }}>Corpus Trajectory</h4>
                <div style={{ flex: 1, minHeight: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10B981" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorWithdrawn" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#9CA3AF' }} stroke="none" />
                      <YAxis tickFormatter={v => `₹${Math.round(v / 100000)}L`} tick={{ fontSize: 10, fill: '#9CA3AF' }} stroke="none" />
                      <Tooltip formatter={v => `₹${fmt(v)}`} contentStyle={{ background: 'rgba(255,255,255,0.9)', border: 'none', borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', color: '#000' }} />
                      <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                      <Area type="monotone" dataKey="withdrawn" name="Cumulative Withdrawal" stroke="#F59E0B" strokeWidth={2} strokeDasharray="4 4" fill="url(#colorWithdrawn)" />
                      <Area type="monotone" dataKey="balance" name="Portfolio Balance" stroke="#10B981" strokeWidth={2} fill="url(#colorBalance)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{ marginTop: 48, padding: 24, background: 'rgba(59,130,246,0.03)', borderRadius: 16, border: '1px solid rgba(59,130,246,0.1)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', flexDirection: compact ? 'column' : 'row', alignItems: compact ? 'flex-start' : 'center', justifyContent: 'space-between', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <ShieldCheck style={{ width: 20, height: 20, color: '#2563eb', flexShrink: 0, marginTop: 2 }} />
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Verified Methodology</h4>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Calculations are tested against official standards: <span style={{ fontWeight: 500, color: '#2563eb' }}>Income Tax Act 1961</span>.</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--border)', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', flexShrink: 0 }}>
              <BookOpen style={{ width: 14, height: 14, color: '#16a34a' }} />
              <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Updated: FY 2026-27 (Interim Budget)</span>
            </div>
          </div>
          <div style={{ paddingTop: 16, borderTop: '1px solid rgba(59,130,246,0.1)' }}>
            <p style={{ fontSize: 10, color: 'var(--text-muted)', margin: 0, textAlign: compact ? 'left' : 'left' }}>Financial research led by <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Soumya Ranjan Dash</span>, Certified Financial Researcher.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
