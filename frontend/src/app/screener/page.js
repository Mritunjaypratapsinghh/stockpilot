'use client';
import { useState, useEffect } from 'react';
import { Filter, Search, TrendingUp, TrendingDown, Loader2 } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function ScreenerPage() {
  const [screens, setScreens] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeScreen, setActiveScreen] = useState(null);
  const [showCustom, setShowCustom] = useState(false);
  const [filters, setFilters] = useState({ pe_max: '', pb_max: '', roe_min: '', dividend_yield_min: '', market_cap_min: '' });

  useEffect(() => { loadScreens(); }, []);

  const loadScreens = async () => {
    try {
      const data = await api('/api/screener/screens');
      setScreens(data.screens || []);
    } catch (e) { console.error(e); }
  };

  const runScreen = async (screenId) => {
    setLoading(true);
    setActiveScreen(screenId);
    setShowCustom(false);
    try {
      const data = await api(`/api/screener/run/${screenId}`);
      setResults(data.results || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const runCustom = async () => {
    setLoading(true);
    setActiveScreen('custom');
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) params.append(k, v); });
    try {
      const data = await api(`/api/screener/custom?${params}`);
      setResults(data.results || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 1 }) || '—';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <h1 className="text-2xl font-bold mb-6">Stock Screener</h1>

        {/* Pre-built Screens */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
          {screens.map(s => (
            <button key={s.id} onClick={() => runScreen(s.id)} className={`p-3 rounded-lg text-left text-sm ${activeScreen === s.id ? 'bg-[#6366f1] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)] hover:border-[#6366f1]'}`}>
              <div className="font-medium">{s.name}</div>
              <div className={`text-xs ${activeScreen === s.id ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{s.description}</div>
            </button>
          ))}
          <button onClick={() => setShowCustom(!showCustom)} className={`p-3 rounded-lg text-left text-sm ${showCustom ? 'bg-[#6366f1] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)] hover:border-[#6366f1]'}`}>
            <div className="font-medium flex items-center gap-1"><Filter className="w-4 h-4" /> Custom</div>
            <div className={`text-xs ${showCustom ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>Your filters</div>
          </button>
        </div>

        {/* Custom Filters */}
        {showCustom && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">PE Max</label>
                <input type="number" value={filters.pe_max} onChange={e => setFilters({...filters, pe_max: e.target.value})} placeholder="e.g. 20" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded text-sm" />
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">PB Max</label>
                <input type="number" value={filters.pb_max} onChange={e => setFilters({...filters, pb_max: e.target.value})} placeholder="e.g. 3" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded text-sm" />
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">ROE Min %</label>
                <input type="number" value={filters.roe_min} onChange={e => setFilters({...filters, roe_min: e.target.value})} placeholder="e.g. 15" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded text-sm" />
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">Div Yield Min %</label>
                <input type="number" value={filters.dividend_yield_min} onChange={e => setFilters({...filters, dividend_yield_min: e.target.value})} placeholder="e.g. 2" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded text-sm" />
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">MCap Min (Cr)</label>
                <input type="number" value={filters.market_cap_min} onChange={e => setFilters({...filters, market_cap_min: e.target.value})} placeholder="e.g. 10000" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded text-sm" />
              </div>
            </div>
            <button onClick={runCustom} className="px-4 py-2 bg-[#6366f1] text-white rounded text-sm font-medium">Run Screen</button>
          </div>
        )}

        {/* Results */}
        {loading ? (
          <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-[#6366f1]" /></div>
        ) : results.length > 0 ? (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                  <th className="text-left px-4 py-3">Stock</th>
                  <th className="text-right px-4 py-3">Price</th>
                  <th className="text-right px-4 py-3">MCap (Cr)</th>
                  <th className="text-right px-4 py-3">PE</th>
                  <th className="text-right px-4 py-3">PB</th>
                  <th className="text-right px-4 py-3">ROE %</th>
                  <th className="text-right px-4 py-3">Div %</th>
                  <th className="text-right px-4 py-3">52W</th>
                </tr>
              </thead>
              <tbody>
                {results.map((s, i) => (
                  <tr key={i} className="border-b border-[var(--border)] hover:bg-[var(--bg-hover)]">
                    <td className="px-4 py-3">
                      <a href={`/stock?s=${s.symbol}`} className="hover:text-[#6366f1]">
                        <div className="font-medium">{s.symbol}</div>
                        <div className="text-xs text-[var(--text-muted)] truncate max-w-[150px]">{s.name}</div>
                      </a>
                    </td>
                    <td className="px-4 py-3 text-right">₹{fmt(s.price)}</td>
                    <td className="px-4 py-3 text-right">{fmt(s.market_cap)}</td>
                    <td className="px-4 py-3 text-right">{fmt(s.pe)}</td>
                    <td className="px-4 py-3 text-right">{fmt(s.pb)}</td>
                    <td className="px-4 py-3 text-right">{fmt(s.roe)}</td>
                    <td className="px-4 py-3 text-right">{fmt(s.dividend_yield)}</td>
                    <td className="px-4 py-3 text-right">
                      <span className={s.change_52w >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}>{s.change_52w >= 0 ? '+' : ''}{fmt(s.change_52w)}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : activeScreen && (
          <div className="text-center py-12 text-[var(--text-muted)]">No stocks match the criteria</div>
        )}
      </main>
    </div>
  );
}
