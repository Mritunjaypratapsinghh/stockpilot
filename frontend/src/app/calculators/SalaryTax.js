'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { api } from '../../lib/api';

const fmt = n => n?.toLocaleString('en-IN') || '0';
const COLORS = ['#10b981', '#ef4444', '#6366f1', '#f59e0b'];

const s = {
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24, maxWidth: 1200, margin: '0 auto', padding: 0 },
  header: { display: 'flex', alignItems: 'center', gap: 12, margin: '0 0 24px 0', padding: 0 },
  title: { fontSize: 20, fontWeight: 700, margin: 0, padding: 0 },
  badge: { padding: '4px 10px', background: 'rgba(99,102,241,0.1)', borderRadius: 4, color: 'var(--accent)', fontSize: 12, fontWeight: 500 },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  label: { fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 8px 0', padding: 0, display: 'block' },
  inputRow: { display: 'flex', alignItems: 'center', gap: 8, margin: 0, padding: 0 },
  input: { flex: 1, padding: '10px 12px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 14, color: 'var(--text-primary)' },
  slider: { width: '100%', height: 6, margin: '8px 0', padding: 0, accentColor: 'var(--accent)' },
  sliderLabels: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', margin: '0 0 4px 0', padding: 0 },
  section: { margin: '0 0 20px 0', padding: 0 },
  btnGroup: { display: 'flex', gap: 8, margin: 0, padding: 0 },
  btn: { flex: 1, padding: '10px', margin: 0, border: 'none', borderRadius: 8, fontSize: 12, cursor: 'pointer', transition: 'all 0.15s' },
  hint: { fontSize: 11, color: 'var(--text-muted)', margin: '8px 0 0 0', padding: 0 },
  resultCard: { background: 'linear-gradient(135deg, #10b981, #059669)', borderRadius: 12, padding: 24, margin: 0, color: '#fff' },
  resultLabel: { fontSize: 12, opacity: 0.8, margin: '0 0 4px 0', padding: 0 },
  resultValue: { fontSize: 36, fontWeight: 700, margin: '0 0 4px 0', padding: 0 },
  resultSub: { fontSize: 12, opacity: 0.8, margin: 0, padding: 0 },
  statRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, margin: '24px 0 0 0', padding: 0 },
  stat: { margin: 0, padding: 0 },
  statLabel: { fontSize: 11, opacity: 0.8, margin: '0 0 4px 0', padding: 0 },
  statValue: { fontSize: 20, fontWeight: 600, margin: 0, padding: 0 },
  breakdownCard: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  breakdownHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 16px 0', padding: 0 },
  breakdownTitle: { fontSize: 14, fontWeight: 600, margin: 0, padding: 0 },
  breakdownBadge: { fontSize: 11, color: 'var(--text-muted)' },
  row: { display: 'flex', justifyContent: 'space-between', padding: '8px 0', margin: 0, borderBottom: '1px solid var(--border)', fontSize: 13 },
  rowLabel: { color: 'var(--text-muted)', paddingLeft: 8 },
  green: { color: '#10b981' },
  red: { color: '#ef4444' },
  disclaimer: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8, padding: 16, margin: '24px auto 0', maxWidth: 1200, fontSize: 12, color: 'var(--text-muted)' },
};

