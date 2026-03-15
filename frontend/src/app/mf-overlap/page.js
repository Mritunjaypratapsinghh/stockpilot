'use client';
import { useState, useEffect } from 'react';
import { Layers, AlertTriangle, CheckCircle, Info, PieChart, ArrowRight, X } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

const CAT = {
  largecap: { label: 'Large Cap', color: 'bg-blue-500/20 text-blue-400', dot: 'bg-blue-400' },
  midcap: { label: 'Mid Cap', color: 'bg-purple-500/20 text-purple-400', dot: 'bg-purple-400' },
  smallcap: { label: 'Small Cap', color: 'bg-orange-500/20 text-orange-400', dot: 'bg-orange-400' },
  flexicap: { label: 'Flexi Cap', color: 'bg-green-500/20 text-green-400', dot: 'bg-green-400' },
  largemid: { label: 'Large & Mid', color: 'bg-cyan-500/20 text-cyan-400', dot: 'bg-cyan-400' },
  index: { label: 'Index', color: 'bg-yellow-500/20 text-yellow-400', dot: 'bg-yellow-400' },
  debt: { label: 'Debt', color: 'bg-gray-500/20 text-gray-400', dot: 'bg-gray-400' },
  equity: { label: 'Equity', color: 'bg-emerald-500/20 text-emerald-400', dot: 'bg-emerald-400' },
};

const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

function ScoreRing({ score }) {
  const r = 54, c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = score >= 70 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444';
  return (
    <div className="relative w-32 h-32">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="var(--border)" strokeWidth="8" />
        <circle cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={offset} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        <span className="text-[10px] text-[var(--text-muted)]">of 100</span>
      </div>
    </div>
  );
}

