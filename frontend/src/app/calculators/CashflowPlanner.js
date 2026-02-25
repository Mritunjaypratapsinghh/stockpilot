'use client';
import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Trash2 } from 'lucide-react';

const fmt = n => n?.toLocaleString('en-IN') || '0';

const s = {
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 1000, margin: '0 auto', padding: 0 },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  title: { fontSize: 18, fontWeight: 600, margin: '0 0 24px 0', padding: 0 },
  sectionHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '0 0 12px 0', padding: 0 },
  sectionTitle: { fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8, margin: 0, padding: 0 },
  addBtn: { display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: 'var(--accent)', fontSize: 13, cursor: 'pointer', margin: 0, padding: 0 },
  inputRow: { display: 'flex', gap: 8, margin: '0 0 8px 0', padding: 0 },
  input: { flex: 1, padding: '10px 12px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13, color: 'var(--text-primary)' },
  inputAmount: { width: 110, padding: '10px 12px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13, color: 'var(--text-primary)', textAlign: 'right' },
  deleteBtn: { padding: 8, margin: 0, background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' },
  section: { margin: '0 0 24px 0', padding: 0 },
  totals: { display: 'flex', justifyContent: 'space-between', padding: '16px 0 0 0', margin: '16px 0 0 0', borderTop: '1px solid var(--border)' },
  totalLabel: { fontSize: 13, color: 'var(--text-muted)', margin: '0 0 4px 0', padding: 0 },
  totalValue: { fontSize: 18, fontWeight: 600, margin: 0, padding: 0 },
  statGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, margin: 0, padding: 0 },
  statCard: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 16, margin: 0 },
  statLabel: { fontSize: 13, color: 'var(--text-muted)', margin: '0 0 4px 0', padding: 0 },
  statValue: { fontSize: 24, fontWeight: 700, margin: 0, padding: 0 },
  vizCard: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: '16px 0 0 0' },
  vizTitle: { fontSize: 13, fontWeight: 500, margin: '0 0 16px 0', padding: 0 },
  vizContainer: { position: 'relative', height: 200, margin: 0, padding: 0 },
  vizBar: { position: 'absolute', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' },
  statusCard: { padding: 16, borderRadius: 12, margin: '16px 0 0 0' },
};