export default function SalaryTax() {
  const [ctc, setCtc] = useState(1200000);
  const [pfType, setPfType] = useState('capped');
  const [regime, setRegime] = useState('new');
  const [vpf, setVpf] = useState(0);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/salary-tax?annual_ctc=${ctc}&pf_type=${pfType}&regime=${regime}&vpf=${vpf}`)
      .then(setResult).catch(console.error);
  }, [ctc, pfType, regime, vpf]);

  const chartData = result ? [
    { name: 'Take Home', value: result.annual_inhand },
    { name: 'Income Tax', value: result.annual_tax },
    { name: 'PF & VPF', value: result.breakdown.employee_pf },
    { name: 'Other', value: result.breakdown.professional_tax + result.breakdown.gratuity },
  ].filter(d => d.value > 0) : [];

  return (
    <div>
      <div style={s.header}>
        <h1 style={s.title}>Salary & Tax Calculator</h1>
        <span style={s.badge}>FY 26-27</span>
      </div>

      <div style={s.grid}>
        <div style={s.card}>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '0 0 24px 0' }}>Calculate your In-Hand Salary and compare New vs. Old Regime tax liability.</p>
          
          <div style={s.section}>
            <label style={s.label}>Annual CTC</label>
            <div style={s.inputRow}>
              <span style={{ color: 'var(--text-muted)' }}>₹</span>
              <input type="number" value={ctc} onChange={e => setCtc(+e.target.value)} style={s.input} />
            </div>
            <input type="range" min="300000" max="10000000" step="50000" value={ctc} onChange={e => setCtc(+e.target.value)} style={s.slider} />
            <div style={s.sliderLabels}><span>₹3L</span><span>₹1Cr</span></div>
          </div>

          <div style={s.section}>
            <label style={s.label}>PF Configuration</label>
            <div style={s.btnGroup}>
              <button onClick={() => setPfType('capped')} style={{ ...s.btn, background: pfType === 'capped' ? 'var(--accent)' : 'var(--bg-tertiary)', color: pfType === 'capped' ? '#fff' : 'var(--text-secondary)' }}>Capped (₹1800)</button>
              <button onClick={() => setPfType('full')} style={{ ...s.btn, background: pfType === 'full' ? 'var(--accent)' : 'var(--bg-tertiary)', color: pfType === 'full' ? '#fff' : 'var(--text-secondary)' }}>Full Basic</button>
            </div>
          </div>

          <div style={s.section}>
            <label style={s.label}>TAX REGIME</label>
            <div style={s.btnGroup}>
              <button onClick={() => setRegime('new')} style={{ ...s.btn, background: regime === 'new' ? 'var(--accent)' : 'var(--bg-tertiary)', color: regime === 'new' ? '#fff' : 'var(--text-secondary)' }}>New Regime (Default)</button>
              <button onClick={() => setRegime('old')} style={{ ...s.btn, background: regime === 'old' ? 'var(--accent)' : 'var(--bg-tertiary)', color: regime === 'old' ? '#fff' : 'var(--text-secondary)' }}>Old Regime</button>
            </div>
            {regime === 'new' && <p style={s.hint}>Standard Deduction ₹75k. No HRA/80C.</p>}
          </div>

          <div style={s.section}>
            <label style={s.label}>Voluntary PF (VPF)</label>
            <div style={s.inputRow}>
              <span style={{ color: 'var(--text-muted)' }}>₹</span>
              <input type="number" value={vpf} onChange={e => setVpf(+e.target.value)} placeholder="Monthly VPF" style={s.input} />
            </div>
          </div>
        </div>

        <div style={s.resultCard}>
          <div style={s.resultLabel}>MONTHLY IN-HAND</div>
          <div style={s.resultValue}>₹{fmt(result?.monthly_inhand)}</div>
          <div style={s.resultSub}>After all deductions & taxes</div>
          
          <div style={s.statRow}>
            <div style={s.stat}><div style={s.statLabel}>ANNUAL TAX</div><div style={s.statValue}>₹{fmt(result?.annual_tax)}</div></div>
            <div style={s.stat}><div style={s.statLabel}>EFF. TAX RATE</div><div style={s.statValue}>{result?.effective_tax_rate || 0}%</div></div>
          </div>

          <div style={{ margin: '24px 0 0 0' }}>
            <div style={{ fontSize: 12, fontWeight: 500, margin: '0 0 12px 0' }}>SALARY DISTRIBUTION</div>
            <div style={{ height: 120 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart><Pie data={chartData} cx="50%" cy="50%" innerRadius={25} outerRadius={45} dataKey="value">{chartData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}</Pie></PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: 11, margin: '8px 0 0 0' }}>
              {chartData.map((d, i) => (<span key={i} style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS[i] }}></span>{d.name}</span>))}
            </div>
          </div>
        </div>

        <div style={s.breakdownCard}>
          <div style={s.breakdownHeader}>
            <h3 style={s.breakdownTitle}>Detailed Breakdown</h3>
            <span style={s.breakdownBadge}>FY 2026-27</span>
          </div>

          {result && (
            <div>
              <div style={{ ...s.row, borderBottom: '1px solid var(--border)' }}><span>Annual CTC</span><span style={{ fontWeight: 500 }}>₹{fmt(result.breakdown.annual_ctc)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>(-) Gratuity 4.81%</span><span>₹{fmt(result.breakdown.gratuity)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>(-) Employer PF 12%</span><span>₹{fmt(result.breakdown.employer_pf)}</span></div>
              <div style={{ ...s.row, ...s.green }}><span>Gross Salary</span><span style={{ fontWeight: 500 }}>₹{fmt(result.breakdown.gross_salary)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>Basic Salary</span><span>₹{fmt(result.breakdown.basic)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>HRA</span><span>₹{fmt(result.breakdown.hra)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>Special Allowance</span><span>₹{fmt(result.breakdown.special_allowance)}</span></div>
              <div style={{ ...s.row, ...s.red }}><span>Gross Deductions</span><span style={{ fontWeight: 500 }}>₹{fmt(result.breakdown.employee_pf + result.breakdown.professional_tax + result.annual_tax)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>Employee PF</span><span>-₹{fmt(result.breakdown.employee_pf)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>Professional Tax</span><span>-₹{fmt(result.breakdown.professional_tax)}</span></div>
              <div style={s.row}><span style={s.rowLabel}>Income Tax</span><span style={result.annual_tax === 0 ? s.green : {}}>-₹{fmt(result.annual_tax)}</span></div>
              <div style={{ ...s.row, borderBottom: 'none', fontWeight: 600 }}><span>Net In-Hand Salary</span><span style={s.green}>₹{fmt(result.annual_inhand)}</span></div>
            </div>
          )}
        </div>
      </div>

      <div style={s.disclaimer}>
        <strong>Disclaimer:</strong> This calculator provides an estimation based on the Finance Bill 2026. Actual tax liability may vary based on specific exemptions (Section 10), HRA city classification, and other income sources. Please consult a CA for exact filing.
      </div>
    </div>
  );
}
