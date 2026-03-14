'use client';
import { useState, useEffect } from 'react';
import { TrendingUp, Wallet, ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import { getPortfolio, getHoldings, getIndices, api } from '../lib/api';
import Link from 'next/link';

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [indices, setIndices] = useState({});
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const [insights, setInsights] = useState([]);
  const [healthScore, setHealthScore] = useState(null);
  const [earnings, setEarnings] = useState([]);

  useEffect(() => {
    const t = localStorage.getItem('token');
    setToken(t);
    if (t) {
      Promise.all([getPortfolio(), getHoldings(), getIndices().catch(() => ({}))])
        .then(([p, h, idx]) => { 
          setPortfolio(p); 
          setHoldings(h); 
          setIndices(idx); 
        })
        .finally(() => setLoading(false));
      api('/api/analytics/insights').then(d => setInsights(d?.insights || [])).catch(() => {});
      api('/api/analytics/health-score').then(d => setHealthScore(d)).catch(() => {});
      api('/api/portfolio/earnings-calendar').then(d => setEarnings(d?.earnings || [])).catch(() => {});
    } else {
      window.location.href = '/landing';
    }
  }, []);

  if (!token) {
    return null;
  }

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6">
        {/* Market Indices */}
        {Object.keys(indices).length > 0 && (
          <div className="flex gap-3 mb-6 overflow-x-auto pb-2">
            {Object.entries(indices).filter(([, data]) => data).map(([name, data]) => (
              <div key={name} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-4 py-2.5 shrink-0">
                <div className="text-xs text-[var(--text-muted)] mb-0.5">{name}</div>
                <div className="text-base font-semibold tabular">{data.price?.toLocaleString('en-IN')}</div>
                <div className={`flex items-center gap-1 text-xs ${(data.change_pct || 0) >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                  {(data.change_pct || 0) >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  {Math.abs(data.change_pct || 0).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">
          <SummaryCard label="Current Value" value={`₹${fmt(portfolio?.current_value)}`} loading={loading} />
          <SummaryCard label="Invested" value={`₹${fmt(portfolio?.total_investment)}`} loading={loading} />
          <SummaryCard 
            label="Total P&L" 
            value={`${portfolio?.total_pnl >= 0 ? '+' : ''}₹${fmt(portfolio?.total_pnl)}`}
            sub={`${portfolio?.total_pnl_pct >= 0 ? '+' : ''}${portfolio?.total_pnl_pct?.toFixed(2)}%`}
            positive={portfolio?.total_pnl >= 0}
            loading={loading}
          />
          <SummaryCard 
            label="Today's P&L" 
            value={`${(portfolio?.day_pnl || 0) >= 0 ? '+' : ''}₹${fmt(portfolio?.day_pnl || 0)}`}
            sub={`${(portfolio?.day_pnl_pct || 0) >= 0 ? '+' : ''}${(portfolio?.day_pnl_pct || 0).toFixed(2)}%`}
            positive={(portfolio?.day_pnl || 0) >= 0}
            loading={loading}
          />
        </div>

        {/* AI Insights + Health Score + Earnings */}
        {(insights.length > 0 || healthScore || earnings.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
            {/* AI Insights */}
            {insights.length > 0 && (
              <div key="insights" className="lg:col-span-2">
                <div className="text-sm font-medium text-[var(--text-muted)] uppercase mb-3">🤖 AI Insights</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {insights.map((ins, i) => (
                    <div key={i} className={`border rounded-lg p-4 ${ins.type === 'warning' ? 'bg-[#ef4444]/5 border-[#ef4444]/20' : ins.type === 'opportunity' ? 'bg-[#10b981]/5 border-[#10b981]/20' : ins.type === 'tip' ? 'bg-[#f59e0b]/5 border-[#f59e0b]/20' : 'bg-[var(--bg-secondary)] border-[var(--border)]'}`}>
                      <div className="flex items-start gap-2">
                        <span className="text-lg">{ins.icon}</span>
                        <div>
                          <div className="font-medium text-sm">{ins.title}</div>
                          <div className="text-sm text-[var(--text-secondary)] mt-1">{ins.body}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sidebar: Health Score + Earnings */}
            <div key="sidebar" className="space-y-4">
              {healthScore && (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-sm font-medium text-[var(--text-muted)] uppercase mb-3">🏥 Portfolio Health</div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`text-3xl font-bold ${healthScore.score >= 80 ? 'text-[#10b981]' : healthScore.score >= 60 ? 'text-[#f59e0b]' : 'text-[#ef4444]'}`}>{healthScore.score}</div>
                    <div className={`text-lg font-bold px-2 py-0.5 rounded ${healthScore.grade === 'A' ? 'bg-[#10b981]/10 text-[#10b981]' : healthScore.grade === 'B' ? 'bg-[#f59e0b]/10 text-[#f59e0b]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>Grade {healthScore.grade}</div>
                  </div>
                  {healthScore.factors?.map((f, i) => (
                    <div key={i} className="flex justify-between text-xs py-1">
                      <span className="text-[var(--text-muted)]">{f.name}</span>
                      <span className={f.score >= f.max * 0.8 ? 'text-[#10b981]' : f.score >= f.max * 0.5 ? 'text-[#f59e0b]' : 'text-[#ef4444]'}>{f.score}/{f.max}</span>
                    </div>
                  ))}
                </div>
              )}

              {earnings.length > 0 && (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-sm font-medium text-[var(--text-muted)] uppercase mb-3">📅 Upcoming Earnings</div>
                  {earnings.slice(0, 5).map((e, i) => (
                    <div key={i} className="flex justify-between text-sm py-1.5 border-b border-[var(--border)] last:border-0">
                      <span className="font-medium">{e.symbol}</span>
                      <span className="text-[var(--text-muted)]">{e.date_str}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Holdings Table */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg">
          <div className="px-4 md:px-6 py-4 border-b border-[var(--border)] flex items-center justify-between">
            <h2 className="font-semibold text-base md:text-lg">Holdings</h2>
            <Link href="/portfolio" className="text-sm text-[var(--accent)] hover:text-[#5558e3]">View All →</Link>
          </div>
          
          {loading ? (
            <LoadingSkeleton rows={5} />
          ) : holdings.length === 0 ? (
            <EmptyState icon={Wallet} message="No holdings yet" action={{ href: '/portfolio', label: 'Add your first stock' }} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px]">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                    <th className="text-left px-4 md:px-6 py-3 font-medium">Stock</th>
                    <th className="text-right px-4 md:px-6 py-3 font-medium">Qty</th>
                    <th className="text-right px-4 md:px-6 py-3 font-medium hidden sm:table-cell">Avg Price</th>
                    <th className="text-right px-4 md:px-6 py-3 font-medium">LTP</th>
                    <th className="text-right px-4 md:px-6 py-3 font-medium hidden md:table-cell">Current Value</th>
                    <th className="text-right px-4 md:px-6 py-3 font-medium">P&L</th>
                    <th className="text-right px-4 md:px-6 py-3 font-medium hidden lg:table-cell">Day Change</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.slice(0, 10).map((h) => (
                    <tr key={h._id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
                      <td className="px-4 md:px-6 py-3 md:py-4">
                        <div className="flex items-center gap-2 md:gap-3">
                          <div className={`w-8 h-8 md:w-10 md:h-10 rounded-lg flex items-center justify-center text-xs md:text-sm font-semibold ${h.pnl >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>
                            {h.symbol?.slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium text-sm md:text-base">{h.symbol}</div>
                            <div className="text-xs text-[var(--text-muted)]">{h.holding_type}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 md:px-6 py-3 md:py-4 text-right tabular text-sm">{parseFloat(h.quantity?.toFixed(4))}</td>
                      <td className="px-4 md:px-6 py-3 md:py-4 text-right tabular text-sm hidden sm:table-cell"><span className="privacy-mask">₹{h.avg_price?.toFixed(2)}</span></td>
                      <td className="px-4 md:px-6 py-3 md:py-4 text-right tabular text-sm"><span className="privacy-mask">₹{h.current_price?.toFixed(2)}</span></td>
                      <td className="px-4 md:px-6 py-3 md:py-4 text-right tabular font-medium text-sm hidden md:table-cell"><span className="privacy-mask">₹{fmt(h.current_value)}</span></td>
                      <td className="px-4 md:px-6 py-3 md:py-4 text-right">
                        <div className={`tabular font-medium text-sm privacy-mask ${h.pnl >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                          {h.pnl >= 0 ? '+' : ''}₹{fmt(h.pnl)}
                        </div>
                        <div className={`text-xs tabular ${h.pnl >= 0 ? 'text-[#10b981]/70' : 'text-[#ef4444]/70'}`}>
                          {h.pnl_pct >= 0 ? '+' : ''}{h.pnl_pct?.toFixed(2)}%
                        </div>
                      </td>
                      <td className="px-4 md:px-6 py-3 md:py-4 text-right hidden lg:table-cell">
                        <span className={`inline-block px-2 py-1 rounded text-sm tabular font-medium ${(h.day_change_pct || 0) >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>
                          {(h.day_change_pct || 0) >= 0 ? '+' : ''}{(h.day_change_pct || 0).toFixed(2)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function SummaryCard({ label, value, sub, positive, loading }) {
  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-5">
      <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1 md:mb-2">{label}</div>
      {loading ? (
        <div className="h-6 md:h-8 w-20 md:w-32 bg-[var(--border)] rounded animate-pulse" />
      ) : (
        <>
          <div className={`text-lg md:text-2xl font-semibold tabular privacy-mask ${sub !== undefined ? (positive ? 'text-[#10b981]' : 'text-[#ef4444]') : ''}`}>{value}</div>
          {sub && <div className={`text-xs md:text-sm tabular privacy-mask ${positive ? 'text-[#10b981]/70' : 'text-[#ef4444]/70'}`}>{sub}</div>}
        </>
      )}
    </div>
  );
}

function LoadingSkeleton({ rows }) {
  return (
    <div className="p-6 space-y-4">
      {[...Array(rows)].map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          <div className="w-10 h-10 bg-[var(--border)] rounded-lg animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-24 bg-[var(--border)] rounded animate-pulse" />
            <div className="h-3 w-16 bg-[var(--border)] rounded animate-pulse" />
          </div>
          <div className="h-4 w-20 bg-[var(--border)] rounded animate-pulse" />
          <div className="h-4 w-20 bg-[var(--border)] rounded animate-pulse" />
          <div className="h-4 w-24 bg-[var(--border)] rounded animate-pulse" />
        </div>
      ))}
    </div>
  );
}

function EmptyState({ icon: Icon, message, action }) {
  return (
    <div className="p-12 text-center">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--border)] flex items-center justify-center">
        <Icon className="w-8 h-8 text-[var(--text-muted)]" />
      </div>
      <div className="text-[var(--text-muted)] mb-2">{message}</div>
      {action && <Link href={action.href} className="text-[var(--accent)] hover:text-[#5558e3]">{action.label} →</Link>}
    </div>
  );
}
