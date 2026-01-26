'use client';
import { useState } from 'react';
import { Search, ArrowRightLeft, TrendingUp, TrendingDown, Loader2 } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function ComparePage() {
  const [symbols, setSymbols] = useState('');
  const [stocks, setStocks] = useState([]);
  const [comparison, setComparison] = useState({});
  const [loading, setLoading] = useState(false);

  const compare = async () => {
    if (!symbols.trim()) return;
    setLoading(true);
    try {
      const data = await api(`/api/compare/compare?symbols=${symbols}`);
      setStocks(data.stocks || []);
      setComparison(data.comparison || {});
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '—';
  const isBest = (symbol, metric) => comparison[metric]?.best === symbol;
  const isWorst = (symbol, metric) => comparison[metric]?.worst === symbol;

  const metrics = [
    { key: 'price', label: 'Price', prefix: '₹' },
    { key: 'market_cap', label: 'MCap (Cr)', prefix: '₹' },
    { key: 'pe', label: 'PE Ratio' },
    { key: 'pb', label: 'PB Ratio' },
    { key: 'roe', label: 'ROE %' },
    { key: 'roce', label: 'ROCE %' },
    { key: 'debt_equity', label: 'Debt/Equity' },
    { key: 'profit_margin', label: 'Profit Margin %' },
    { key: 'revenue_growth', label: 'Revenue Growth %' },
    { key: 'dividend_yield', label: 'Div Yield %' },
    { key: 'high_52w', label: '52W High', prefix: '₹' },
    { key: 'low_52w', label: '52W Low', prefix: '₹' },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <h1 className="text-2xl font-bold mb-6">Compare Stocks</h1>

        {/* Search */}
        <div className="flex gap-3 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)]" />
            <input
              value={symbols}
              onChange={e => setSymbols(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && compare()}
              placeholder="Enter symbols separated by comma (e.g., RELIANCE, TCS, INFY)"
              className="w-full pl-10 pr-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)]"
            />
          </div>
          <button onClick={compare} disabled={loading} className="px-6 py-3 bg-[var(--accent)] text-white rounded-lg font-medium flex items-center gap-2">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowRightLeft className="w-5 h-5" />}
            Compare
          </button>
        </div>

        {/* Quick Compare */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <span className="text-sm text-[var(--text-muted)]">Quick:</span>
          {['RELIANCE,TCS,INFY', 'HDFCBANK,ICICIBANK,KOTAKBANK', 'TATAMOTORS,MARUTI,M&M', 'SUNPHARMA,DRREDDY,CIPLA'].map(q => (
            <button key={q} onClick={() => { setSymbols(q); }} className="px-3 py-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded text-sm hover:border-[var(--accent)]">
              {q.split(',').join(' vs ')}
            </button>
          ))}
        </div>

        {/* Comparison Table */}
        {stocks.length > 0 && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="text-left px-4 py-3 text-sm text-[var(--text-muted)] font-medium">Metric</th>
                    {stocks.map(s => (
                      <th key={s.symbol} className="text-right px-4 py-3 min-w-[140px]">
                        <div className="font-semibold">{s.symbol}</div>
                        <div className="text-xs text-[var(--text-muted)] font-normal truncate">{s.name}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metrics.map(m => (
                    <tr key={m.key} className="border-b border-[var(--border)] hover:bg-[var(--bg-hover)]">
                      <td className="px-4 py-3 text-sm text-[var(--text-muted)]">{m.label}</td>
                      {stocks.map(s => {
                        const val = s[m.key];
                        const best = isBest(s.symbol, m.key);
                        const worst = isWorst(s.symbol, m.key);
                        return (
                          <td key={s.symbol} className={`px-4 py-3 text-right font-medium ${best ? 'text-[#10b981] bg-[#10b981]/5' : worst ? 'text-[#ef4444] bg-[#ef4444]/5' : ''}`}>
                            {m.prefix || ''}{fmt(val)}
                            {best && <TrendingUp className="w-3 h-3 inline ml-1" />}
                            {worst && <TrendingDown className="w-3 h-3 inline ml-1" />}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-3 bg-[var(--bg-primary)] text-xs text-[var(--text-muted)] flex gap-4">
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-[#10b981]/20 rounded" /> Best</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-[#ef4444]/20 rounded" /> Worst</span>
            </div>
          </div>
        )}

        {stocks.length === 0 && !loading && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
            <ArrowRightLeft className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
            <div className="text-[var(--text-muted)]">Enter 2-4 stock symbols to compare</div>
          </div>
        )}
      </main>
    </div>
  );
}
