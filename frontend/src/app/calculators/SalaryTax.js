'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { api } from '../../lib/api';
import { Banknote, IndianRupee, ShieldCheck, Info, TrendingUp } from 'lucide-react';
import { C, card, slider, sCard, togBtn, CalcStatus, fmt, useCompact } from './theme';

const COLORS = ['#10b981', '#ef4444', '#f59e0b', '#6366f1'];

export default function SalaryTax() {
  const compact = useCompact();
  const [ctc, setCtc] = useState(1200000);
  const [pfType, setPfType] = useState('capped');
  const [regime, setRegime] = useState('new');
  const [intl, setIntl] = useState(false);
  const [vpf, setVpf] = useState(0);
  const [vpfMode, setVpfMode] = useState('amount');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/salary-tax?annual_ctc=${ctc}&pf_type=${pfType}&regime=${regime}&vpf=${vpf}`)
      .then(r => { setResult(r); setError(null); }).catch(e => setError(e.message));
  }, [ctc, pfType, regime, vpf]);

  const chartData = result ? [
    { name: 'Take Home', value: result.annual_inhand },
    { name: 'Income Tax', value: result.annual_tax },
    { name: 'PF & VPF', value: result.breakdown.employee_pf },
    { name: 'Other Deductions', value: result.breakdown.professional_tax + result.breakdown.gratuity },
  ] : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, margin: 0, padding: 0 }}>
      <CalcStatus loading={!result && !error} error={error} />
      {/* Header */}
      <div style={{ display: 'flex', flexDirection: compact ? 'column' : 'row', justifyContent: 'space-between', alignItems: compact ? 'flex-start' : 'center', gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px 0', display: 'flex', alignItems: 'center', gap: 12 }}>
            <Banknote style={{ width: 32, height: 32, color: 'var(--accent)' }} />
            Salary & Tax Calculator
            <span style={{ fontSize: 12, background: 'rgba(99,102,241,0.1)', color: 'var(--accent)', padding: '4px 10px', borderRadius: 9999, border: '1px solid rgba(99,102,241,0.2)', fontWeight: 500 }}>FY 26-27</span>
          </h2>
          <p style={{ fontSize: 14, color: 'var(--text-muted)', margin: 0 }}>Calculate your In-Hand Salary and compare New vs. Old Regime tax liability.</p>
        </div>
        <button style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 500, color: 'var(--accent)', background: 'rgba(99,102,241,0.05)', padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer', margin: 0 }}>
          <Info style={{ width: 16, height: 16 }} /> How it works
        </button>
      </div>

      {/* Main Grid: 7/5 */}
      <div style={{ display: 'grid', gridTemplateColumns: compact ? '1fr' : '7fr 5fr', gap: 32 }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Annual CTC */}
          <div style={sCard}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 16px 0' }}>
              <label style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                <IndianRupee style={{ width: 20, height: 20, color: 'var(--accent)' }} /> Annual CTC
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'var(--bg-tertiary)', borderRadius: 8, padding: '4px 12px', border: '1px solid var(--border)', margin: 0 }}>
                <span style={{ color: 'var(--text-muted)', fontWeight: 700 }}>₹</span>
                <input type="number" value={ctc} onChange={e => setCtc(+e.target.value)} style={{ width: 128, background: 'transparent', border: 'none', fontSize: 20, fontWeight: 700, color: 'var(--accent)', outline: 'none', textAlign: 'right', margin: 0 }} />
              </div>
            </div>
            <input type="range" aria-label="Annual CTC" min={500000} max={10000000} step={100000} value={ctc} onChange={e => setCtc(+e.target.value)} style={{ ...slider, accentColor: 'var(--accent)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginTop: 8, fontWeight: 500 }}><span>₹5L</span><span>₹1Cr</span></div>
          </div>

          {/* PF Configuration */}
          <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 12, border: '1px solid var(--border)', margin: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '0 0 12px 0' }}>
              <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                <ShieldCheck style={{ width: 16, height: 16, color: 'var(--accent)' }} /> PF Configuration
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer', color: 'var(--text-muted)', margin: 0 }}>
                <input type="checkbox" checked={intl} onChange={e => setIntl(e.target.checked)} style={{ width: 14, height: 14, accentColor: 'var(--accent)', margin: 0 }} /> International Worker
              </label>
            </div>
            <div style={{ display: 'flex', gap: 8, background: 'var(--bg-primary)', padding: 4, borderRadius: 8, border: '1px solid var(--border)' }}>
              <button onClick={() => setPfType('capped')} style={togBtn(pfType === 'capped')}>Capped (₹1800)</button>
              <button onClick={() => setPfType('full')} style={togBtn(pfType === 'full')}>Full Basic</button>
            </div>
          </div>

          {/* Tax Regime */}
          <div style={sCard}>
            <label style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 16px 0', display: 'block' }}>Tax Regime</label>
            <div style={{ display: 'flex', background: 'var(--bg-tertiary)', padding: 4, borderRadius: 12, position: 'relative' }}>
              <button onClick={() => setRegime('new')} style={{ flex: 1, padding: '12px 8px', fontSize: 14, fontWeight: 700, borderRadius: 8, border: 'none', cursor: 'pointer', background: regime === 'new' ? 'var(--bg-secondary)' : 'transparent', color: regime === 'new' ? 'var(--accent)' : 'var(--text-muted)', boxShadow: regime === 'new' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none', transition: 'all 0.2s', margin: 0, zIndex: 1 }}>New Regime (Default)</button>
              <button onClick={() => setRegime('old')} style={{ flex: 1, padding: '12px 8px', fontSize: 14, fontWeight: 700, borderRadius: 8, border: 'none', cursor: 'pointer', background: regime === 'old' ? 'var(--bg-secondary)' : 'transparent', color: regime === 'old' ? 'var(--accent)' : 'var(--text-muted)', boxShadow: regime === 'old' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none', transition: 'all 0.2s', margin: 0, zIndex: 1 }}>Old Regime</button>
            </div>
            {regime === 'new' && <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '12px 0 0 0', display: 'flex', alignItems: 'center', gap: 8 }}><Info style={{ width: 12, height: 12 }} /> Standard Deduction ₹75k, No 80C/80D.</p>}
          </div>

          {/* VPF */}
          <div style={{ ...sCard, position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: -16, right: -16, padding: 32, background: 'rgba(249,115,22,0.05)', borderRadius: '0 0 0 100%' }}>
              <TrendingUp style={{ color: 'rgba(249,115,22,0.5)', width: 24, height: 24 }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '0 0 16px 0' }}>
              <label style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Voluntary PF (VPF)</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, background: 'var(--bg-tertiary)', borderRadius: 8, padding: 4 }}>
                <button onClick={() => setVpfMode('amount')} style={{ padding: '4px 12px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: vpfMode === 'amount' ? 700 : 400, background: vpfMode === 'amount' ? 'var(--bg-secondary)' : 'transparent', color: vpfMode === 'amount' ? 'var(--text-primary)' : 'var(--text-muted)', boxShadow: vpfMode === 'amount' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none', margin: 0 }}>₹ Amount</button>
                <button onClick={() => setVpfMode('pct')} style={{ padding: '4px 12px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: vpfMode === 'pct' ? 700 : 400, background: vpfMode === 'pct' ? 'var(--bg-secondary)' : 'transparent', color: vpfMode === 'pct' ? 'var(--text-primary)' : 'var(--text-muted)', boxShadow: vpfMode === 'pct' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none', margin: 0 }}>% Basic</button>
              </div>
            </div>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontWeight: 700, margin: 0 }}>₹</span>
              <input type="number" value={vpf} onChange={e => setVpf(+e.target.value)} placeholder="Monthly VPF" style={{ width: '100%', padding: '12px 16px 12px 32px', background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 12, fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', outline: 'none', margin: 0 }} />
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Monthly In-Hand */}
          <div style={{ background: '#0f172a', color: '#fff', padding: 32, borderRadius: 24, boxShadow: '0 20px 25px rgba(0,0,0,0.15)', border: '1px solid #1e293b', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: '-50%', right: '-25%', width: 256, height: 256, background: 'rgba(99,102,241,0.2)', borderRadius: '50%', filter: 'blur(48px)', pointerEvents: 'none' }} />
            <div style={{ position: 'relative', zIndex: 1 }}>
              <div style={{ marginBottom: 32 }}>
                <p style={{ color: '#9ca3af', fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', margin: '0 0 4px 0' }}>Monthly In-Hand</p>
                <h3 style={{ fontSize: compact ? 36 : 48, fontWeight: 800, color: '#34d399', margin: '0 0 8px 0' }}>₹{fmt(result?.monthly_inhand)}</h3>
                <p style={{ fontSize: 14, color: '#6b7280', margin: 0 }}>After all deductions & taxes</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 24 }}>
                <div>
                  <p style={{ color: '#9ca3af', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 4px 0' }}>Annual Tax</p>
                  <p style={{ fontSize: 20, fontWeight: 700, color: '#f87171', margin: 0 }}>₹{fmt(result?.annual_tax)}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ color: '#9ca3af', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 4px 0' }}>Eff. Tax Rate</p>
                  <p style={{ fontSize: 20, fontWeight: 700, color: '#93c5fd', margin: 0 }}>{result?.effective_tax_rate || 0}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Salary Distribution */}
          <div style={{ ...sCard, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)', width: '100%', textAlign: 'left', margin: '0 0 16px 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Salary Distribution</h4>
            <div style={{ width: 256, height: 256, position: 'relative' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartData.filter(d => d.value > 0)} cx="50%" cy="50%" innerRadius="47%" outerRadius="62%" dataKey="value" stroke="none">
                    {chartData.filter(d => d.value > 0).map((d, i) => {
                      const ci = chartData.findIndex(c => c.name === d.name);
                      return <Cell key={i} fill={COLORS[ci]} />;
                    })}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', pointerEvents: 'none' }}>
                <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 700 }}>CTC</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>₹{fmt(ctc / 100000)}L</span>
              </div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center', marginTop: 16 }}>
              {['Take Home', 'Income Tax', 'PF & VPF', 'Other Deductions'].map((name, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>
                  <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS[i] }} />{name}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Breakdown */}
      {result && <BreakdownTable result={result} pfType={pfType} />}

      {/* Disclaimer */}
      <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 12, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
        <strong>Disclaimer:</strong> This calculator provides an estimation based on the Finance Bill 2026. Actual tax liability may vary based on specific exemptions (Section 10), HRA city classification, and other income sources. Please consult a CA for exact filing.
      </div>
    </div>
  );
}

function BreakdownTable({ result, pfType }) {
  const b = result.breakdown;
  const sCard = { background: 'var(--bg-secondary)', borderRadius: 16, margin: 0, border: '1px solid var(--border)', overflow: 'hidden' };

  const Row = ({ label, monthly, annual, style: s = {}, indent, color, bold, badge }) => (
    <tr style={s}>
      <td style={{ padding: '10px 24px', fontWeight: bold ? 700 : 500, color: color || 'var(--text-muted)', paddingLeft: indent ? 32 : 24, fontSize: 14 }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>{label}{badge && <span style={{ fontSize: 10, background: '#fef3c7', color: '#92400e', padding: '2px 6px', borderRadius: 4, border: '1px solid #fde68a', marginLeft: 4, fontWeight: 700 }}>{badge}</span>}</span>
      </td>
      <td style={{ padding: '10px 24px', textAlign: 'right', fontFamily: 'monospace', fontSize: 14, color: color || 'var(--text-muted)', fontWeight: bold ? 700 : 400 }}>{monthly}</td>
      <td style={{ padding: '10px 24px', textAlign: 'right', fontFamily: 'monospace', fontSize: 14, color: color || (bold ? 'var(--text-primary)' : 'var(--text-muted)'), fontWeight: bold ? 700 : 400 }}>{annual}</td>
    </tr>
  );

  const grossDed = b.employee_pf + b.professional_tax + result.annual_tax;

  return (
    <div style={sCard}>
      <div style={{ padding: 16, background: 'var(--bg-tertiary)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontWeight: 700, color: 'var(--text-primary)', margin: 0, fontSize: 16 }}>Detailed Breakdown</h3>
        <span style={{ fontSize: 12, fontFamily: 'monospace', background: 'rgba(99,102,241,0.1)', color: 'var(--accent)', padding: '4px 8px', borderRadius: 4 }}>FY 2026-27</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', fontSize: 14, textAlign: 'left', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--bg-tertiary)', color: 'var(--text-muted)', textTransform: 'uppercase', fontSize: 12 }}>
              <th style={{ padding: '12px 24px' }}>Component</th>
              <th style={{ padding: '12px 24px', textAlign: 'right' }}>Monthly</th>
              <th style={{ padding: '12px 24px', textAlign: 'right' }}>Annual</th>
            </tr>
          </thead>
          <tbody>
            <Row label="Annual CTC" monthly="-" annual={`₹${fmt(b.annual_ctc)}`} bold style={{ background: 'var(--bg-tertiary)' }} color="var(--text-primary)" />
            <Row label="(-) Gratuity (4.81%)" monthly="-" annual={`₹${fmt(b.gratuity)}`} indent />
            <Row label="(-) Employer PF (12%)" monthly="-" annual={`₹${fmt(b.employer_pf)}`} indent />
            <Row label="Gross Salary" monthly={`₹${fmt(Math.round(b.gross_salary / 12))}`} annual={`₹${fmt(b.gross_salary)}`} bold color="var(--accent)" style={{ background: 'rgba(99,102,241,0.05)', borderTop: '1px solid rgba(99,102,241,0.2)' }} />
            <Row label="Basic Salary" monthly={`₹${fmt(Math.round(b.basic / 12))}`} annual={`₹${fmt(b.basic)}`} indent />
            <Row label="HRA" monthly={`₹${fmt(Math.round(b.hra / 12))}`} annual={`₹${fmt(b.hra)}`} indent />
            <Row label="Special Allowance" monthly={`₹${fmt(Math.round(b.special_allowance / 12))}`} annual={`₹${fmt(b.special_allowance)}`} indent />
            <Row label="Gross Deductions" monthly={`₹${fmt(Math.round(grossDed / 12))}`} annual={`₹${fmt(grossDed)}`} bold color="#ef4444" style={{ background: 'rgba(239,68,68,0.05)', borderTop: '1px solid rgba(239,68,68,0.2)' }} />
            <Row label="Employee PF" monthly={`-₹${fmt(Math.round(b.employee_pf / 12))}`} annual={`-₹${fmt(b.employee_pf)}`} indent color="#f87171" badge={pfType === 'capped' ? 'Capped' : null} />
            <Row label="Professional Tax" monthly={`-₹${fmt(Math.round(b.professional_tax / 12))}`} annual={`-₹${fmt(b.professional_tax)}`} indent color="#f87171" />
            <Row label="Income Tax" monthly={`-₹${fmt(Math.round(result.annual_tax / 12))}`} annual={`-₹${fmt(result.annual_tax)}`} indent bold color="#ef4444" style={{ background: 'rgba(239,68,68,0.1)' }} />
            <Row label="Net In-Hand Salary" monthly={`₹${fmt(result.monthly_inhand)}`} annual={`₹${fmt(result.annual_inhand)}`} bold color="var(--text-primary)" style={{ background: 'rgba(99,102,241,0.15)', borderTop: '2px solid var(--accent)', fontSize: 18 }} />
          </tbody>
        </table>
      </div>
    </div>
  );
}
