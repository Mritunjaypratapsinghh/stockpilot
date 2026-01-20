'use client';
import { useState, useEffect } from 'react';
import { TrendingUp, Wallet, ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import { getPortfolio, getHoldings, getIndices } from '../lib/api';
import Link from 'next/link';

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [indices, setIndices] = useState({});
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const t = localStorage.getItem('token');
    setToken(t);
    if (t) {
      Promise.all([getPortfolio(), getHoldings(), getIndices().catch(() => ({}))])
        .then(([p, h, idx]) => { setPortfolio(p); setHoldings(h); setIndices(idx); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  if (!token) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-[#6366f1] flex items-center justify-center">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold mb-3">StockPilot</h1>
          <p className="text-[var(--text-secondary)] mb-8">Track your portfolio with real-time analytics</p>
          <a href="/login" className="inline-flex items-center gap-2 px-6 py-3 bg-[#6366f1] text-white rounded-lg font-medium hover:bg-[#5558e3]">
            Get Started <ArrowRight className="w-5 h-5" />
          </a>
        </div>
      </div>
    );
  }

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        {/* Market Indices */}
        {Object.keys(indices).length > 0 && (
          <div className="flex gap-4 mb-6">
            {Object.entries(indices).map(([name, data]) => (
              <div key={name} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-5 py-3">
                <div className="text-sm text-[var(--text-muted)] mb-1">{name}</div>
                <div className="text-lg font-semibold tabular">{data.price?.toLocaleString('en-IN')}</div>
                <div className={`flex items-center gap-1 text-sm ${data.change_pct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                  {data.change_pct >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  {Math.abs(data.change_pct || 0).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
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

        {/* Holdings Table */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg">
          <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between">
            <h2 className="font-semibold text-lg">Holdings</h2>
            <Link href="/portfolio" className="text-sm text-[#6366f1] hover:text-[#5558e3]">View All →</Link>
          </div>
          
          {loading ? (
            <LoadingSkeleton rows={5} />
          ) : holdings.length === 0 ? (
            <EmptyState icon={Wallet} message="No holdings yet" action={{ href: '/portfolio', label: 'Add your first stock' }} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                    <th className="text-left px-6 py-3 font-medium">Stock</th>
                    <th className="text-right px-6 py-3 font-medium">Qty</th>
                    <th className="text-right px-6 py-3 font-medium">Avg Price</th>
                    <th className="text-right px-6 py-3 font-medium">LTP</th>
                    <th className="text-right px-6 py-3 font-medium">Current Value</th>
                    <th className="text-right px-6 py-3 font-medium">P&L</th>
                    <th className="text-right px-6 py-3 font-medium">Day Change</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.slice(0, 10).map((h) => (
                    <tr key={h._id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-semibold ${h.pnl >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>
                            {h.symbol?.slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium">{h.symbol}</div>
                            <div className="text-sm text-[var(--text-muted)]">{h.holding_type}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right tabular">{h.quantity}</td>
                      <td className="px-6 py-4 text-right tabular">₹{h.avg_price?.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right tabular">₹{h.current_price?.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right tabular font-medium">₹{fmt(h.current_value)}</td>
                      <td className="px-6 py-4 text-right">
                        <div className={`tabular font-medium ${h.pnl >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                          {h.pnl >= 0 ? '+' : ''}₹{fmt(h.pnl)}
                        </div>
                        <div className={`text-sm tabular ${h.pnl >= 0 ? 'text-[#10b981]/70' : 'text-[#ef4444]/70'}`}>
                          {h.pnl_pct >= 0 ? '+' : ''}{h.pnl_pct?.toFixed(2)}%
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
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
    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
      <div className="text-sm text-[var(--text-muted)] mb-2">{label}</div>
      {loading ? (
        <div className="h-8 w-32 bg-[var(--border)] rounded animate-pulse" />
      ) : (
        <>
          <div className={`text-2xl font-semibold tabular ${sub !== undefined ? (positive ? 'text-[#10b981]' : 'text-[#ef4444]') : ''}`}>{value}</div>
          {sub && <div className={`text-sm tabular ${positive ? 'text-[#10b981]/70' : 'text-[#ef4444]/70'}`}>{sub}</div>}
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
      {action && <Link href={action.href} className="text-[#6366f1] hover:text-[#5558e3]">{action.label} →</Link>}
    </div>
  );
}
