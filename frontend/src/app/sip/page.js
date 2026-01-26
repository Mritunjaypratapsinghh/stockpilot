'use client';
import { useState, useEffect } from 'react';
import { RefreshCw, Plus, Pause, Play, Trash2, X, Calculator } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function SIPPage() {
  const [sips, setSips] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showCalc, setShowCalc] = useState(false);
  const [form, setForm] = useState({ symbol: '', amount: '', frequency: 'monthly', sip_date: '1', start_date: new Date().toISOString().split('T')[0] });
  const [calc, setCalc] = useState({ amount: '10000', years: '10', return: '12' });
  const [calcResult, setCalcResult] = useState(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api('/api/sip/');
      setSips(data.sips || []);
      setSummary(data.summary || {});
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api('/api/sip/', { method: 'POST', body: JSON.stringify({ ...form, amount: parseFloat(form.amount), sip_date: parseInt(form.sip_date) }) });
      setShowForm(false);
      setForm({ symbol: '', amount: '', frequency: 'monthly', sip_date: '1', start_date: new Date().toISOString().split('T')[0] });
      loadData();
    } catch (e) { alert(e.message); }
  };

  const toggleSIP = async (id) => { await api(`/api/sip/${id}/toggle`, { method: 'PUT' }); loadData(); };
  const deleteSIP = async (id) => { if (confirm('Delete SIP?')) { await api(`/api/sip/${id}`, { method: 'DELETE' }); loadData(); } };

  const runCalculator = async () => {
    try {
      const data = await api(`/api/sip/calculator?monthly_amount=${calc.amount}&years=${calc.years}&expected_return=${calc.return}`);
      setCalcResult(data);
    } catch (e) { console.error(e); }
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">SIP Tracker</h1>
          <div className="flex gap-2">
            <button onClick={() => setShowCalc(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-sm"><Calculator className="w-4 h-4" /> Calculator</button>
            <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] text-white rounded-lg text-sm font-medium"><Plus className="w-4 h-4" /> Add SIP</button>
          </div>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)]">Total Invested</div>
            <div className="text-xl font-semibold">₹{fmt(summary.total_invested)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)]">Current Value</div>
            <div className="text-xl font-semibold">₹{fmt(summary.current_value)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)]">Total Returns</div>
            <div className={`text-xl font-semibold ${summary.total_returns >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              {summary.total_returns >= 0 ? '+' : ''}₹{fmt(summary.total_returns)}
            </div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)]">Returns %</div>
            <div className={`text-xl font-semibold ${summary.returns_pct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              {summary.returns_pct >= 0 ? '+' : ''}{summary.returns_pct}%
            </div>
          </div>
        </div>

        {/* SIP List */}
        {loading ? (
          <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-20 bg-[var(--bg-secondary)] rounded-lg animate-pulse" />)}</div>
        ) : sips.length === 0 ? (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
            <RefreshCw className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
            <div className="text-[var(--text-muted)]">No SIPs yet. Start your first SIP!</div>
          </div>
        ) : (
          <div className="space-y-3">
            {sips.map(sip => (
              <div key={sip._id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="font-medium">{sip.symbol}</div>
                      <div className="text-sm text-[var(--text-muted)]">₹{fmt(sip.amount)}/{sip.frequency} • Day {sip.sip_date}</div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${sip.is_active ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[var(--border)] text-[var(--text-muted)]'}`}>
                      {sip.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-sm text-[var(--text-muted)]">Invested</div>
                      <div className="font-medium">₹{fmt(sip.total_invested)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-[var(--text-muted)]">Current</div>
                      <div className="font-medium">₹{fmt(sip.current_value)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-[var(--text-muted)]">Returns</div>
                      <div className={`font-medium ${sip.returns >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                        {sip.returns_pct >= 0 ? '+' : ''}{sip.returns_pct}%
                      </div>
                    </div>
                    {sip.xirr && (
                      <div className="text-right">
                        <div className="text-sm text-[var(--text-muted)]">XIRR</div>
                        <div className={`font-medium ${sip.xirr >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{sip.xirr}%</div>
                      </div>
                    )}
                    <div className="flex gap-1">
                      <button onClick={() => toggleSIP(sip._id)} className="p-2 hover:bg-[var(--border)] rounded">
                        {sip.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </button>
                      <button onClick={() => deleteSIP(sip._id)} className="p-2 hover:bg-[#ef4444]/10 hover:text-[#ef4444] rounded">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add SIP Modal */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowForm(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Add SIP</h2>
                <button onClick={() => setShowForm(false)} className="p-2 text-[var(--text-muted)] hover:text-white"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Symbol</label>
                  <input value={form.symbol} onChange={e => setForm({...form, symbol: e.target.value.toUpperCase()})} placeholder="e.g. PPFAS" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">Amount (₹)</label>
                    <input type="number" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} placeholder="10000" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" required />
                  </div>
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">SIP Date</label>
                    <select value={form.sip_date} onChange={e => setForm({...form, sip_date: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg">
                      {[...Array(28)].map((_, i) => <option key={i+1} value={i+1}>{i+1}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Start Date</label>
                  <input type="date" value={form.start_date} onChange={e => setForm({...form, start_date: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" required />
                </div>
                <button type="submit" className="w-full py-3 bg-[#6366f1] text-white rounded-lg font-medium">Create SIP</button>
              </form>
            </div>
          </div>
        )}

        {/* Calculator Modal */}
        {showCalc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowCalc(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">SIP Calculator</h2>
                <button onClick={() => setShowCalc(false)} className="p-2 text-[var(--text-muted)] hover:text-white"><X className="w-5 h-5" /></button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Monthly Amount (₹)</label>
                  <input type="number" value={calc.amount} onChange={e => setCalc({...calc, amount: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">Years</label>
                    <input type="number" value={calc.years} onChange={e => setCalc({...calc, years: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">Expected Return %</label>
                    <input type="number" value={calc.return} onChange={e => setCalc({...calc, return: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg" />
                  </div>
                </div>
                <button onClick={runCalculator} className="w-full py-3 bg-[#6366f1] text-white rounded-lg font-medium">Calculate</button>
                {calcResult && (
                  <div className="bg-[var(--bg-primary)] rounded-lg p-4 space-y-2">
                    <div className="flex justify-between"><span className="text-[var(--text-muted)]">Total Invested</span><span className="font-medium">₹{fmt(calcResult.total_invested)}</span></div>
                    <div className="flex justify-between"><span className="text-[var(--text-muted)]">Future Value</span><span className="font-medium text-[#10b981]">₹{fmt(calcResult.future_value)}</span></div>
                    <div className="flex justify-between"><span className="text-[var(--text-muted)]">Wealth Gained</span><span className="font-medium text-[#10b981]">₹{fmt(calcResult.wealth_gained)}</span></div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
