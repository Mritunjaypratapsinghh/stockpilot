'use client';
import { useState, useEffect, useCallback, useRef, lazy, Suspense } from 'react';
import { TrendingUp, Wallet, ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import { getPortfolio, getHoldings, getIndices, getSnapshots, api } from '../lib/api';
import Link from 'next/link';
import dynamic from 'next/dynamic';

const AreaChart = dynamic(() => import('recharts').then(mod => mod.AreaChart), { ssr: false });
const Area = dynamic(() => import('recharts').then(mod => mod.Area), { ssr: false });
const XAxis = dynamic(() => import('recharts').then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then(mod => mod.YAxis), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then(mod => mod.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [indices, setIndices] = useState({});
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const [insights, setInsights] = useState([]);
  const [healthScore, setHealthScore] = useState(null);
  const [earnings, setEarnings] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [chartRange, setChartRange] = useState('3M');
  const [chartLoading, setChartLoading] = useState(false);
  const chartAbortRef = useRef(null);

  const handleRangeChange = useCallback((range) => {
    if (range === chartRange || chartLoading) return;
    if (chartAbortRef.current) chartAbortRef.current.abort();
    chartAbortRef.current = new AbortController();
    setChartRange(range);
    setChartLoading(true);
    getSnapshots(range)
      .then(d => setSnapshots(d?.snapshots || []))
      .catch(() => {})
      .finally(() => setChartLoading(false));
  }, [chartRange, chartLoading]);

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
      getSnapshots('3M').then(d => setSnapshots(d?.snapshots || [])).catch(() => {});
    } else {
      window.location.href = '/landing';
    }
  }, []);

  if (!token) {
    return null;
  }

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  // Onboarding for first-time users
  if (!loading && holdings.length === 0) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Navbar />
        <main className="p-4 md:p-6 max-w-2xl mx-auto">
          <div className="text-center py-12">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-[var(--accent)]/10 flex items-center justify-center">
              <TrendingUp className="w-10 h-10 text-[var(--accent)]" />
            </div>
            <h1 className="text-2xl md:text-3xl font-bold mb-3">Welcome to StockPilot</h1>
            <p className="text-[var(--text-muted)] mb-8 max-w-md mx-auto">Your portfolio intelligence platform. Start by adding your holdings to unlock AI signals, tax insights, and more.</p>
          </div>
          <div className="space-y-4">
            <Link href="/portfolio" className="flex items-center gap-4 p-5 bg-[var(--accent)]/10 border-2 border-[var(--accent)]/30 rounded-xl hover:bg-[var(--accent)]/20 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-[var(--accent)] flex items-center justify-center shrink-0"><ArrowUpRight className="w-6 h-6 text-white" /></div>
              <div><div className="font-semibold">Import from Groww</div><div className="text-sm text-[var(--text-muted)]">Upload your Groww XLSX export to import all holdings instantly</div></div>
            </Link>
            <Link href="/portfolio" className="flex items-center gap-4 p-5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors">
              <div className="w-12 h-12 rounded-lg bg-[var(--bg-tertiary)] flex items-center justify-center shrink-0"><Wallet className="w-6 h-6 text-[var(--text-muted)]" /></div>
              <div><div className="font-semibold">Add Manually</div><div className="text-sm text-[var(--text-muted)]">Add stocks and mutual funds one by one with buy price and quantity</div></div>
            </Link>
          </div>
          <div className="mt-10 grid grid-cols-3 gap-4 text-center">
            <div className="p-4"><div className="text-2xl mb-1">🤖</div><div className="text-xs text-[var(--text-muted)]">AI Signals & Chat</div></div>
            <div className="p-4"><div className="text-2xl mb-1">📊</div><div className="text-xs text-[var(--text-muted)]">Tax Harvesting</div></div>
            <div className="p-4"><div className="text-2xl mb-1">🔔</div><div className="text-xs text-[var(--text-muted)]">Smart Alerts</div></div>
          </div>
        </main>
      </div>
    );
  }

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

        {/* Portfolio Growth Chart */}
        {snapshots.length > 1 && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm font-medium text-[var(--text-muted)] uppercase">📈 Portfolio Growth</div>
              <div className="flex gap-1">
                {['1W', '1M', '3M', '6M', '1Y', 'ALL'].map(r => (
                  <button key={r} onClick={() => handleRangeChange(r)} disabled={chartLoading}
                    className={`px-2 py-1 text-xs rounded ${chartRange === r ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-primary)] text-[var(--text-muted)] hover:bg-[var(--border)]'} ${chartLoading ? 'opacity-50 cursor-not-allowed' : ''}`}>{r}</button>
                ))}
              </div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={snapshots}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={snapshots[snapshots.length-1]?.pnl >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={snapshots[snapshots.length-1]?.pnl >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{fontSize: 10}} tickFormatter={d => d?.slice(5)} stroke="var(--text-muted)" />
                <YAxis tick={{fontSize: 10}} tickFormatter={v => `₹${(v/100000).toFixed(1)}L`} stroke="var(--text-muted)" width={50} />
                <Tooltip content={({active, payload}) => active && payload?.[0] ? (
                  <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded p-2 text-xs">
                    <div className="font-medium">{payload[0].payload.date}</div>
                    <div>Value: ₹{payload[0].payload.value?.toLocaleString('en-IN')}</div>
                    <div>Invested: ₹{payload[0].payload.invested?.toLocaleString('en-IN')}</div>
                    <div className={payload[0].payload.pnl >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}>P&L: {payload[0].payload.pnl >= 0 ? '+' : ''}₹{payload[0].payload.pnl?.toLocaleString('en-IN')} ({payload[0].payload.pnl_pct}%)</div>
                  </div>
                ) : null} />
                <Area type="monotone" dataKey="value" stroke={snapshots[snapshots.length-1]?.pnl >= 0 ? '#10b981' : '#ef4444'} fill="url(#colorValue)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* AI Insights + Health Score + Earnings */}
        {(insights.length > 0 || healthScore || earnings.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
            {insights.length > 0 ? (
              <div className="lg:col-span-2">
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
            ) : (
              <div className="lg:col-span-2" />
            )}

            <div className="space-y-4">
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
                  {holdings.slice(0, 10).map((h, idx) => (
                    <tr key={h._id || h.id || idx} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
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