export default function MFOverlapPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api('/api/analytics/mf-overlap').then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><main className="p-4 md:p-6"><div className="animate-pulse space-y-4"><div className="h-32 bg-[var(--bg-secondary)] rounded-lg" /><div className="h-64 bg-[var(--bg-secondary)] rounded-lg" /></div></main></div>;

  const { funds = [], overlaps = [], matrix = {}, summary = {} } = data || {};
  const equityFunds = funds.filter(f => f.category !== 'debt');
  const debtFunds = funds.filter(f => f.category === 'debt');

  // Group funds by category for insights
  const catGroups = {};
  equityFunds.forEach(f => {
    catGroups[f.category] = catGroups[f.category] || [];
    catGroups[f.category].push(f);
  });
  const duplicateCats = Object.entries(catGroups).filter(([, v]) => v.length > 1);

  // Build specific recommendations
  const recommendations = [];
  duplicateCats.forEach(([cat, catFunds]) => {
    const sorted = [...catFunds].sort((a, b) => b.value - a.value);
    const keep = sorted[0];
    const drop = sorted.slice(1);
    recommendations.push({
      type: 'consolidate',
      text: `You have ${catFunds.length} ${CAT[cat]?.label || cat} funds. Consider keeping ${keep.symbol} (₹${fmt(keep.value)}) and consolidating ${drop.map(d => d.symbol).join(', ')}.`,
      severity: 'high',
    });
  });
  if (debtFunds.length > 0 && equityFunds.length > 0) {
    recommendations.push({
      type: 'info',
      text: `${debtFunds.length} debt fund${debtFunds.length > 1 ? 's' : ''} excluded — they hold bonds/T-bills, not equities.`,
      severity: 'low',
    });
  }
  if (overlaps.length === 0 && equityFunds.length > 1) {
    recommendations.push({ type: 'good', text: 'No stock overlap across your equity funds. Great diversification!', severity: 'none' });
  }

  if (!funds.length) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar />
        <main className="p-4 md:p-6">
          <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2 mb-6"><Layers className="w-5 h-5 md:w-6 md:h-6" /> MF Overlap Analyzer</h1>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
            <PieChart className="w-12 h-12 mx-auto mb-3 text-[var(--text-muted)]" />
            <p className="text-[var(--text-muted)]">No mutual fund holdings found. Add MF investments to see overlap analysis.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
            <Layers className="w-5 h-5 md:w-6 md:h-6" /> MF Overlap Analyzer
          </h1>
        </div>
        <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/30 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-[#f59e0b] shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium text-[#f59e0b]">Estimated Data</div>
            <div className="text-sm text-[var(--text-secondary)]">Overlap analysis uses estimated top holdings based on fund category (large cap, mid cap, etc.), not actual fund portfolio data from AMCs. Use this as a directional guide, not exact overlap percentages.</div>
          </div>
        </div>

        {/* Top Section: Score + Summary + Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          {/* Score Card */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6 flex items-center gap-6">
            <ScoreRing score={summary.diversification_score || 0} />
            <div>
              <p className="text-sm font-semibold mb-1">Diversification Score</p>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                {summary.diversification_score >= 70 ? 'Your funds are well diversified.' :
                 summary.diversification_score >= 40 ? 'Moderate overlap between funds.' :
                 'High overlap — you\'re paying multiple expense ratios for similar exposure.'}
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6">
            <p className="text-sm font-semibold mb-3">Fund Breakdown</p>
            <div className="space-y-2">
              {Object.entries(catGroups).map(([cat, catFunds]) => (
                <div key={cat} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${CAT[cat]?.dot || 'bg-gray-400'}`} />
                    <span className="text-xs">{CAT[cat]?.label || cat}</span>
                    {catFunds.length > 1 && <span className="text-[10px] bg-red-500/20 text-red-400 px-1.5 rounded">×{catFunds.length}</span>}
                  </div>
                  <span className="text-xs text-[var(--text-muted)]">₹{fmt(catFunds.reduce((s, f) => s + f.value, 0))}</span>
                </div>
              ))}
              {debtFunds.length > 0 && (
                <div className="flex items-center justify-between opacity-50">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-gray-400" />
                    <span className="text-xs">Debt</span>
                    <span className="text-[10px] text-[var(--text-muted)]">(excluded)</span>
                  </div>
                  <span className="text-xs text-[var(--text-muted)]">₹{fmt(debtFunds.reduce((s, f) => s + f.value, 0))}</span>
                </div>
              )}
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6">
            <p className="text-sm font-semibold mb-3">Recommendations</p>
            <div className="space-y-3">
              {recommendations.length === 0 && <p className="text-xs text-[var(--text-muted)]">No issues found.</p>}
              {recommendations.map((r, i) => (
                <div key={i} className="flex gap-2">
                  {r.severity === 'high' ? <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" /> :
                   r.severity === 'none' ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" /> :
                   <Info className="w-4 h-4 text-[var(--text-muted)] shrink-0 mt-0.5" />}
                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">{r.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Funds Grid */}
        <h2 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Your {funds.length} Mutual Funds</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {funds.map(f => {
            const c = CAT[f.category] || CAT.equity;
            const isDuplicate = (catGroups[f.category]?.length || 0) > 1;
            return (
              <div key={f.symbol} className={`bg-[var(--bg-secondary)] border rounded-lg p-4 ${f.category === 'debt' ? 'opacity-50 border-[var(--border)]' : isDuplicate ? 'border-red-500/30' : 'border-[var(--border)]'}`}>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${c.color}`}>{c.label}</span>
                  {isDuplicate && f.category !== 'debt' && <span className="text-[10px] text-red-400">duplicate</span>}
                </div>
                <p className="text-sm font-medium leading-tight mb-2 line-clamp-2">{f.name}</p>
                <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                  <span>₹{fmt(f.value)}</span>
                  <span>{f.category === 'debt' ? 'No equities' : `${f.stock_count} stocks`}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Heatmap */}
        {overlaps.length > 0 && matrix.stocks?.length > 0 && (
          <>
            <h2 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Overlap Heatmap</h2>
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="text-left p-2 pb-3 text-[var(--text-muted)] font-medium sticky left-0 bg-[var(--bg-secondary)] min-w-[120px]">Fund</th>
                    {matrix.stocks.map(s => (
                      <th key={s} className="p-2 pb-3 text-center text-[var(--text-muted)] font-medium min-w-[80px]">{s}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrix.data?.map((row, ri) => {
                    const hasAny = Object.values(row.weights).some(w => w > 0);
                    if (!hasAny) return null;
                    const cat = equityFunds.find(f => f.symbol === row.fund)?.category;
                    return (
                      <tr key={row.fund} className="border-t border-[var(--border)]">
                        <td className="p-2 sticky left-0 bg-[var(--bg-secondary)]">
                          <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full shrink-0 ${CAT[cat]?.dot || 'bg-gray-400'}`} />
                            <span className="font-medium">{row.fund}</span>
                          </div>
                        </td>
                        {matrix.stocks.map(s => {
                          const w = row.weights[s] || 0;
                          return (
                            <td key={s} className="p-2 text-center">
                              {w > 0 ? (
                                <span className="inline-block px-2 py-1 rounded text-xs font-medium" style={{
                                  backgroundColor: `rgba(139, 92, 246, ${Math.min(0.15 + (w / 10) * 0.6, 0.75)})`,
                                  color: w > 4 ? '#e9d5ff' : '#c4b5fd'
                                }}>
                                  {w}%
                                </span>
                              ) : (
                                <span className="text-[var(--border)]">·</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* Overlap Detail List */}
        {overlaps.length > 0 && (
          <>
            <h2 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">
              {overlaps.length} Overlapping Stocks
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {overlaps.map(o => (
                <div key={o.stock} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">{o.stock}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${o.risk_level === 'High' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                      {o.fund_count} funds
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {o.funds.map((f, i) => {
                      const cat = equityFunds.find(ef => ef.symbol === f.fund_symbol)?.category;
                      return (
                        <span key={i} className="text-[11px] bg-[var(--bg-primary)] px-2 py-0.5 rounded flex items-center gap-1">
                          <span className={`w-1.5 h-1.5 rounded-full ${CAT[cat]?.dot || 'bg-gray-400'}`} />
                          {f.fund_symbol} <span className="text-[var(--text-muted)]">{f.weight}%</span>
                        </span>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
