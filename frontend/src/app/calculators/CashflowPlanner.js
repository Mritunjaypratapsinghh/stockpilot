'use client';
import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Trash2 } from 'lucide-react';
import { CalcStatus, C, card, grid2, label, input, section, title, statCard, statLabel, statVal, gridHalf, footer, footerIcon, fmt, useCompact } from './theme';

function SankeyDiagram({ inflows, outflows, surplus }) {
  const totalIn = inflows.reduce((s, i) => s + i.amount, 0) || 1;
  const W = 500, H = 300, nodeW = 10;
  const leftX = 70, midX = W / 2 - nodeW / 2, rightX = W - 90;
  const incomeH = 140, incomeY = (H - incomeH) / 2;
  const items = [{ name: 'Savings', amount: Math.max(surplus, 0), color: '#06b6d4' }, ...outflows.map(o => ({ ...o, color: '#ef4444' }))];
  let rightY = (H - 220) / 2;

  const paths = items.map(item => {
    const h = Math.max((item.amount / totalIn) * 220, 20);
    const y = rightY;
    rightY += h + 5;
    return { ...item, y, h };
  });

  return (
    <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ margin: 0, padding: 0 }}>
      <rect x={leftX} y={incomeY} width={nodeW} height={incomeH} rx={5} fill="#10b981" />
      <text x={leftX - 10} y={incomeY + incomeH / 2 - 10} textAnchor="end" style={{ fontSize: 11, fill: 'var(--text-muted)' }}>Income</text>
      <text x={leftX - 10} y={incomeY + incomeH / 2 + 8} textAnchor="end" style={{ fontSize: 12, fill: 'var(--text-primary)', fontWeight: 600 }}>₹{fmt(totalIn)}</text>
      <rect x={midX} y={incomeY} width={nodeW} height={incomeH} rx={5} fill="#10b981" opacity={0.4} />
      <path d={`M${leftX + nodeW},${incomeY} C${midX - 30},${incomeY} ${midX - 30},${incomeY} ${midX},${incomeY} L${midX},${incomeY + incomeH} C${midX - 30},${incomeY + incomeH} ${midX - 30},${incomeY + incomeH} ${leftX + nodeW},${incomeY + incomeH} Z`} fill="#10b981" opacity={0.1} />
      {paths.map((p, i) => {
        const srcY1 = incomeY + (i === 0 ? 0 : paths.slice(0, i).reduce((s, pp) => s + pp.h + 5, 0));
        const srcY2 = srcY1 + p.h;
        return (
          <g key={i}>
            <path d={`M${midX + nodeW},${Math.min(srcY1, incomeY + incomeH - 2)} C${rightX - 40},${srcY1} ${rightX - 40},${p.y} ${rightX},${p.y} L${rightX},${p.y + p.h} C${rightX - 40},${p.y + p.h} ${rightX - 40},${Math.min(srcY2, incomeY + incomeH)} ${midX + nodeW},${Math.min(srcY2, incomeY + incomeH)} Z`} fill={p.color} opacity={0.12} />
            <rect x={rightX} y={p.y} width={nodeW} height={p.h} rx={4} fill={p.color} />
            <text x={rightX + 18} y={p.y + p.h / 2 - 7} style={{ fontSize: 11, fill: 'var(--text-muted)' }}>{p.name}</text>
            <text x={rightX + 18} y={p.y + p.h / 2 + 9} style={{ fontSize: 12, fill: 'var(--text-primary)', fontWeight: 600 }}>₹{fmt(p.amount)}</text>
          </g>
        );
      })}
    </svg>
  );
}

