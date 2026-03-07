'use client';
import { useState, useEffect } from 'react';
import { Layers, AlertTriangle, CheckCircle, PieChart } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function MFOverlapPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api('/api/analytics/mf-overlap').then(setData).finally(() => setLoading(false));
  }, []);

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-4 md:p-6">Analyzing your mutual funds...</div></div>;

  if (!data?.funds?.length) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Navbar />
        <main className="p-4 md:p-6">
          <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2 mb-6"><Layers className="w-5 h-5 md:w-6 md:h-6" /> MF Overlap Analyzer</h1>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
            <PieChart className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
            <div className="text-[var(--text-muted)]">No mutual funds in your portfolio. Add MF holdings to analyze overlap.</div>
          </div>
        </main>
      </div>
    );
  }

  const { funds, overlaps, summary } = data;
  const scoreColor = summary.diversification_score >= 70 ? '#10b981' : summary.diversification_score >= 40 ? '#f59e0b' : '#ef4444';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6">
        <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2 mb-6"><Layers className="w-5 h-5 md:w-6 md:h-6" /> MF Overlap Analyzer</h1>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Mutual Funds</div>
            <div className="text-xl md:text-2xl font-semibold">{summary.total_funds}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Overlapping Stocks</div>
            <div className="text-xl md:text-2xl font-semibold text-[#f59e0b]">{summary.overlapping_stocks}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">High Overlap</div>
            <div className="text-xl md:text-2xl font-semibold text-[#ef4444]">{summary.high_overlap_stocks}</div>
            <div className="text-xs text-[var(--text-muted)]">In 3+ funds</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Diversification</div>
            <div className="text-xl md:text-2xl font-semibold" style={{ color: scoreColor }}>{summary.diversification_score}/100</div>
          </div>
        </div>

        {/* Recommendation */}
        <div className={`rounded-lg p-4 mb-6 flex items-start gap-3 ${summary.diversification_score >= 70 ? 'bg-[#10b981]/10 border border-[#10b981]/30' : 'bg-[#f59e0b]/10 border border-[#f59e0b]/30'}`}>
          {summary.diversification_score >= 70 ? <CheckCircle className="w-5 h-5 text-[#10b981] mt-0.5 shrink-0" /> : <AlertTriangle className="w-5 h-5 text-[#f59e0b] mt-0.5 shrink-0" />}
          <div>
            <div className="font-medium" style={{ color: summary.diversification_score >= 70 ? '#10b981' : '#f59e0b' }}>
              {summary.diversification_score >= 70 ? 'Good Diversification' : 'Overlap Detected'}
            </div>
            <div className="text-sm text-[var(--text-secondary)]">{summary.recommendation}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Your Funds */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <h2 className="font-semibold mb-4">Your Mutual Funds</h2>
            <div className="space-y-3">
              {funds.map((f, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-[var(--bg-primary)] rounded-lg">
                  <div>
                    <div className="font-medium text-sm">{f.name.length > 30 ? f.name.slice(0, 30) + '...' : f.name}</div>
                    <div className="text-xs text-[var(--text-muted)]">{f.stock_count} stocks</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">₹{fmt(f.value)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Overlapping Stocks */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <h2 className="font-semibold mb-4">Stock Overlap</h2>
            {overlaps.length > 0 ? (
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {overlaps.map((o, i) => (
                  <div key={i} className="p-3 bg-[var(--bg-primary)] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium">{o.stock}</div>
                      <span className={`text-xs px-2 py-0.5 rounded ${o.risk_level === 'High' ? 'bg-[#ef4444]/10 text-[#ef4444]' : 'bg-[#f59e0b]/10 text-[#f59e0b]'}`}>
                        {o.fund_count} funds
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {o.funds.map((f, j) => (
                        <span key={j} className="text-xs bg-[var(--bg-secondary)] px-2 py-1 rounded">
                          {f.fund.length > 15 ? f.fund.slice(0, 15) + '...' : f.fund} ({f.weight}%)
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[var(--text-muted)]">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-[#10b981]" />
                No significant overlap found
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
