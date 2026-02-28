'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { api } from '../../lib/api';
import { Info, ChevronDown, ChevronUp, ChartPie, TrendingUp, ShieldCheck, BookOpen } from 'lucide-react';
import { C, slider, sCard, CalcStatus, fmt, useCompact } from './theme';

export default function SIPStepup() {
  const compact = useCompact();
  const [amount, setAmount] = useState(10000);
  const [returns, setReturns] = useState(12);
  const [years, setYears] = useState(10);
  const [stepup, setStepup] = useState(10);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [chartView, setChartView] = useState('donut');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/sip-stepup?monthly_amount=${amount}&expected_return=${returns}&years=${years}&annual_stepup=${stepup}`)
      .then(r => { setResult(r); setError(null); }).catch(e => setError(e.message));
  }, [amount, returns, years, stepup]);

  const pieData = result ? [
    { name: 'Invested', value: result.stepup.total_invested },
    { name: 'Wealth Gained', value: result.stepup.wealth_gained },
  ] : [];

  const areaData = result?.yearly_breakdown?.map(r => {
    // Compound growth: each year's invested amount grows at monthly rate for remaining months
    const monthlyRate = returns / 100 / 12;
    let value = 0;
    let sip = amount;
    for (let y = 1; y <= r.year; y++) {
      const monthsLeft = (r.year - y) * 12;
      for (let m = 0; m < 12; m++) value += sip * Math.pow(1 + monthlyRate, monthsLeft + (12 - m));
      sip *= (1 + stepup / 100);
    }
    return { year: `Y${r.year}`, invested: r.cumulative_invested, value: Math.round(value) };
  }) || [];

  const iconToggle = (active) => ({
    padding: 6, borderRadius: 6, border: 'none', cursor: 'pointer', transition: 'all 0.15s', margin: 0,
    background: active ? 'var(--bg-secondary)' : 'transparent', color: active ? 'var(--text-primary)' : 'var(--text-muted)',
    boxShadow: active ? '0 1px 2px rgba(0,0,0,0.08)' : 'none', display: 'flex',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 48, margin: 0, padding: 0 }}>
      <CalcStatus loading={!result && !error} error={error} />
      <div style={{ display: 'flex', flexDirection: compact ? 'column-reverse' : 'row', gap: 32, alignItems: 'flex-start' }}>
        {/* Left — Configuration */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 24, width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>SIP Configuration</h3>
            <button style={{ color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, margin: 0 }}>
              <Info style={{ width: 20, height: 20 }} />
            </button>
          </div>

          {/* Monthly Investment */}
          <div>
            <label style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 8 }}>Monthly Investment (₹)</label>
            <input type="number" value={amount} onChange={e => setAmount(+e.target.value)} style={{ width: '100%', padding: '8px 16px', borderRadius: 8, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 14, outline: 'none', margin: 0 }} />
          </div>

          {/* Expected Return */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-muted)', margin: 0 }}>Expected Return: {returns}%</label>
            </div>
            <input type="range" aria-label="Expected Return" min={5} max={20} value={returns} onChange={e => setReturns(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
          </div>

          {/* Time Period */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-muted)', margin: 0 }}>Time Period: {years} Years</label>
            </div>
            <input type="range" aria-label="Time Period" min={1} max={30} value={years} onChange={e => setYears(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
          </div>

          {/* Annual Step-up */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-muted)', margin: 0 }}>Annual Step-up: {stepup}%</label>
            </div>
            <input type="range" aria-label="Step-up Rate" min={0} max={20} value={stepup} onChange={e => setStepup(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
          </div>

          {/* Breakdown Toggle */}
          <div style={{ paddingTop: 16 }}>
            <button onClick={() => setShowBreakdown(!showBreakdown)} style={{
              width: '100%', padding: '10px 16px', borderRadius: 12, border: '2px solid var(--accent)',
              background: 'transparent', color: 'var(--accent)', fontSize: 16, fontWeight: 500, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, margin: 0, transition: 'all 0.2s',
            }}>
              {showBreakdown ? 'Hide' : 'View'} Yearly Breakdown
              {showBreakdown ? <ChevronUp style={{ width: 16, height: 16 }} /> : <ChevronDown style={{ width: 16, height: 16 }} />}
            </button>
          </div>

        </div>

        {/* Right — Chart + Stats */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 24, width: '100%' }}>
          {/* Chart Toggle */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginBottom: 16 }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: 4, borderRadius: 8, display: 'flex', gap: 4 }}>
              <button onClick={() => setChartView('donut')} style={iconToggle(chartView === 'donut')} title="Donut Chart">
                <ChartPie style={{ width: 16, height: 16 }} />
              </button>
              <button onClick={() => setChartView('growth')} style={iconToggle(chartView === 'growth')} title="Growth Graph">
                <TrendingUp style={{ width: 16, height: 16 }} />
              </button>
            </div>
          </div>

          {/* Chart */}
          <div style={{ height: 400, width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
            {result && chartView === 'donut' && (
              <>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius="36%" outerRadius="50%" dataKey="value" stroke="var(--bg-secondary)" strokeWidth={2}>
                      <Cell fill="#0A2540" />
                      <Cell fill="#00D4FF" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none', width: 140 }}>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', margin: '0 0 4px 0' }}>Total Value</p>
                  <p style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0, lineHeight: 1.2, wordBreak: 'break-all' }}>₹{fmt(result.stepup.corpus)}</p>
                </div>
              </>
            )}
            {result && chartView === 'growth' && (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={areaData}>
                  <defs>
                    <linearGradient id="colorInvested" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0A2540" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0A2540" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#9CA3AF' }} stroke="none" />
                  <YAxis tickFormatter={v => `₹${Math.round(v / 100000)}L`} tick={{ fontSize: 10, fill: '#9CA3AF' }} stroke="none" />
                  <Tooltip formatter={v => `₹${fmt(Math.round(v))}`} contentStyle={{ background: 'rgba(255,255,255,0.9)', border: 'none', borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Area type="monotone" dataKey="invested" name="Total Invested" stroke="#0A2540" strokeWidth={2} fill="url(#colorInvested)" />
                  <Area type="monotone" dataKey="value" name="Portfolio Value" stroke="#00D4FF" strokeWidth={2} fill="url(#colorValue)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Stats */}
          {result && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div style={{ padding: 16, background: 'var(--bg-tertiary)', borderRadius: 12 }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 4px 0' }}>Total Invested</p>
                  <p style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0, wordBreak: 'break-all', lineHeight: 1.3 }}>₹{fmt(result.stepup.total_invested)}</p>
                </div>
                <div style={{ padding: 16, background: 'rgba(34,197,94,0.1)', borderRadius: 12 }}>
                  <p style={{ color: '#16a34a', fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 4px 0' }}>Wealth Gained</p>
                  <p style={{ fontSize: 18, fontWeight: 700, color: '#15803d', margin: 0, wordBreak: 'break-all', lineHeight: 1.3 }}>₹{fmt(result.stepup.wealth_gained)}</p>
                </div>
              </div>

              {/* Maturity Value */}
              <div style={{ padding: 16, background: 'rgba(59,130,246,0.1)', borderRadius: 12, border: '1px solid rgba(59,130,246,0.15)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <p style={{ fontSize: 14, color: 'var(--accent)', margin: 0 }}>Maturity Value</p>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>Last Monthly SIP</p>
                    <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>₹{fmt(result.stepup.last_monthly_sip)}</p>
                  </div>
                </div>
                <span style={{ fontSize: 24, fontWeight: 700, color: 'var(--accent)', wordBreak: 'break-all', display: 'block' }}>₹{fmt(result.stepup.corpus)}</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Yearly Breakdown */}
      {showBreakdown && result && (
        <div style={{ background: 'var(--bg-secondary)', borderRadius: 16, border: '1px solid var(--border)', overflow: 'hidden' }}>
          <div style={{ padding: 16, borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Yearly Breakdown</h3>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: 'var(--bg-tertiary)', color: 'var(--text-muted)', fontSize: 12, textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left' }}>Year</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Monthly SIP</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Year Invested</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Cumulative</th>
                </tr>
              </thead>
              <tbody>{result.yearly_breakdown.map(r => (
                <tr key={r.year} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '10px 16px', color: 'var(--text-primary)', fontWeight: 500 }}>{r.year}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'right', color: 'var(--text-muted)', fontFamily: 'monospace' }}>₹{fmt(r.monthly_sip)}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'right', color: 'var(--text-muted)', fontFamily: 'monospace' }}>₹{fmt(r.year_invested)}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'right', color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'monospace' }}>₹{fmt(r.cumulative_invested)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{ padding: 24, background: 'rgba(59,130,246,0.03)', borderRadius: 16, border: '1px solid rgba(59,130,246,0.1)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', flexDirection: compact ? 'column' : 'row', alignItems: compact ? 'flex-start' : 'center', justifyContent: 'space-between', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <ShieldCheck style={{ width: 20, height: 20, color: '#2563eb', flexShrink: 0, marginTop: 2 }} />
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Verified Methodology</h4>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Calculations are tested against official standards: <span style={{ fontWeight: 500, color: '#2563eb' }}>Compound Interest Formula (CAGR)</span>.</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--border)', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', flexShrink: 0 }}>
              <BookOpen style={{ width: 14, height: 14, color: '#16a34a' }} />
              <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Updated: FY 2026-27 (Interim Budget)</span>
            </div>
          </div>
          <div style={{ paddingTop: 16, borderTop: '1px solid rgba(59,130,246,0.1)' }}>
          </div>
        </div>
      </div>
    </div>
  );
}
