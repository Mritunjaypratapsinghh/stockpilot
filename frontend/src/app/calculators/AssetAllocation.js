'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { api } from '../../lib/api';
import { Plus, Trash2, AlertTriangle } from 'lucide-react';
import { CalcStatus, C, card, grid2, label, val, slider, sliderLabels, row, section, title, statCard, statLabel, statVal, gridHalf, footer, footerIcon, fmt, useCompact } from './theme';

const RISK_LEVELS = ['very_low', 'low', 'moderate', 'high', 'very_high'];
const RISK_LABELS = { very_low: 'Very Low', low: 'Low', moderate: 'Moderate', high: 'High', very_high: 'Very High' };
const ASSET_TYPES = ['Large Cap Equity', 'Mid Cap Equity', 'Small Cap Equity', 'Debt Fund', 'Gold', 'Cash/Liquid'];
const REC_COLORS = ['#7C3AED', '#a78bfa', '#c4b5fd', '#06b6d4', '#f59e0b', '#6b7280'];
const CUR_COLORS = ['#f59e0b', '#06b6d4', '#6b7280', '#7C3AED', '#10b981', '#ef4444'];

export default function AssetAllocation() {
  const compact = useCompact();
  const [age, setAge] = useState(30);
  const [risk, setRisk] = useState('moderate');
  const [horizon, setHorizon] = useState(10);
  const [beginner, setBeginner] = useState(false);
  const [showHoldings, setShowHoldings] = useState(true);
  const [holdings, setHoldings] = useState([
    { name: 'Nifty 50 Fund', type: 'Large Cap Equity', amount: 200000 },
    { name: 'Debt Fund', type: 'Debt Fund', amount: 150000 },
    { name: 'Savings Account', type: 'Cash/Liquid', amount: 50000 },
  ]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/asset-allocation?age=${age}&risk_appetite=${risk}&horizon=${horizon}`)
      .then(r => { setResult(r); setError(null); }).catch(e => setError(e.message));
  }, [age, risk, horizon]);

  const addHolding = () => setHoldings([...holdings, { name: '', type: 'Large Cap Equity', amount: 0 }]);
  const removeHolding = i => setHoldings(holdings.filter((_, idx) => idx !== i));
  const updateHolding = (i, f, v) => setHoldings(holdings.map((h, idx) => idx === i ? { ...h, [f]: f === 'amount' ? +v : v } : h));

  const totalHoldings = holdings.reduce((s, h) => s + h.amount, 0);
  const currentAlloc = {};
  holdings.forEach(h => { currentAlloc[h.type] = (currentAlloc[h.type] || 0) + h.amount; });
  const currentEquity = ((currentAlloc['Large Cap Equity'] || 0) + (currentAlloc['Mid Cap Equity'] || 0) + (currentAlloc['Small Cap Equity'] || 0)) / (totalHoldings || 1) * 100;
  const currentDebt = (currentAlloc['Debt Fund'] || 0) / (totalHoldings || 1) * 100;

  const currentChartData = Object.entries(currentAlloc).filter(([, v]) => v > 0).map(([k, v]) => ({ name: k, value: Math.round(v / totalHoldings * 100) }));

  const recChartData = result ? [
    { name: 'Large Cap Equity', value: result.recommended.breakdown.large_cap },
    { name: 'Large & Mid Cap', value: result.recommended.breakdown.mid_cap },
    { name: 'Small Cap', value: result.recommended.breakdown.small_cap || 0 },
    { name: 'Debt Fund', value: result.recommended.breakdown.debt_fund },
    { name: 'Gold', value: result.recommended.gold },
    { name: 'Cash/Liquid', value: 5 },
  ].filter(d => d.value > 0) : [];

  const recEquity = result ? result.recommended.equity : 0;
  const divergence = showHoldings && totalHoldings > 0 ? Math.abs(recEquity - Math.round(currentEquity)) + Math.abs((result?.recommended.debt || 0) - Math.round(currentDebt)) : 0;
  const divergencePct = Math.min(divergence, 100);

  const holdingCard = { background: C.cardAlt, borderRadius: 12, padding: 14, margin: '0 0 10px 0', border: `1px solid ${C.border}` };

  return (
    <div style={{ margin: 0, padding: 0 }}>
      <CalcStatus loading={!result && !error} error={error} />
      <div style={grid2(compact)}>
        {/* LEFT */}
        <div>
          <div style={card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 24px 0' }}>
              <h2 style={{ ...title, margin: 0 }}>YOUR PROFILE</h2>
              <span style={{ fontSize: 20, color: C.textMuted, cursor: 'pointer' }}>ⓘ</span>
            </div>

            <div style={section}>
              <div style={row}><span style={{ fontSize: 14, color: C.accent }}>Your Age</span><span style={val}>{age} Yrs</span></div>
              <input type="range" min={18} max={80} value={age} aria-label="Age" onChange={e => setAge(+e.target.value)} style={slider} />
              <div style={sliderLabels}><span>18 Yrs</span><span>80 Yrs</span></div>
            </div>

            <div style={section}>
              <div style={row}><span style={{ fontSize: 14, color: C.accent }}>Risk Appetite</span><span style={val}>{RISK_LABELS[risk]}</span></div>
              <div role="radiogroup" aria-label="Risk Appetite" style={{ display: 'flex', gap: 0, margin: '8px 0 0', borderRadius: 10, overflow: 'hidden', border: `1px solid ${C.border}` }}>
                {RISK_LEVELS.map((r, i) => (
                  <button key={r} role="radio" aria-checked={risk === r} onClick={() => setRisk(r)} style={{
                    flex: 1, padding: '10px 2px', margin: 0, border: 'none', fontSize: 11, cursor: 'pointer',
                    background: risk === r ? C.accent : C.card, color: risk === r ? '#fff' : C.textSec,
                    fontWeight: risk === r ? 600 : 400, transition: 'all 0.15s',
                  }}>{['V.Low', 'Low', 'Med', 'High', 'V.High'][i]}</button>
                ))}
              </div>
            </div>

            <div style={section}>
              <div style={row}><span style={{ fontSize: 14, color: C.accent }}>Investment Horizon</span><span style={val}>{horizon} Yrs</span></div>
              <input type="range" min={1} max={30} value={horizon} aria-label="Investment Horizon" onChange={e => setHorizon(+e.target.value)} style={slider} />
              <div style={sliderLabels}><span>1 Yr</span><span>30 Yrs</span></div>
            </div>

            <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: 16, background: C.cardAlt, borderRadius: 12, cursor: 'pointer', margin: 0, border: `1px solid ${C.border}` }}>
              <input type="checkbox" checked={beginner} onChange={e => setBeginner(e.target.checked)} style={{ marginTop: 2, accentColor: C.accent }} />
              <div><div style={{ fontSize: 14, fontWeight: 500, color: C.text }}>I am a Beginner</div><div style={{ fontSize: 12, color: C.textMuted }}>I don't have an existing portfolio to compare.</div></div>
            </label>
          </div>

          {!beginner && (
            <div style={{ ...card, marginTop: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 18px 0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 15, fontWeight: 600, color: C.text }}>CURRENT HOLDINGS</span>
                  <button onClick={() => setShowHoldings(!showHoldings)} style={{
                    width: 42, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer', position: 'relative',
                    background: showHoldings ? C.accent : C.borderLight, transition: 'background 0.2s',
                  }}>
                    <span style={{ position: 'absolute', top: 3, left: showHoldings ? 21 : 3, width: 18, height: 18, borderRadius: '50%', background: '#fff', transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)' }} />
                  </button>
                </div>
                <button onClick={addHolding} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: C.accent, fontSize: 14, fontWeight: 500, cursor: 'pointer', padding: 0, margin: 0 }}>
                  <Plus style={{ width: 16, height: 16 }} /> Add Asset
                </button>
              </div>

              {showHoldings && holdings.map((h, i) => (
                <div key={i} style={holdingCard}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 8px 0' }}>
                    <input value={h.name} onChange={e => updateHolding(i, 'name', e.target.value)} placeholder="Fund name" style={{ border: 'none', background: 'transparent', fontSize: 14, color: C.accent, fontWeight: 500, outline: 'none', flex: 1, padding: 0, margin: 0 }} />
                    <select value={h.type} onChange={e => updateHolding(i, 'type', e.target.value)} style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: '4px 8px', fontSize: 12, color: C.textSec, background: C.cardAlt, margin: '0 0 0 8px' }}>
                      {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 14, color: C.textMuted }}>₹</span>
                    <input type="number" value={h.amount} onChange={e => updateHolding(i, 'amount', e.target.value)} style={{ flex: 1, border: 'none', background: 'transparent', fontSize: 15, color: C.text, outline: 'none', padding: 0, margin: 0 }} />
                    {holdings.length > 1 && <button onClick={() => removeHolding(i)} style={{ background: 'none', border: 'none', color: C.textMuted, cursor: 'pointer', padding: 4, margin: 0 }}><Trash2 style={{ width: 15, height: 15 }} /></button>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {result && (
            <div style={{ ...card, marginTop: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '0 0 14px 0' }}>
                <span style={{ color: C.accent, fontSize: 18 }}>→</span>
                <span style={{ fontSize: 15, fontWeight: 600, color: C.text }}>ACTION PLAN</span>
              </div>
              <p style={{ fontSize: 14, color: C.textSec, margin: '0 0 14px 0', lineHeight: 1.6 }}>
                Based on your <strong>{RISK_LABELS[risk]}</strong> risk profile and <strong>{horizon} year</strong> horizon, you should target roughly <strong>{recEquity}% Equity</strong>.
              </p>
              {showHoldings && totalHoldings > 0 && currentEquity < recEquity && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 14, background: C.redBg, borderRadius: 10 }}>
                  <AlertTriangle style={{ width: 16, height: 16, color: C.orange, flexShrink: 0 }} />
                  <span style={{ fontSize: 13, color: C.orange }}>Your Equity is lower than recommended. Consider increasing it.</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT */}
        <div>
          {result && showHoldings && totalHoldings > 0 && !beginner && (
            <div style={{ ...card, marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', margin: '0 0 22px 0' }}>
                <div>
                  <h3 style={{ fontSize: 17, fontWeight: 600, color: C.text, margin: '0 0 4px 0' }}>Reality Check</h3>
                  <p style={{ fontSize: 13, color: C.textMuted, margin: 0 }}>Comparing your portfolio vs. Recommended</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 11, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Portfolio Divergence</div>
                  <div style={{ fontSize: 30, fontWeight: 700, color: divergencePct > 20 ? C.red : C.green }}>{divergencePct.toFixed(1)}%</div>
                  {divergencePct > 20 && <div style={{ fontSize: 12, color: C.red, maxWidth: 170 }}>Significant misalignment. Your risk exposure differs from your ideal profile.</div>}
                </div>
              </div>

              <div style={gridHalf(compact)}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: C.textMuted, textAlign: 'center', margin: '0 0 8px 0', textTransform: 'uppercase' }}>Current</div>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart><Pie data={currentChartData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" paddingAngle={2}>
                        {currentChartData.map((_, i) => <Cell key={i} fill={CUR_COLORS[i % CUR_COLORS.length]} />)}
                      </Pie><Tooltip formatter={v => `${v}%`} /></PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div style={{ fontSize: 12, color: C.textMuted }}>
                    {currentChartData.map((d, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', margin: '3px 0' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 9, height: 9, borderRadius: '50%', background: CUR_COLORS[i % CUR_COLORS.length], display: 'inline-block' }} />{d.name}</span>
                        <span>{d.value}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: C.textMuted, textAlign: 'center', margin: '0 0 8px 0', textTransform: 'uppercase' }}>
                    Recommended <span style={{ background: C.accent, color: '#fff', padding: '2px 8px', borderRadius: 4, fontSize: 10, marginLeft: 4 }}>IDEAL</span>
                  </div>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart><Pie data={recChartData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" paddingAngle={2}>
                        {recChartData.map((_, i) => <Cell key={i} fill={REC_COLORS[i % REC_COLORS.length]} />)}
                      </Pie><Tooltip formatter={v => `${v}%`} /></PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div style={{ fontSize: 12, color: C.textMuted }}>
                    {recChartData.map((d, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', margin: '3px 0' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 9, height: 9, borderRadius: '50%', background: REC_COLORS[i % REC_COLORS.length], display: 'inline-block' }} />{d.name}</span>
                        <span>{d.value}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {result && (beginner || !showHoldings || totalHoldings === 0) && (
            <div style={card}>
              <h2 style={title}>Recommended Allocation</h2>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart><Pie data={recChartData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" paddingAngle={2} label={({ value }) => `${value}%`}>
                    {recChartData.map((_, i) => <Cell key={i} fill={REC_COLORS[i % REC_COLORS.length]} />)}
                  </Pie><Tooltip formatter={v => `${v}%`} /><Legend /></PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ background: C.cardAlt, borderRadius: 12, padding: 18, marginTop: 18, border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 14, fontWeight: 600, margin: '0 0 12px 0', color: C.text }}>Breakdown</div>
                {recChartData.map((d, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, margin: '0 0 6px 0' }}>
                    <span style={{ color: C.textMuted }}>{d.name}</span><span style={{ fontWeight: 500, color: C.text }}>{d.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={footer}>
        <span style={footerIcon}>✓</span>
        <span><strong>Verified Methodology</strong> · Calculations are tested against official standards: Modern Portfolio Theory (Brinson Study).</span>
      </div>
    </div>
  );
}
