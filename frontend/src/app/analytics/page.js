'use client';
import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, PieChart, AlertTriangle, Target } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState(null);
  const [returns, setReturns] = useState(null);
  const [drawdown, setDrawdown] = useState(null);
  const [sectorRisk, setSectorRisk] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [m, r, d, s] = await Promise.all([
        api('/api/analytics/metrics'),
        api('/api/analytics/returns'),
        api('/api/analytics/drawdown'),
        api('/api/analytics/sector-risk')
      ]);
      setMetrics(m);
      setReturns(r);
      setDrawdown(d);
      setSectorRisk(s);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-6">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <h1 className="text-2xl font-bold mb-6">Portfolio Analytics</h1>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Portfolio Beta</div>
            <div className="text-2xl font-semibold">{metrics?.metrics?.beta || '—'}</div>
            <div className="text-xs text-[var(--text-muted)]">{metrics?.metrics?.beta > 1 ? 'More volatile than market' : 'Less volatile than market'}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Volatility (Annual)</div>
            <div className="text-2xl font-semibold">{metrics?.metrics?.volatility_annual}%</div>
            <div className="text-xs text-[var(--text-muted)]">Standard deviation</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">CAGR</div>
            <div className={`text-2xl font-semibold ${returns?.cagr >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              {returns?.cagr >= 0 ? '+' : ''}{returns?.cagr}%
            </div>
            <div className="text-xs text-[var(--text-muted)]">{returns?.holding_period_years} years</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Risk Profile</div>
            <div className="text-xl font-semibold">{metrics?.risk_profile?.level}</div>
            <div className="text-xs text-[var(--text-muted)]">{metrics?.risk_profile?.description}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Returns Analysis */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <h3 className="font-medium mb-4 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-[#10b981]" /> Returns Analysis</h3>
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-[var(--border)]">
                <span className="text-[var(--text-muted)]">Invested</span>
                <span className="font-medium">₹{fmt(returns?.invested)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]">
                <span className="text-[var(--text-muted)]">Current Value</span>
                <span className="font-medium">₹{fmt(returns?.current_value)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]">
                <span className="text-[var(--text-muted)]">Absolute Return</span>
                <span className={`font-medium ${returns?.absolute_return >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                  {returns?.absolute_return >= 0 ? '+' : ''}₹{fmt(returns?.absolute_return)} ({returns?.absolute_return_pct}%)
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]">
                <span className="text-[var(--text-muted)]">CAGR</span>
                <span className={`font-medium ${returns?.cagr >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{returns?.cagr}%</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-[var(--text-muted)]">vs NIFTY 50 (5Y CAGR ~12.5%)</span>
                <span className={`font-medium ${returns?.benchmark_comparison?.outperformance >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                  {returns?.benchmark_comparison?.outperformance >= 0 ? '+' : ''}{returns?.benchmark_comparison?.outperformance}%
                </span>
              </div>
            </div>
          </div>

          {/* Drawdown Analysis */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <h3 className="font-medium mb-4 flex items-center gap-2"><TrendingDown className="w-5 h-5 text-[#ef4444]" /> Drawdown Analysis</h3>
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-[var(--text-muted)]">Current Drawdown</span>
                <span className="text-[#ef4444] font-medium">{drawdown?.portfolio_drawdown}%</span>
              </div>
              <div className="h-3 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                <div className="h-full bg-[#ef4444] rounded-full" style={{ width: `${Math.min(100, drawdown?.portfolio_drawdown || 0)}%` }} />
              </div>
            </div>
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Estimated Peak</span>
                <span>₹{fmt(drawdown?.estimated_peak)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Current Value</span>
                <span>₹{fmt(drawdown?.current_value)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Recovery Needed</span>
                <span className="text-[#f59e0b]">{drawdown?.recovery_needed}%</span>
              </div>
            </div>
            {drawdown?.holdings_in_drawdown?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[var(--border)]">
                <div className="text-sm text-[var(--text-muted)] mb-2">Top Losers ({drawdown?.total_holdings_down} stocks down)</div>
                {drawdown.holdings_in_drawdown.slice(0, 3).map((h, i) => (
                  <div key={i} className="flex justify-between text-sm py-1">
                    <span>{h.symbol}</span>
                    <span className="text-[#ef4444]">-{h.drawdown_pct}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Concentration Risk */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <h3 className="font-medium mb-4 flex items-center gap-2"><PieChart className="w-5 h-5 text-[var(--accent)]" /> Concentration Analysis</h3>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Top 5 Concentration</span>
                <span className={metrics?.metrics?.top_5_concentration > 70 ? 'text-[#ef4444]' : 'text-[#10b981]'}>{metrics?.metrics?.top_5_concentration}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Diversification</span>
                <span className={`px-2 py-0.5 rounded text-xs ${metrics?.metrics?.diversification === 'Good' ? 'bg-[#10b981]/10 text-[#10b981]' : metrics?.metrics?.diversification === 'Moderate' ? 'bg-[#f59e0b]/10 text-[#f59e0b]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>
                  {metrics?.metrics?.diversification}
                </span>
              </div>
            </div>
            <div className="text-sm text-[var(--text-muted)] mb-2">Top Holdings</div>
            {metrics?.top_holdings?.map((h, i) => (
              <div key={i} className="flex justify-between text-sm py-1">
                <span>{h.symbol}</span>
                <span>{h.weight}%</span>
              </div>
            ))}
          </div>

          {/* Sector Risk */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <h3 className="font-medium mb-4 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-[#f59e0b]" /> Sector Risk</h3>
            <div className="space-y-2 mb-4">
              {sectorRisk?.sectors?.slice(0, 5).map((s, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm">{s.sector}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${s.concentration_risk === 'High' ? 'bg-[#ef4444]' : s.concentration_risk === 'Moderate' ? 'bg-[#f59e0b]' : 'bg-[#10b981]'}`} style={{ width: `${s.weight}%` }} />
                    </div>
                    <span className="text-sm w-12 text-right">{s.weight}%</span>
                  </div>
                </div>
              ))}
            </div>
            {sectorRisk?.recommendations?.length > 0 && (
              <div className="bg-[#f59e0b]/10 rounded-lg p-3">
                <div className="text-sm font-medium text-[#f59e0b] mb-1">Recommendations</div>
                {sectorRisk.recommendations.map((r, i) => (
                  <div key={i} className="text-sm text-[var(--text-secondary)]">• {r}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