export default function CashflowPlanner() {
  const [inflows, setInflows] = useState([{ name: 'Salary', amount: 80000 }, { name: 'Freelance', amount: 20000 }]);
  const [outflows, setOutflows] = useState([{ name: 'Rent', amount: 25000 }, { name: 'Food', amount: 15000 }, { name: 'Travel', amount: 5000 }]);
  const [result, setResult] = useState(null);

  useEffect(() => {
    const inflowStr = inflows.map(i => i.amount).join(',');
    const outflowStr = outflows.map(o => o.amount).join(',');
    api(`/api/v1/calculators/cashflow?inflows=${inflowStr}&outflows=${outflowStr}`)
      .then(setResult).catch(console.error);
  }, [inflows, outflows]);

  const addInflow = () => setInflows([...inflows, { name: '', amount: 0 }]);
  const addOutflow = () => setOutflows([...outflows, { name: '', amount: 0 }]);
  const removeInflow = (i) => setInflows(inflows.filter((_, idx) => idx !== i));
  const removeOutflow = (i) => setOutflows(outflows.filter((_, idx) => idx !== i));
  const updateInflow = (i, field, val) => setInflows(inflows.map((item, idx) => idx === i ? { ...item, [field]: field === 'amount' ? +val : val } : item));
  const updateOutflow = (i, field, val) => setOutflows(outflows.map((item, idx) => idx === i ? { ...item, [field]: field === 'amount' ? +val : val } : item));

  return (
    <div style={s.grid}>
      <div style={s.card}>
        <h2 style={s.title}>Financial Inputs</h2>
        
        <div style={s.section}>
          <div style={s.sectionHeader}>
            <span style={{ ...s.sectionTitle, color: '#10b981' }}>↗ INFLOWS</span>
            <button onClick={addInflow} style={s.addBtn}><Plus style={{ width: 16, height: 16, margin: 0, padding: 0 }} /> Add</button>
          </div>
          {inflows.map((item, i) => (
            <div key={i} style={s.inputRow}>
              <input type="text" value={item.name} onChange={e => updateInflow(i, 'name', e.target.value)} placeholder="Source" style={s.input} />
              <input type="number" value={item.amount} onChange={e => updateInflow(i, 'amount', e.target.value)} placeholder="Amount" style={s.inputAmount} />
              {inflows.length > 1 && <button onClick={() => removeInflow(i)} style={s.deleteBtn}><Trash2 style={{ width: 16, height: 16, margin: 0, padding: 0 }} /></button>}
            </div>
          ))}
        </div>

        <div style={s.section}>
          <div style={s.sectionHeader}>
            <span style={{ ...s.sectionTitle, color: '#ef4444' }}>↙ OUTFLOWS</span>
            <button onClick={addOutflow} style={s.addBtn}><Plus style={{ width: 16, height: 16, margin: 0, padding: 0 }} /> Add</button>
          </div>
          {outflows.map((item, i) => (
            <div key={i} style={s.inputRow}>
              <input type="text" value={item.name} onChange={e => updateOutflow(i, 'name', e.target.value)} placeholder="Expense" style={s.input} />
              <input type="number" value={item.amount} onChange={e => updateOutflow(i, 'amount', e.target.value)} placeholder="Amount" style={s.inputAmount} />
              {outflows.length > 1 && <button onClick={() => removeOutflow(i)} style={s.deleteBtn}><Trash2 style={{ width: 16, height: 16, margin: 0, padding: 0 }} /></button>}
            </div>
          ))}
        </div>

        <div style={s.totals}>
          <div><div style={s.totalLabel}>Total Income</div><div style={{ ...s.totalValue, color: '#10b981' }}>₹{fmt(result?.total_income)}</div></div>
          <div style={{ textAlign: 'right' }}><div style={s.totalLabel}>Total Expenses</div><div style={{ ...s.totalValue, color: '#ef4444' }}>₹{fmt(result?.total_expenses)}</div></div>
        </div>
      </div>

      <div>
        {result && (
          <>
            <div style={s.statGrid}>
              <div style={s.statCard}>
                <div style={s.statLabel}>Net Surplus</div>
                <div style={{ ...s.statValue, color: result.net_surplus >= 0 ? '#10b981' : '#ef4444' }}>
                  {result.net_surplus >= 0 ? '+' : ''}₹{fmt(result.net_surplus)}
                </div>
              </div>
              <div style={s.statCard}>
                <div style={s.statLabel}>Savings Rate</div>
                <div style={s.statValue}>{result.savings_rate}%</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Target: {result.target_savings_rate}%</div>
              </div>
            </div>

            <div style={s.vizCard}>
              <div style={s.vizTitle}>CASH FLOW VISUALIZATION</div>
              <div style={s.vizContainer}>
                <div style={{ ...s.vizBar, left: 0, top: '50%', transform: 'translateY(-50%)', width: 90, height: 120, background: 'rgba(16,185,129,0.2)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Income</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#10b981' }}>₹{fmt(result.total_income)}</div>
                </div>
                <div style={{ position: 'absolute', right: 0, top: 0, width: 90, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ ...s.vizBar, position: 'relative', width: '100%', height: 50, background: 'rgba(16,185,129,0.2)' }}>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Savings</div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#10b981' }}>₹{fmt(result.net_surplus)}</div>
                  </div>
                  {outflows.slice(0, 3).map((o, i) => (
                    <div key={i} style={{ ...s.vizBar, position: 'relative', width: '100%', height: 40, background: 'rgba(239,68,68,0.2)' }}>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{o.name}</div>
                      <div style={{ fontSize: 11, fontWeight: 600, color: '#ef4444' }}>₹{fmt(o.amount)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ ...s.statusCard, background: result.savings_rate >= result.target_savings_rate ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)', border: `1px solid ${result.savings_rate >= result.target_savings_rate ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}` }}>
              {result.savings_rate >= result.target_savings_rate ? (
                <p style={{ fontSize: 13, color: '#10b981', margin: 0 }}>✓ Great! You're saving {result.savings_rate}% of your income, above the {result.target_savings_rate}% target.</p>
              ) : (
                <p style={{ fontSize: 13, color: '#f59e0b', margin: 0 }}>⚠ Your savings rate is {result.savings_rate}%, below the recommended {result.target_savings_rate}%. Consider reducing expenses.</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