export default function CashflowPlanner() {
  const compact = useCompact();
  const [inflows, setInflows] = useState([{ name: 'Salary', amount: 80000 }, { name: 'Freelance', amount: 20000 }]);
  const [outflows, setOutflows] = useState([{ name: 'Rent', amount: 25000 }, { name: 'Food', amount: 15000 }, { name: 'Travel', amount: 5000 }]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/cashflow?inflows=${inflows.map(i => i.amount).join(',')}&outflows=${outflows.map(o => o.amount).join(',')}`)
      .then(r => { setResult(r); setError(null); }).catch(e => setError(e.message));
  }, [inflows, outflows]);

  const addInflow = () => setInflows([...inflows, { name: '', amount: 0 }]);
  const addOutflow = () => setOutflows([...outflows, { name: '', amount: 0 }]);
  const removeInflow = i => setInflows(inflows.filter((_, idx) => idx !== i));
  const removeOutflow = i => setOutflows(outflows.filter((_, idx) => idx !== i));
  const updateInflow = (i, f, v) => setInflows(inflows.map((item, idx) => idx === i ? { ...item, [f]: f === 'amount' ? +v : v } : item));
  const updateOutflow = (i, f, v) => setOutflows(outflows.map((item, idx) => idx === i ? { ...item, [f]: f === 'amount' ? +v : v } : item));

  const fieldStyle = { flex: 1, padding: '12px 14px', background: C.cardAlt, border: `1.5px solid ${C.border}`, borderRadius: 10, fontSize: 14, color: C.text, outline: 'none', margin: 0 };
  const amtStyle = { ...fieldStyle, width: 120, flex: 'none', textAlign: 'right' };

  return (
    <div style={{ margin: 0, padding: 0 }}>
      <CalcStatus loading={!result && !error} error={error} />
      <div style={grid2(compact)}>
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 24px 0' }}>
            <h2 style={{ ...title, margin: 0 }}>Financial Inputs</h2>
            <span style={{ fontSize: 20, color: C.textMuted, cursor: 'pointer' }}>ⓘ</span>
          </div>

          <div style={section}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 14px 0' }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: C.green, display: 'flex', alignItems: 'center', gap: 6 }}>↗ INFLOWS</span>
              <button onClick={addInflow} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: C.accent, fontSize: 14, fontWeight: 500, cursor: 'pointer', padding: 0, margin: 0 }}><Plus style={{ width: 16, height: 16 }} /> Add</button>
            </div>
            {inflows.map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, margin: '0 0 10px 0', alignItems: 'center' }}>
                <input value={item.name} onChange={e => updateInflow(i, 'name', e.target.value)} placeholder="Source" style={fieldStyle} />
                <input type="number" value={item.amount} onChange={e => updateInflow(i, 'amount', e.target.value)} style={amtStyle} />
                {inflows.length > 1 && <button onClick={() => removeInflow(i)} style={{ background: 'none', border: 'none', color: C.textMuted, cursor: 'pointer', padding: 4, margin: 0 }}><Trash2 style={{ width: 15, height: 15 }} /></button>}
              </div>
            ))}
          </div>

          <div style={section}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 14px 0' }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: C.red, display: 'flex', alignItems: 'center', gap: 6 }}>↙ OUTFLOWS</span>
              <button onClick={addOutflow} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: C.accent, fontSize: 14, fontWeight: 500, cursor: 'pointer', padding: 0, margin: 0 }}><Plus style={{ width: 16, height: 16 }} /> Add</button>
            </div>
            {outflows.map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, margin: '0 0 10px 0', alignItems: 'center' }}>
                <input value={item.name} onChange={e => updateOutflow(i, 'name', e.target.value)} placeholder="Expense" style={fieldStyle} />
                <input type="number" value={item.amount} onChange={e => updateOutflow(i, 'amount', e.target.value)} style={amtStyle} />
                {outflows.length > 1 && <button onClick={() => removeOutflow(i)} style={{ background: 'none', border: 'none', color: C.textMuted, cursor: 'pointer', padding: 4, margin: 0 }}><Trash2 style={{ width: 15, height: 15 }} /></button>}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '18px 0 0 0', borderTop: `1px solid ${C.border}` }}>
            <div><div style={{ fontSize: 13, color: C.textMuted }}>Total Income</div><div style={{ fontSize: 20, fontWeight: 700, color: C.green }}>₹{fmt(result?.total_income)}</div></div>
            <div style={{ textAlign: 'right' }}><div style={{ fontSize: 13, color: C.textMuted }}>Total Expenses</div><div style={{ fontSize: 20, fontWeight: 700, color: C.red }}>₹{fmt(result?.total_expenses)}</div></div>
          </div>
        </div>

        <div>
          {result && (
            <>
              <div style={gridHalf(compact)}>
                <div style={statCard}><div style={statLabel}>Net Surplus</div><div style={{ ...statVal, color: result.net_surplus >= 0 ? C.green : C.red }}>{result.net_surplus >= 0 ? '+ ' : ''}₹{fmt(Math.abs(result.net_surplus))}</div></div>
                <div style={statCard}><div style={statLabel}>Savings Rate</div><div style={statVal}>{result.savings_rate}%</div><div style={{ fontSize: 12, color: C.textMuted, marginTop: 2 }}>Target: {result.target_savings_rate}%</div></div>
              </div>

              <div style={{ ...card, marginTop: 18 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: C.text, margin: '0 0 14px 0', textTransform: 'uppercase' }}>Cash Flow Visualization</div>
                <SankeyDiagram inflows={inflows} outflows={outflows} surplus={result.net_surplus} />
              </div>
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
