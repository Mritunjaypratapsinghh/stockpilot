'use client';
import { useState, useEffect } from 'react';
import { Target, Plus, Trash2, TrendingUp, Calendar, X, PiggyBank } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

const CATEGORIES = [
  { value: 'retirement', label: 'Retirement', icon: '🏖️' },
  { value: 'house', label: 'House', icon: '🏠' },
  { value: 'education', label: 'Education', icon: '🎓' },
  { value: 'emergency', label: 'Emergency Fund', icon: '🏥' },
  { value: 'general', label: 'General', icon: '💰' },
];

export default function GoalsPage() {
  const [goals, setGoals] = useState([]);
  const [projections, setProjections] = useState(null);
  const [portfolioValue, setPortfolioValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', target_amount: '', target_date: '', category: 'general', monthly_sip: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [goalsData, projData] = await Promise.all([api('/api/finance/goals'), api('/api/finance/goals/projections')]);
      setGoals(goalsData.goals || []);
      setPortfolioValue(goalsData.portfolio_value || 0);
      setProjections(projData);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api('/api/finance/goals', { method: 'POST', body: JSON.stringify({ ...form, target_amount: parseFloat(form.target_amount), monthly_sip: form.monthly_sip ? parseFloat(form.monthly_sip) : null }) });
      setShowForm(false);
      setForm({ name: '', target_amount: '', target_date: '', category: 'general', monthly_sip: '' });
      loadData();
    } catch (e) { alert(e.message); }
  };

  const deleteGoal = async (id) => { if (confirm('Delete goal?')) { await api(`/api/finance/goals/${id}`, { method: 'DELETE' }); loadData(); } };
  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Financial Goals</h1>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:bg-[#5558e3]">
            <Plus className="w-4 h-4" /> Add Goal
          </button>
        </div>

        {/* Portfolio Projections */}
        {projections && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <TrendingUp className="w-5 h-5 text-[#10b981]" />
              <span className="font-medium">Portfolio Projections</span>
              <span className="text-sm text-[var(--text-muted)]">Current: ₹{fmt(projections.current_value)}</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {projections.projections?.map(p => (
                <div key={p.years} className="bg-[var(--bg-primary)] rounded-lg p-3">
                  <div className="text-sm text-[var(--text-muted)] mb-1">{p.years} Year{p.years > 1 ? 's' : ''}</div>
                  <div className="text-xs text-[var(--text-muted)]">Conservative (8%)</div>
                  <div className="font-medium">₹{fmt(p.conservative)}</div>
                  <div className="text-xs text-[var(--text-muted)] mt-1">Moderate (12%)</div>
                  <div className="font-medium text-[#10b981]">₹{fmt(p.moderate)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Goals List */}
        {loading ? (
          <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-[var(--bg-secondary)] rounded-lg animate-pulse" />)}</div>
        ) : goals.length === 0 ? (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
            <Target className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
            <div className="text-[var(--text-muted)]">No goals yet. Create your first financial goal!</div>
          </div>
        ) : (
          <div className="grid gap-4">
            {goals.map(g => {
              const cat = CATEGORIES.find(c => c.value === g.category) || CATEGORIES[4];
              return (
                <div key={g._id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{cat.icon}</span>
                      <div>
                        <div className="font-medium">{g.name}</div>
                        <div className="text-sm text-[var(--text-muted)]">{cat.label} • {g.months_left} months left</div>
                      </div>
                    </div>
                    <button onClick={() => deleteGoal(g._id)} className="p-2 text-[var(--text-muted)] hover:text-[#ef4444]"><Trash2 className="w-4 h-4" /></button>
                  </div>
                  
                  <div className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span>₹{fmt(g.current_value)} of ₹{fmt(g.target_amount)}</span>
                      <span className={g.on_track ? 'text-[#10b981]' : 'text-[#f59e0b]'}>{g.progress}%</span>
                    </div>
                    <div className="h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${g.on_track ? 'bg-[#10b981]' : 'bg-[#f59e0b]'}`} style={{ width: `${Math.min(100, g.progress)}%` }} />
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4">
                      <div><span className="text-[var(--text-muted)]">Your SIP:</span> ₹{fmt(g.monthly_sip)}/mo</div>
                      <div><span className="text-[var(--text-muted)]">Required:</span> <span className={g.on_track ? 'text-[#10b981]' : 'text-[#ef4444]'}>₹{fmt(g.required_sip)}/mo</span></div>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${g.on_track ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#f59e0b]/10 text-[#f59e0b]'}`}>
                      {g.on_track ? 'On Track' : 'Needs Attention'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Add Goal Modal */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowForm(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Create Goal</h2>
                <button onClick={() => setShowForm(false)} className="p-2 text-[var(--text-muted)] hover:text-white"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Goal Name</label>
                  <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Retirement Fund" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Category</label>
                  <select value={form.category} onChange={e => setForm({...form, category: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg">
                    {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.icon} {c.label}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">Target Amount (₹)</label>
                    <input type="number" value={form.target_amount} onChange={e => setForm({...form, target_amount: e.target.value})} placeholder="1000000" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" required />
                  </div>
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">Target Date</label>
                    <input type="date" value={form.target_date} onChange={e => setForm({...form, target_date: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" required />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Monthly SIP (₹) <span className="text-[var(--text-muted)]">optional</span></label>
                  <input type="number" value={form.monthly_sip} onChange={e => setForm({...form, monthly_sip: e.target.value})} placeholder="10000" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" />
                </div>
                <button type="submit" className="w-full py-3 bg-[var(--accent)] text-white rounded-lg font-medium hover:bg-[#5558e3]">Create Goal</button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
