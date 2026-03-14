'use client';
import { useState, useEffect } from 'react';
import { ArrowRightLeft, TrendingUp, TrendingDown, Loader2, BarChart3 } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function SimulatorPage() {
  const [holdings, setHoldings] = useState([]);
  const [sell, setSell] = useState('');
  const [buy, setBuy] = useState('');
  const [amount, setAmount] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api('/api/portfolio/holdings').then(d => {
      const list = Array.isArray(d) ? d : (d?.holdings || []);
      const eq = list.filter(h => h.holding_type !== 'MF');
      setHoldings(eq);
      if (eq.length) setSell(eq[0].symbol);
    }).catch(() => {});
  }, []);

  const simulate = async () => {
    if (!sell || !amount) return;
    setLoading(true);
    try {
      const r = await api('/api/analytics/simulate', {
        method: 'POST',
        body: JSON.stringify({ sell, buy, amount: parseFloat(amount) }),
      });
      setResult(r);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const MetricCard = ({ label, before, after, unit = '', lower }) => {
    const diff = after - before;
    const better = lower ? diff < 0 : diff > 0;
    return (
      <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
        <div className="text-sm text-[var(--text-muted)] mb-2">{label}</div>
        <div className="flex items-end justify-between">
          <div>
            <span className="text-[var(--text-muted)] text-xs">Before: </span>
            <span className="font-medium">{before?.toLocaleString()}{unit}</span>
          </div>
          <div className="text-right">
            <span className="text-[var(--text-muted)] text-xs">After: </span>
            <span className="font-bold">{after?.toLocaleString()}{unit}</span>
          </div>
        </div>
        {diff !== 0 && (
          <div className={`text-xs mt-2 font-medium ${better ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
            {diff > 0 ? '▲' : '▼'} {Math.abs(diff).toLocaleString()}{unit} {better ? '(better)' : '(worse)'}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6 max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
            <ArrowRightLeft className="w-6 h-6 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold">What-If Simulator</h1>
            <p className="text-[var(--text-muted)]">See the impact before you trade</p>
          </div>
        </div>

        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6 mb-6">
          {holdings.length === 0 ? (
            <div className="text-center py-8">
              <ArrowRightLeft className="w-10 h-10 mx-auto mb-3 text-[var(--text-muted)]" />
              <p className="text-[var(--text-muted)]">No equity holdings to simulate. Add stocks first.</p>
            </div>
          ) : (
          <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-sm text-[var(--text-muted)] mb-1 block">Sell</label>
              <select value={sell} onChange={e => setSell(e.target.value)} className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm">
                {holdings.map(h => (
                  <option key={h.symbol} value={h.symbol}>{h.symbol} (₹{(h.current_price || h.avg_price).toLocaleString()})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-[var(--text-muted)] mb-1 block">Buy (optional)</label>
              <input value={buy} onChange={e => setBuy(e.target.value.toUpperCase())} placeholder="e.g. HDFCBANK" className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-sm text-[var(--text-muted)] mb-1 block">Amount (₹)</label>
              <input type="number" value={amount} onChange={e => setAmount(e.target.value)} placeholder="50000" className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <button onClick={simulate} disabled={loading || !sell || !amount} className="w-full md:w-auto px-6 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:bg-[#5558e3] disabled:opacity-50 flex items-center justify-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />}
            Simulate
          </button>
          </>
          )}
        </div>

        {result && (
          <div>
            <h2 className="text-sm font-medium text-[var(--text-muted)] uppercase mb-4">Impact Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <MetricCard label="Concentration (HHI)" before={result.before.hhi} after={result.after.hhi} lower />
              <MetricCard label="# Stocks" before={result.before.stocks} after={result.after.stocks} />
              <MetricCard label="Top Sector %" before={result.before.top_sector_pct} after={result.after.top_sector_pct} unit="%" lower />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <div className="text-sm font-medium mb-3">Before — Sectors</div>
                {Object.entries(result.before.sectors || {}).sort((a, b) => b[1] - a[1]).map(([sec, pct]) => (
                  <div key={sec} className="flex justify-between text-sm py-1">
                    <span className="text-[var(--text-secondary)]">{sec}</span>
                    <span className="font-medium">{pct}%</span>
                  </div>
                ))}
              </div>
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <div className="text-sm font-medium mb-3">After — Sectors</div>
                {Object.entries(result.after.sectors || {}).sort((a, b) => b[1] - a[1]).map(([sec, pct]) => (
                  <div key={sec} className="flex justify-between text-sm py-1">
                    <span className="text-[var(--text-secondary)]">{sec}</span>
                    <span className={`font-medium ${pct > 30 ? 'text-[#ef4444]' : ''}`}>{pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
