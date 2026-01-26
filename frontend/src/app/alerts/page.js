'use client';
import { useState, useEffect } from 'react';
import { Bell, Plus, Trash2, TrendingUp, TrendingDown, X } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { getAlerts, api } from '../../lib/api';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [symbol, setSymbol] = useState('');
  const [alertType, setAlertType] = useState('PRICE_ABOVE');
  const [targetValue, setTargetValue] = useState('');

  useEffect(() => { getAlerts().then(setAlerts).finally(() => setLoading(false)); }, []);
  const createAlert = async (e) => { e.preventDefault(); try { await api('/api/alerts', { method: 'POST', body: JSON.stringify({ symbol: symbol.toUpperCase(), alert_type: alertType, target_value: parseFloat(targetValue) }) }); setSymbol(''); setTargetValue(''); setShowForm(false); getAlerts().then(setAlerts); } catch (err) { alert(err.message); } };
  const deleteAlert = async (id) => { await api(`/api/alerts/${id}`, { method: 'DELETE' }); setAlerts(alerts.filter(a => a._id !== id)); };

  const active = alerts.filter(a => a.is_active);
  const triggered = alerts.filter(a => !a.is_active);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Price Alerts</h1>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:bg-[#5558e3]"><Plus className="w-4 h-4" /> New Alert</button>
        </div>

        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowForm(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6"><h2 className="text-lg font-semibold">Create Alert</h2><button onClick={() => setShowForm(false)} className="p-2 text-[var(--text-muted)] hover:text-white rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button></div>
              <form onSubmit={createAlert} className="space-y-4">
                <div><label className="block text-sm text-[var(--text-secondary)] mb-2">Symbol</label><input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} placeholder="HDFCBANK" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required /></div>
                <div><label className="block text-sm text-[var(--text-secondary)] mb-2">Type</label><div className="grid grid-cols-1 lg:grid-cols-3 gap-2">{[{ v: 'PRICE_ABOVE', l: 'Above' }, { v: 'PRICE_BELOW', l: 'Below' }, { v: 'PERCENT_CHANGE', l: '% Change' }].map(t => <button key={t.v} type="button" onClick={() => setAlertType(t.v)} className={`py-2 rounded-lg text-sm font-medium ${alertType === t.v ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-secondary)]'}`}>{t.l}</button>)}</div></div>
                <div><label className="block text-sm text-[var(--text-secondary)] mb-2">Target</label><input type="number" step="0.01" value={targetValue} onChange={e => setTargetValue(e.target.value)} placeholder={alertType === 'PERCENT_CHANGE' ? '5' : '1500'} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required /></div>
                <button type="submit" className="w-full py-3 bg-[var(--accent)] text-white rounded-lg font-medium hover:bg-[#5558e3]">Create</button>
              </form>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex items-center gap-2 mb-4"><Bell className="w-4 h-4 text-[var(--accent)]" /><span className="font-medium">Active ({active.length})</span></div>
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
              {loading ? <div className="p-6 space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="h-12 bg-[var(--border)] rounded animate-pulse" />)}</div> : active.length === 0 ? <div className="p-8 text-center text-[var(--text-muted)]">No active alerts</div> : (
                <table className="w-full">
                  <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase"><th className="text-left px-4 py-3 font-medium">Stock</th><th className="text-left px-4 py-3 font-medium">Condition</th><th className="text-right px-4 py-3 font-medium">Target</th><th className="w-12"></th></tr></thead>
                  <tbody>{active.map(a => <tr key={a._id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]"><td className="px-4 py-3"><div className="flex items-center gap-2"><div className={`w-8 h-8 rounded-lg flex items-center justify-center ${a.alert_type.includes('ABOVE') ? 'bg-[#10b981]/10' : 'bg-[#ef4444]/10'}`}>{a.alert_type.includes('ABOVE') ? <TrendingUp className="w-4 h-4 text-[#10b981]" /> : <TrendingDown className="w-4 h-4 text-[#ef4444]" />}</div><span className="font-medium">{a.symbol}</span></div></td><td className="px-4 py-3 text-[var(--text-muted)] text-sm">{a.alert_type.replace(/_/g, ' ')}</td><td className="px-4 py-3 text-right tabular font-medium">₹{a.target_value}</td><td className="px-4 py-3"><button onClick={() => deleteAlert(a._id)} className="p-1 text-[var(--text-muted)] hover:text-[#ef4444]"><Trash2 className="w-4 h-4" /></button></td></tr>)}</tbody>
                </table>
              )}
            </div>
          </div>
          <div>
            <div className="mb-4"><span className="font-medium text-[var(--text-muted)]">Triggered ({triggered.length})</span></div>
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden opacity-60">
              {triggered.length === 0 ? <div className="p-8 text-center text-[var(--text-muted)]">No triggered alerts</div> : (
                <table className="w-full">
                  <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase"><th className="text-left px-4 py-3 font-medium">Stock</th><th className="text-left px-4 py-3 font-medium">Condition</th><th className="text-right px-4 py-3 font-medium">Target</th><th className="w-12"></th></tr></thead>
                  <tbody>{triggered.map(a => <tr key={a._id} className="border-b border-[var(--border)] last:border-0"><td className="px-4 py-3 font-medium">{a.symbol}</td><td className="px-4 py-3 text-[var(--text-muted)] text-sm">{a.alert_type.replace(/_/g, ' ')}</td><td className="px-4 py-3 text-right tabular">₹{a.target_value}</td><td className="px-4 py-3"><button onClick={() => deleteAlert(a._id)} className="p-1 text-[var(--text-muted)] hover:text-[#ef4444]"><Trash2 className="w-4 h-4" /></button></td></tr>)}</tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
