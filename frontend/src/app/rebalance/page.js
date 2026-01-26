'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { RefreshCw, TrendingUp, TrendingDown, AlertCircle, Check, Edit2, Save } from 'lucide-react';
import { api } from '../../lib/api';
import Navbar from '../../components/Navbar';

const COLORS = { Equity: '#6366f1', Debt: '#22c55e', Gold: '#eab308', Cash: '#64748b' };

export default function RebalancePage() {
  const [data, setData] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [editing, setEditing] = useState(false);
  const [target, setTarget] = useState({ Equity: 60, Debt: 30, Gold: 5, Cash: 5 });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [alloc, suggest] = await Promise.all([
        api('/api/rebalance/allocation'),
        api('/api/rebalance/suggestions')
      ]);
      setData(alloc);
      setSuggestions(suggest);
      if (alloc.target) setTarget(alloc.target);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const saveTarget = async () => {
    try {
      await api('/api/rebalance/target', {
        method: 'POST',
        body: JSON.stringify(target)
      });
      setEditing(false);
      fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const chartData = data ? Object.entries(data.current).map(([name, value]) => ({ name, value })).filter(d => d.value > 0) : [];

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-6 text-[var(--text-secondary)]">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Portfolio Rebalancing</h1>
          <p className="text-[var(--text-secondary)]">Keep your portfolio aligned with your target allocation</p>
        </div>
        <button onClick={fetchData} className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)]">
          <RefreshCw className="w-5 h-5 text-[var(--text-secondary)]" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Allocation Chart */}
        <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Current Allocation</h2>
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}%`}>
                  {chartData.map((entry) => <Cell key={entry.name} fill={COLORS[entry.name]} />)}
                </Pie>
                <Tooltip formatter={(v) => `${v}%`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center text-[var(--text-secondary)] mt-2">
            Total: ₹{data?.total_value?.toLocaleString('en-IN')}
          </div>
        </div>

        {/* Target Allocation */}
        <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Target Allocation</h2>
            {editing ? (
              <button onClick={saveTarget} className="flex items-center gap-1 px-3 py-1 bg-[#22c55e] text-white rounded-lg text-sm">
                <Save className="w-4 h-4" />Save
              </button>
            ) : (
              <button onClick={() => setEditing(true)} className="flex items-center gap-1 px-3 py-1 bg-[var(--bg-tertiary)] rounded-lg text-sm text-[var(--text-secondary)]">
                <Edit2 className="w-4 h-4" />Edit
              </button>
            )}
          </div>
          <div className="space-y-4">
            {Object.entries(target).map(([cat, val]) => (
              <div key={cat} className="flex items-center gap-4">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[cat] }}></div>
                <span className="w-16 text-[var(--text-primary)]">{cat}</span>
                {editing ? (
                  <input type="number" value={val} onChange={(e) => setTarget({ ...target, [cat]: Number(e.target.value) })} className="w-20 px-2 py-1 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded text-[var(--text-primary)]" />
                ) : (
                  <span className="w-12 text-[var(--text-primary)]">{val}%</span>
                )}
                <div className="flex-1 bg-[var(--bg-tertiary)] rounded-full h-2">
                  <div className="h-2 rounded-full" style={{ width: `${val}%`, backgroundColor: COLORS[cat] }}></div>
                </div>
                <span className={`w-16 text-right text-sm ${data?.deviation?.[cat] > 0 ? 'text-[#22c55e]' : data?.deviation?.[cat] < 0 ? 'text-[#ef4444]' : 'text-[var(--text-secondary)]'}`}>
                  {data?.deviation?.[cat] > 0 ? '+' : ''}{data?.deviation?.[cat]}%
                </span>
              </div>
            ))}
          </div>
          {editing && (
            <p className="text-sm text-[var(--text-secondary)] mt-4">Total: {Object.values(target).reduce((a, b) => a + b, 0)}% (must equal 100%)</p>
          )}
        </div>
      </div>

      {/* Rebalancing Suggestions */}
      <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Rebalancing Suggestions</h2>
        {suggestions?.suggestions?.length > 0 ? (
          <div className="space-y-4">
            {suggestions.suggestions.map((s, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                <div className={`p-2 rounded-lg ${s.action === 'BUY' ? 'bg-[#22c55e]/20' : 'bg-[#ef4444]/20'}`}>
                  {s.action === 'BUY' ? <TrendingUp className="w-5 h-5 text-[#22c55e]" /> : <TrendingDown className="w-5 h-5 text-[#ef4444]" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.action === 'BUY' ? 'bg-[#22c55e]/20 text-[#22c55e]' : 'bg-[#ef4444]/20 text-[#ef4444]'}`}>{s.action}</span>
                    <span className="font-medium text-[var(--text-primary)]">{s.category}</span>
                  </div>
                  <p className="text-sm text-[var(--text-secondary)] mt-1">
                    {s.action} ₹{s.amount.toLocaleString('en-IN')} to reach {s.target_pct}% target (currently {s.current_pct}%)
                  </p>
                  {s.suggested_funds && (
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Suggested: {s.suggested_funds.join(', ')}</p>
                  )}
                </div>
                <div className="text-right">
                  <span className={`text-lg font-semibold ${s.deviation_pct > 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                    {s.deviation_pct > 0 ? '+' : ''}{s.deviation_pct}%
                  </span>
                  <p className="text-xs text-[var(--text-secondary)]">deviation</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-3 p-4 bg-[#22c55e]/10 rounded-lg">
            <Check className="w-5 h-5 text-[#22c55e]" />
            <span className="text-[#22c55e]">Your portfolio is well balanced! No rebalancing needed.</span>
          </div>
        )}
        <p className="text-sm text-[var(--text-secondary)] mt-4 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {suggestions?.note}
        </p>
      </div>
      </main>
    </div>
  );
}
