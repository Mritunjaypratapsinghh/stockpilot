'use client';
import { useState, useEffect } from 'react';
import { Layers, AlertTriangle, CheckCircle, Info, PieChart, TrendingDown } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

const CAT_LABELS = { largecap: 'Large Cap', midcap: 'Mid Cap', smallcap: 'Small Cap', flexicap: 'Flexi Cap', largemid: 'Large & Mid', index: 'Index', debt: 'Debt', equity: 'Equity' };
const CAT_COLORS = { largecap: 'bg-blue-500/20 text-blue-400', midcap: 'bg-purple-500/20 text-purple-400', smallcap: 'bg-orange-500/20 text-orange-400', flexicap: 'bg-green-500/20 text-green-400', largemid: 'bg-cyan-500/20 text-cyan-400', index: 'bg-yellow-500/20 text-yellow-400', debt: 'bg-gray-500/20 text-gray-400', equity: 'bg-emerald-500/20 text-emerald-400' };

const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

export default function MFOverlapPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('matrix'); // matrix | list

  useEffect(() => {
    api('/api/analytics/mf-overlap').then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><main className="p-4 md:p-6"><p className="text-[var(--text-muted)]">Analyzing your mutual funds...</p></main></div>;

  const { funds = [], overlaps = [], matrix = {}, summary = {} } = data || {};
  const equityFunds = funds.filter(f => f.category !== 'debt');
  const debtFunds = funds.filter(f => f.category === 'debt');
  const scoreColor = summary.diversification_score >= 70 ? 'text-green-400' : summary.diversification_score >= 40 ? 'text-yellow-400' : 'text-red-400';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
            <Layers className="w-5 h-5 md:w-6 md:h-6" /> MF Overlap Analyzer
          </h1>
          <span className="text-xs bg-yellow-500/20 text-yellow-400 px-3 py-1 rounded-full flex items-center gap-1 w-fit">
            <Info className="w-3 h-3" /> Based on typical category holdings (estimated)
          </span>
        </div>

        {!funds.length ? (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-8 text-center">
            <PieChart className="w-12 h-12 mx-auto mb-3 text-[var(--text-muted)]" />
            <p className="text-[var(--text-muted)]">No mutual fund holdings found. Add MF investments to see overlap analysis.</p>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-1">Diversification Score</p>
                <p className={`text-2xl font-bold ${scoreColor}`}>{summary.diversification_score}<span className="text-sm">/100</span></p>
              </div>
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-1">Equity Funds</p>
                <p className="text-2xl font-bold">{summary.equity_funds}</p>
                {summary.debt_funds > 0 && <p className="text-xs text-[var(--text-muted)]">+ {summary.debt_funds} debt (no overlap)</p>}
              </div>
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-1">Overlapping Stocks</p>
                <p className="text-2xl font-bold">{summary.overlapping_stocks}</p>
              </div>
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-1">High Overlap (3+ funds)</p>
                <p className="text-2xl font-bold text-red-400">{summary.high_overlap_stocks}</p>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`rounded-lg p-4 mb-6 flex items-start gap-3 ${summary.diversification_score >= 70 ? 'bg-green-500/10 border border-green-500/20' : summary.diversification_score >= 40 ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
              {summary.diversification_score >= 70 ? <CheckCircle className="w-5 h-5 text-green-400 shrink-0 mt-0.5" /> : <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />}
              <div>
                <p className="text-sm font-medium">{summary.recommendation}</p>
                <p className="text-xs text-[var(--text-muted)] mt-1">Debt/liquid funds are excluded from overlap analysis as they don't hold equities.</p>
              </div>
            </div>

            {/* Fund List */}
            <h2 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Your Funds</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
              {funds.map(f => (
                <div key={f.symbol} className={`bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 ${f.category === 'debt' ? 'opacity-60' : ''}`}>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <p className="text-sm font-medium leading-tight line-clamp-2">{f.name}</p>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap ${CAT_COLORS[f.category] || CAT_COLORS.equity}`}>
                      {CAT_LABELS[f.category] || f.category}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                    <span>₹{fmt(f.value)}</span>
                    <span>{f.category === 'debt' ? 'No equity holdings' : `${f.stock_count} top stocks`}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Overlap Section */}
            {overlaps.length > 0 && (
              <>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider">Stock Overlap</h2>
                  <div className="flex gap-1 bg-[var(--bg-secondary)] rounded-lg p-0.5">
                    {['matrix', 'list'].map(v => (
                      <button key={v} onClick={() => setView(v)} className={`px-3 py-1 text-xs rounded-md ${view === v ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-muted)]'}`}>
                        {v === 'matrix' ? 'Heatmap' : 'List'}
                      </button>
                    ))}
                  </div>
                </div>

                {view === 'matrix' && matrix.stocks?.length > 0 ? (
                  <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6 overflow-x-auto">
                    <p className="text-xs text-[var(--text-muted)] mb-3">Each cell shows the stock's weight (%) in that fund. Darker = higher allocation.</p>
                    <table className="w-full text-xs">
                      <thead>
                        <tr>
                          <th className="text-left p-2 text-[var(--text-muted)] font-medium sticky left-0 bg-[var(--bg-secondary)]">Fund</th>
                          {matrix.stocks.map(s => (
                            <th key={s} className="p-2 text-center text-[var(--text-muted)] font-medium min-w-[70px]">{s}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {matrix.data?.map(row => (
                          <tr key={row.fund} className="border-t border-[var(--border)]">
                            <td className="p-2 font-medium sticky left-0 bg-[var(--bg-secondary)] max-w-[150px] truncate" title={row.fund_name}>{row.fund}</td>
                            {matrix.stocks.map(s => {
                              const w = row.weights[s] || 0;
                              const opacity = w > 0 ? Math.min(0.2 + (w / 12) * 0.8, 1) : 0;
                              return (
                                <td key={s} className="p-2 text-center">
                                  {w > 0 ? (
                                    <span className="inline-block px-2 py-1 rounded" style={{ backgroundColor: `rgba(59, 130, 246, ${opacity})` }}>
                                      {w}%
                                    </span>
                                  ) : (
                                    <span className="text-[var(--text-muted)]">—</span>
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : view === 'list' ? (
                  <div className="space-y-3 mb-6">
                    {overlaps.map(o => (
                      <div key={o.stock} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{o.stock}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full ${o.risk_level === 'High' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                              {o.fund_count} funds · {o.risk_level}
                            </span>
                          </div>
                          <span className="text-xs text-[var(--text-muted)]">Total: {o.total_exposure}%</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {o.funds.map((f, i) => (
                            <span key={i} className="text-xs bg-[var(--bg-primary)] px-2 py-1 rounded">
                              {f.fund_symbol} <span className="text-[var(--text-muted)]">({f.weight}%)</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </>
            )}

            {overlaps.length === 0 && equityFunds.length > 0 && (
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-6 text-center">
                <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <p className="text-sm">No stock overlap detected across your equity funds. Great diversification!</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
