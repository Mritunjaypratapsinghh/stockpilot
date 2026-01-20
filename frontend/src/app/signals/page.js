'use client';
import { useState, useEffect } from 'react';
import { Zap, TrendingUp, TrendingDown, RefreshCw, Target } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function SignalsPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [ipos, setIpos] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadSignals = async () => { setLoading(true); try { const data = await api('/api/research/advisor/run', { method: 'POST' }); setRecommendations(data.portfolio || []); setIpos(data.ipos || []); } catch (e) {} setLoading(false); };
  useEffect(() => { loadSignals(); }, []);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-[#6366f1]/10 flex items-center justify-center"><Zap className="w-6 h-6 text-[#6366f1]" /></div>
            <div><h1 className="text-2xl font-bold">Smart Signals</h1><p className="text-[var(--text-muted)]">AI-powered recommendations</p></div>
          </div>
          <button onClick={loadSignals} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] text-white rounded-lg text-sm font-medium hover:bg-[#5558e3] disabled:opacity-50"><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Analyze</button>
        </div>

        {loading ? (
          <div className="py-20 text-center"><div className="flex justify-center gap-1 mb-4">{[0, 1, 2].map(i => <div key={i} className="w-3 h-3 bg-[#6366f1] rounded-full animate-pulse" style={{ animationDelay: `${i * 150}ms` }} />)}</div><p className="text-[var(--text-muted)]">Analyzing portfolio...</p></div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="col-span-2">
              <h2 className="text-sm font-medium text-[var(--text-muted)] uppercase mb-4">Portfolio Actions</h2>
              {recommendations.length === 0 ? (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center"><Target className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" /><div className="text-[var(--text-muted)]">No actionable signals</div></div>
              ) : (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase"><th className="text-left px-5 py-3 font-medium">Stock</th><th className="text-left px-5 py-3 font-medium">Action</th><th className="text-right px-5 py-3 font-medium">Price</th><th className="text-right px-5 py-3 font-medium">P&L</th><th className="text-left px-5 py-3 font-medium">Reason</th></tr></thead>
                    <tbody>
                      {recommendations.map((r, i) => {
                        const isBuy = r.action?.includes('BUY'), isSell = r.action?.includes('SELL') || r.action === 'EXIT';
                        return (
                          <tr key={i} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
                            <td className="px-5 py-4"><div className="flex items-center gap-3"><div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isBuy ? 'bg-[#10b981]/10' : isSell ? 'bg-[#ef4444]/10' : 'bg-[var(--border)]'}`}>{isBuy ? <TrendingUp className="w-5 h-5 text-[#10b981]" /> : isSell ? <TrendingDown className="w-5 h-5 text-[#ef4444]" /> : <Target className="w-5 h-5 text-[var(--text-muted)]" />}</div><div><div className="font-medium">{r.symbol}</div><div className="text-sm text-[var(--text-muted)]">Avg: ₹{r.avg_price?.toFixed(0)}</div></div></div></td>
                            <td className="px-5 py-4"><span className={`inline-block px-2 py-1 rounded text-sm font-medium ${isBuy ? 'bg-[#10b981]/10 text-[#10b981]' : isSell ? 'bg-[#ef4444]/10 text-[#ef4444]' : 'bg-[var(--border)] text-[var(--text-muted)]'}`}>{r.action}</span></td>
                            <td className="px-5 py-4 text-right tabular font-medium">₹{r.current_price?.toFixed(2)}</td>
                            <td className="px-5 py-4 text-right"><span className={`tabular font-medium ${r.pnl_pct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{r.pnl_pct >= 0 ? '+' : ''}{r.pnl_pct?.toFixed(1)}%</span></td>
                            <td className="px-5 py-4 text-[var(--text-secondary)] text-sm max-w-xs truncate">{r.reasons?.[0]}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div>
              <h2 className="text-sm font-medium text-[var(--text-muted)] uppercase mb-4">IPO Recommendations</h2>
              <div className="space-y-3">
                {ipos.filter(ipo => ipo.action).length === 0 ? <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-8 text-center text-[var(--text-muted)]">No IPO recommendations</div> : ipos.filter(ipo => ipo.action).map((ipo, i) => (
                  <div key={i} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2"><div className="font-medium">{ipo.name}</div><span className={`text-xs font-medium px-2 py-1 rounded ${ipo.action === 'APPLY' ? 'bg-[#10b981]/10 text-[#10b981]' : ipo.action === 'AVOID' ? 'bg-[#ef4444]/10 text-[#ef4444]' : 'bg-[#eab308]/10 text-[#eab308]'}`}>{ipo.action}</span></div>
                    <div className="text-sm text-[var(--text-muted)] mb-2">{ipo.price_band} • GMP: ₹{ipo.gmp} ({ipo.gmp_pct?.toFixed(0)}%)</div>
                    <div className="text-sm text-[var(--text-secondary)]">{ipo.reasons?.[0]}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        <p className="mt-8 text-sm text-[var(--text-muted)] text-center">⚠️ Not financial advice. Do your own research.</p>
      </main>
    </div>
  );
}
