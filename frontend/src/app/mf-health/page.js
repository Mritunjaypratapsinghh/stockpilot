'use client';
import { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle, TrendingUp, TrendingDown, DollarSign, Layers, ArrowRight } from 'lucide-react';
import { api } from '../../lib/api';
import Navbar from '../../components/Navbar';

export default function MFHealthPage() {
  const [health, setHealth] = useState(null);
  const [overlap, setOverlap] = useState(null);
  const [expense, setExpense] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [h, o, e] = await Promise.all([
        api('/api/portfolio/mf/health'),
        api('/api/portfolio/mf/overlap'),
        api('/api/portfolio/mf/expense-impact?years=20')
      ]);
      setHealth(h);
      setOverlap(o);
      setExpense(e);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-6">Loading...</div></div>;

  const getStatusColor = (status) => {
    if (status === 'Outperforming') return 'text-[#22c55e]';
    if (status === 'Underperforming') return 'text-[#ef4444]';
    return 'text-[var(--text-secondary)]';
  };

  const getStatusBg = (status) => {
    if (status === 'Outperforming') return 'bg-[#22c55e]/10';
    if (status === 'Underperforming') return 'bg-[#ef4444]/10';
    return 'bg-[var(--bg-tertiary)]';
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Mutual Fund Health Check</h1>
          <p className="text-[var(--text-secondary)]">Analyze your MF portfolio for performance, overlap, and expenses</p>
        </div>

        {/* Health Score */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-xl ${health?.health_score >= 70 ? 'bg-[#22c55e]/20' : health?.health_score >= 40 ? 'bg-[#eab308]/20' : 'bg-[#ef4444]/20'}`}>
                <Activity className={`w-6 h-6 ${health?.health_score >= 70 ? 'text-[#22c55e]' : health?.health_score >= 40 ? 'text-[#eab308]' : 'text-[#ef4444]'}`} />
              </div>
              <div>
                <div className="text-sm text-[var(--text-secondary)]">Health Score</div>
                <div className={`text-2xl font-bold ${health?.health_score >= 70 ? 'text-[#22c55e]' : health?.health_score >= 40 ? 'text-[#eab308]' : 'text-[#ef4444]'}`}>{health?.health_score || 0}/100</div>
                {health?.note && <div className="text-xs text-[var(--text-secondary)] mt-1">{health.note}</div>}
              </div>
            </div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <div className="text-sm text-[var(--text-secondary)]">Total MF Value</div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">₹{(health?.total_mf_value || 0).toLocaleString('en-IN')}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <div className="text-sm text-[var(--text-secondary)]">Avg Expense Ratio</div>
            <div className={`text-2xl font-bold ${(health?.avg_expense_ratio || 0) > 1 ? 'text-[#ef4444]' : 'text-[#22c55e]'}`}>{health?.avg_expense_ratio || 0}%</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <div className="text-sm text-[var(--text-secondary)]">Annual Expense</div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">₹{(health?.total_annual_expense || 0).toLocaleString('en-IN')}</div>
          </div>
        </div>

        {/* Issues */}
        {health?.issues?.length > 0 && (
          <div className="bg-[#ef4444]/10 border border-[#ef4444]/30 rounded-xl p-4">
            <div className="flex items-center gap-2 text-[#ef4444] font-medium mb-2">
              <AlertTriangle className="w-5 h-5" />Issues Found
            </div>
            <ul className="space-y-1">
              {health.issues.map((issue, i) => (
                <li key={i} className="text-sm text-[var(--text-secondary)]">• {issue}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Fund Analysis */}
        <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Fund Performance</h2>
          <div className="space-y-3">
            {health?.funds?.map((fund, i) => (
              <div key={i} className={`p-4 rounded-lg ${getStatusBg(fund.status)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">{fund.symbol}</div>
                    <div className="text-sm text-[var(--text-secondary)]">{fund.category} • Expense: {fund.expense_ratio}%</div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${fund.returns_pct >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                      {fund.returns_pct >= 0 ? '+' : ''}{fund.returns_pct}%
                    </div>
                    <div className={`text-sm ${getStatusColor(fund.status)}`}>{fund.status}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-2 text-xs text-[var(--text-secondary)]">
                  <span>Benchmark: {fund.benchmark_return}%</span>
                  <span>•</span>
                  <span>Value: ₹{fund.value.toLocaleString('en-IN')}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Expense Impact */}
        {expense && (
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Expense Ratio Impact (20 Years)</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg">
                <div className="text-sm text-[var(--text-secondary)]">Current Plan Value</div>
                <div className="text-xl font-bold text-[var(--text-primary)]">₹{(expense.future_value_current / 100000).toFixed(1)}L</div>
                <div className="text-xs text-[var(--text-secondary)]">@ {expense.current_expense_ratio}% expense</div>
              </div>
              <div className="p-4 bg-[#22c55e]/10 rounded-lg border border-[#22c55e]/30">
                <div className="text-sm text-[var(--text-secondary)]">Direct Plan Value</div>
                <div className="text-xl font-bold text-[#22c55e]">₹{(expense.future_value_direct / 100000).toFixed(1)}L</div>
                <div className="text-xs text-[var(--text-secondary)]">@ {expense.direct_expense_ratio}% expense</div>
              </div>
              <div className="p-4 bg-[var(--accent)]/10 rounded-lg border border-[var(--accent)]/30">
                <div className="text-sm text-[var(--text-secondary)]">Potential Savings</div>
                <div className="text-xl font-bold text-[var(--accent)]">₹{(expense.potential_savings / 100000).toFixed(1)}L</div>
                <div className="text-xs text-[var(--text-secondary)]">by switching to direct</div>
              </div>
            </div>
            <p className="text-sm text-[var(--text-secondary)] mt-4">{expense.message}</p>
          </div>
        )}

        {/* Recommendations */}
        {health?.recommendations?.length > 0 && (
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Recommendations</h2>
            <div className="space-y-3">
              {health.recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                  <div className="p-2 rounded-lg bg-[var(--accent)]/20">
                    {rec.type === 'switch' && <TrendingUp className="w-5 h-5 text-[var(--accent)]" />}
                    {rec.type === 'expense' && <DollarSign className="w-5 h-5 text-[var(--accent)]" />}
                    {rec.type === 'consolidate' && <Layers className="w-5 h-5 text-[var(--accent)]" />}
                    {rec.type === 'add' && <CheckCircle className="w-5 h-5 text-[var(--accent)]" />}
                  </div>
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">{rec.message}</div>
                    {rec.potential_savings && (
                      <div className="text-sm text-[#22c55e]">Potential savings: ₹{rec.potential_savings.toLocaleString('en-IN')}/year</div>
                    )}
                    {rec.funds && (
                      <div className="text-sm text-[var(--text-secondary)]">Funds: {rec.funds.join(', ')}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
