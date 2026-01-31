'use client';
import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function MarketPage() {
  const [indices, setIndices] = useState({});
  const [summary, setSummary] = useState(null);
  const [fiiDii, setFiiDii] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    const [idx, sum, fii] = await Promise.all([api('/api/market/indices').catch(() => ({})), api('/api/market/market-summary').catch(() => null), api('/api/market/fii-dii').catch(() => null)]);
    setIndices(idx); setSummary(sum); setFiiDii(fii); setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Market Overview</h1>
          <button onClick={loadData} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-sm hover:bg-[var(--bg-hover)]"><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh</button>
        </div>

        {/* Indices */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          {loading ? [...Array(3)].map((_, i) => <div key={i} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5 h-28 animate-pulse" />) : Object.entries(indices).map(([name, data]) => (
            <div key={name} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
              <div className="flex items-center justify-between mb-2"><span className="text-[var(--text-muted)]">{name}</span>{data.change_pct >= 0 ? <TrendingUp className="w-5 h-5 text-[#10b981]" /> : <TrendingDown className="w-5 h-5 text-[#ef4444]" />}</div>
              <div className="text-2xl font-semibold tabular mb-1">{data.price?.toLocaleString('en-IN')}</div>
              <div className={`flex items-center gap-1 text-sm ${data.change_pct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{data.change_pct >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}{data.change >= 0 ? '+' : ''}{data.change?.toFixed(2)} ({data.change_pct?.toFixed(2)}%)</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Movers */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-[var(--border)] font-semibold">Top Movers</div>
            {summary?.top_movers?.length ? (
              <table className="w-full">
                <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase"><th className="text-left px-5 py-3 font-medium">Stock</th><th className="text-right px-5 py-3 font-medium">Price</th><th className="text-right px-5 py-3 font-medium">Change</th></tr></thead>
                <tbody>{summary.top_movers.map(s => <tr key={s.symbol} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]"><td className="px-5 py-3"><div className="flex items-center gap-3"><div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-semibold ${s.change_pct >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{s.symbol.slice(0, 2)}</div><span className="font-medium">{s.symbol}</span></div></td><td className="px-5 py-3 text-right tabular font-medium">₹{s.price?.toLocaleString('en-IN')}</td><td className="px-5 py-3 text-right"><span className={`inline-block px-2 py-1 rounded text-sm tabular font-medium ${s.change_pct >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{s.change_pct >= 0 ? '+' : ''}{s.change_pct?.toFixed(2)}%</span></td></tr>)}</tbody>
              </table>
            ) : <div className="p-8 text-center text-[var(--text-muted)]">No data</div>}
          </div>

          {/* FII/DII */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-[var(--border)] font-semibold">FII / DII Activity</div>
            {fiiDii?.note ? <div className="p-8 text-center text-[var(--text-muted)]">{fiiDii.note}</div> : (
              <div className="p-5 space-y-4">
                <div className="bg-[var(--bg-primary)] rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3"><span className="font-medium">FII (Foreign)</span><span className={`text-xs px-2 py-1 rounded ${(fiiDii?.fii?.net || 0) >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{(fiiDii?.fii?.net || 0) >= 0 ? 'Net Buyer' : 'Net Seller'}</span></div>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-sm"><div><div className="text-[var(--text-muted)] text-xs mb-1">Buy</div><div className="text-[#10b981] font-medium tabular">₹{((fiiDii?.fii?.buy || 0) / 100).toFixed(0)} Cr</div></div><div><div className="text-[var(--text-muted)] text-xs mb-1">Sell</div><div className="text-[#ef4444] font-medium tabular">₹{((fiiDii?.fii?.sell || 0) / 100).toFixed(0)} Cr</div></div><div><div className="text-[var(--text-muted)] text-xs mb-1">Net</div><div className={`font-medium tabular ${(fiiDii?.fii?.net || 0) >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>₹{((fiiDii?.fii?.net || 0) / 100).toFixed(0)} Cr</div></div></div>
                </div>
                <div className="bg-[var(--bg-primary)] rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3"><span className="font-medium">DII (Domestic)</span><span className={`text-xs px-2 py-1 rounded ${(fiiDii?.dii?.net || 0) >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{(fiiDii?.dii?.net || 0) >= 0 ? 'Net Buyer' : 'Net Seller'}</span></div>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-sm"><div><div className="text-[var(--text-muted)] text-xs mb-1">Buy</div><div className="text-[#10b981] font-medium tabular">₹{((fiiDii?.dii?.buy || 0) / 100).toFixed(0)} Cr</div></div><div><div className="text-[var(--text-muted)] text-xs mb-1">Sell</div><div className="text-[#ef4444] font-medium tabular">₹{((fiiDii?.dii?.sell || 0) / 100).toFixed(0)} Cr</div></div><div><div className="text-[var(--text-muted)] text-xs mb-1">Net</div><div className={`font-medium tabular ${(fiiDii?.dii?.net || 0) >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>₹{((fiiDii?.dii?.net || 0) / 100).toFixed(0)} Cr</div></div></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
