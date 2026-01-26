'use client';
import { useState, useEffect } from 'react';
import { Plus, Trash2, Eye, X, Search } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [symbol, setSymbol] = useState('');
  const [notes, setNotes] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => { loadWatchlist(); }, []);
  const loadWatchlist = () => { api('/api/watchlist').then(setWatchlist).catch(console.error).finally(() => setLoading(false)); };
  const addToWatchlist = async (e) => { e.preventDefault(); try { await api('/api/watchlist', { method: 'POST', body: JSON.stringify({ symbol: symbol.toUpperCase(), notes }) }); setSymbol(''); setNotes(''); setShowForm(false); loadWatchlist(); } catch (err) { alert(err.message); } };
  const removeFromWatchlist = async (id) => { await api(`/api/watchlist/${id}`, { method: 'DELETE' }); loadWatchlist(); };
  const filtered = watchlist.filter(w => w.symbol.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Watchlist</h1>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:bg-[#5558e3]">
            <Plus className="w-4 h-4" /> Add Stock
          </button>
        </div>

        <div className="relative mb-4 w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..." className="w-full pl-10 pr-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-white placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]" />
        </div>

        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowForm(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Add to Watchlist</h2>
                <button onClick={() => setShowForm(false)} className="p-2 text-[var(--text-muted)] hover:text-white rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={addToWatchlist} className="space-y-4">
                <div><label className="block text-sm text-[var(--text-secondary)] mb-2">Symbol</label><input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} placeholder="RELIANCE" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required /></div>
                <div><label className="block text-sm text-[var(--text-secondary)] mb-2">Notes (optional)</label><input value={notes} onChange={e => setNotes(e.target.value)} placeholder="Why watching?" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" /></div>
                <button type="submit" className="w-full py-3 bg-[var(--accent)] text-white rounded-lg font-medium hover:bg-[#5558e3]">Add</button>
              </form>
            </div>
          </div>
        )}

        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
          {loading ? (
            <div className="p-6 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-[var(--border)] rounded animate-pulse" />)}</div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center"><div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--border)] flex items-center justify-center"><Eye className="w-8 h-8 text-[var(--text-muted)]" /></div><div className="text-[var(--text-muted)]">{search ? 'No matches' : 'Watchlist empty'}</div></div>
          ) : (
            <table className="w-full">
              <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase"><th className="text-left px-6 py-3 font-medium">Stock</th><th className="text-left px-6 py-3 font-medium">Notes</th><th className="text-right px-6 py-3 font-medium">Price</th><th className="text-right px-6 py-3 font-medium">Change</th><th className="text-right px-6 py-3 font-medium">Actions</th></tr></thead>
              <tbody>
                {filtered.map(w => (
                  <tr key={w._id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
                    <td className="px-6 py-4"><div className="flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center text-sm font-semibold text-[var(--accent)]">{w.symbol.slice(0, 2)}</div><span className="font-medium">{w.symbol}</span></div></td>
                    <td className="px-6 py-4 text-[var(--text-muted)]">{w.notes || '-'}</td>
                    <td className="px-6 py-4 text-right tabular font-medium">{w.current_price ? `₹${w.current_price.toFixed(2)}` : '-'}</td>
                    <td className="px-6 py-4 text-right">{w.day_change_pct !== undefined ? <span className={`inline-block px-2 py-1 rounded text-sm tabular font-medium ${w.day_change_pct >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>{w.day_change_pct >= 0 ? '+' : ''}{w.day_change_pct.toFixed(2)}%</span> : '-'}</td>
                    <td className="px-6 py-4 text-right"><button onClick={() => removeFromWatchlist(w._id)} className="p-2 text-[var(--text-muted)] hover:text-[#ef4444] hover:bg-[#ef4444]/10 rounded-lg"><Trash2 className="w-4 h-4" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}
