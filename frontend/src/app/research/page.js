'use client';
import { useState, useRef } from 'react';
import { Search, Loader2 } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { getAnalysis, getNews, api } from '../../lib/api';

export default function ResearchPage() {
  const [symbol, setSymbol] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const searchTimeout = useRef(null);

  const searchSymbol = async (query) => {
    if (query.length < 2) { setSearchResults([]); return; }
    try {
      const results = await api(`/api/market/search?q=${query}`);
      setSearchResults(results.slice(0, 5));
      setShowDropdown(true);
    } catch { setSearchResults([]); }
  };

  const handleInput = (value) => {
    setSymbol(value.toUpperCase());
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => searchSymbol(value), 300);
  };

  const selectSymbol = (sym) => {
    setSymbol(sym);
    setShowDropdown(false);
    analyze(sym);
  };

  const analyze = async (sym) => {
    const s = sym || symbol;
    if (!s.trim()) return;
    setLoading(true);
    setShowDropdown(false);
    try {
      const [a, n] = await Promise.all([getAnalysis(s), getNews(s)]);
      setAnalysis(a);
      setNews(n.news || []);
    } catch {}
    setLoading(false);
  };

  const handleSubmit = (e) => { e.preventDefault(); analyze(); };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <h1 className="text-2xl font-bold mb-6">Stock Research</h1>

        <form onSubmit={handleSubmit} className="flex gap-3 mb-6 w-96">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input 
              value={symbol} 
              onChange={e => handleInput(e.target.value)} 
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              placeholder="Search stock (e.g. Reliance)" 
              className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]" 
              autoComplete="off"
            />
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {searchResults.map((s, i) => (
                  <button key={`${s.symbol}-${i}`} type="button" onClick={() => selectSymbol(s.symbol)} className="w-full px-4 py-3 text-left hover:bg-[var(--bg-tertiary)] flex justify-between items-center">
                    <span className="font-medium text-[var(--text-primary)]">{s.symbol}</span>
                    <span className="text-sm text-[var(--text-muted)] truncate ml-2">{s.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button type="submit" disabled={loading} className="px-6 py-2.5 bg-[var(--accent)] text-white rounded-lg font-medium hover:bg-[#5558e3] disabled:opacity-50">{loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Analyze'}</button>
        </form>

        {analysis && !analysis.error ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="col-span-2 space-y-4">
              {/* Header */}
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6 flex items-center justify-between">
                <div><h2 className="text-2xl font-bold mb-1">{analysis.symbol}</h2><span className={`inline-block px-3 py-1 rounded text-sm font-medium ${analysis.trend === 'BULLISH' ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{analysis.trend}</span></div>
                <div className="text-3xl font-bold tabular">₹{analysis.current_price}</div>
              </div>

              {/* Moving Averages */}
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-[var(--border)] font-semibold">Moving Averages</div>
                <table className="w-full">
                  <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase"><th className="text-left px-6 py-3 font-medium">Indicator</th><th className="text-right px-6 py-3 font-medium">Value</th><th className="text-right px-6 py-3 font-medium">Signal</th></tr></thead>
                  <tbody>
                    <tr className="border-b border-[var(--border)]"><td className="px-6 py-3 font-medium">SMA 20</td><td className="px-6 py-3 text-right tabular">₹{analysis.sma_20}</td><td className="px-6 py-3 text-right"><span className={`inline-block px-2 py-0.5 rounded text-sm ${analysis.current_price > analysis.sma_20 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{analysis.current_price > analysis.sma_20 ? 'Above' : 'Below'}</span></td></tr>
                    {analysis.sma_50 && <tr className="border-b border-[var(--border)]"><td className="px-6 py-3 font-medium">SMA 50</td><td className="px-6 py-3 text-right tabular">₹{analysis.sma_50}</td><td className="px-6 py-3 text-right"><span className={`inline-block px-2 py-0.5 rounded text-sm ${analysis.current_price > analysis.sma_50 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{analysis.current_price > analysis.sma_50 ? 'Above' : 'Below'}</span></td></tr>}
                    {analysis.sma_200 && <tr><td className="px-6 py-3 font-medium">SMA 200</td><td className="px-6 py-3 text-right tabular">₹{analysis.sma_200}</td><td className="px-6 py-3 text-right"><span className={`inline-block px-2 py-0.5 rounded text-sm ${analysis.current_price > analysis.sma_200 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{analysis.current_price > analysis.sma_200 ? 'Above' : 'Below'}</span></td></tr>}
                  </tbody>
                </table>
              </div>

              {/* Support/Resistance */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#10b981]/5 border border-[#10b981]/20 rounded-lg p-5"><div className="text-sm text-[#10b981] mb-1">Support</div><div className="text-2xl font-bold">₹{analysis.support}</div></div>
                <div className="bg-[#ef4444]/5 border border-[#ef4444]/20 rounded-lg p-5"><div className="text-sm text-[#ef4444] mb-1">Resistance</div><div className="text-2xl font-bold">₹{analysis.resistance}</div></div>
              </div>
            </div>

            <div className="space-y-4">
              {/* RSI */}
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
                <h3 className="font-semibold mb-4">RSI</h3>
                <div className="flex items-center gap-4 mb-4">
                  <div className="text-4xl font-bold tabular">{analysis.rsi}</div>
                  <span className={`px-2 py-1 rounded text-sm font-medium ${analysis.rsi_signal === 'OVERSOLD' ? 'bg-[#10b981]/10 text-[#10b981]' : analysis.rsi_signal === 'OVERBOUGHT' ? 'bg-[#ef4444]/10 text-[#ef4444]' : 'bg-[var(--border)] text-[var(--text-muted)]'}`}>{analysis.rsi_signal}</span>
                </div>
                <div className="h-3 bg-[var(--bg-primary)] rounded-full overflow-hidden mb-2"><div className={`h-full ${analysis.rsi < 30 ? 'bg-[#10b981]' : analysis.rsi > 70 ? 'bg-[#ef4444]' : 'bg-[var(--accent)]'}`} style={{ width: `${analysis.rsi}%` }} /></div>
                <div className="flex justify-between text-xs text-[var(--text-muted)]"><span>Oversold</span><span>Overbought</span></div>
              </div>

              {/* News */}
              {news.length > 0 && (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                  <div className="px-5 py-4 border-b border-[var(--border)] font-semibold">News</div>
                  <div className="divide-y divide-[var(--border)]">{news.slice(0, 5).map((n, i) => <a key={i} href={n.link} target="_blank" className="block px-5 py-3 hover:bg-[var(--bg-tertiary)]"><div className="font-medium text-sm line-clamp-2 mb-1">{n.title}</div><div className="text-xs text-[var(--text-muted)]">{n.publisher}</div></a>)}</div>
                </div>
              )}
            </div>
          </div>
        ) : !loading && (
          <div className="text-center py-20"><div className="w-20 h-20 mx-auto mb-6 rounded-full bg-[var(--border)] flex items-center justify-center"><Search className="w-10 h-10 text-[var(--text-muted)]" /></div><div className="text-[var(--text-muted)] text-lg">Search for a stock to analyze</div></div>
        )}
      </main>
    </div>
  );
}
