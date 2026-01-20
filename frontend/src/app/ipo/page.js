'use client';
import { useState, useEffect } from 'react';
import { Calendar, RefreshCw } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function IPOPage() {
  const [ipos, setIpos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const loadIPOs = async () => { setLoading(true); try { setIpos(await api('/api/ipo/gmp')); } catch (e) {} setLoading(false); };
  useEffect(() => { loadIPOs(); }, []);

  const filteredIpos = filter === 'all' ? ipos : ipos.filter(i => i.type?.toUpperCase() === filter.toUpperCase());

  const getStyle = (action) => {
    if (action === 'APPLY') return 'bg-[#10b981]/10 text-[#10b981]';
    if (action === 'MAY APPLY') return 'bg-[#6366f1]/10 text-[#6366f1]';
    if (action === 'RISKY') return 'bg-[#eab308]/10 text-[#eab308]';
    return 'bg-[#ef4444]/10 text-[#ef4444]';
  };

  const fmt = (n) => n?.toLocaleString('en-IN') || '0';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">IPO Tracker</h1>
          <button onClick={loadIPOs} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-sm text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh</button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-lg w-fit">
          {[['all', 'All'], ['Mainboard', 'Mainboard'], ['SME', 'SME']].map(([key, label]) => (
            <button key={key} onClick={() => setFilter(key)} className={`px-4 py-2 rounded-md text-sm font-medium ${filter === key ? 'bg-[#6366f1] text-white' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}`}>
              {label} {key !== 'all' && <span className="ml-1 text-xs">({ipos.filter(i => i.type?.toUpperCase() === key.toUpperCase()).length})</span>}
            </button>
          ))}
        </div>

        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
          {loading ? <div className="p-6 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-[var(--border)] rounded animate-pulse" />)}</div> : filteredIpos.length === 0 ? (
            <div className="p-12 text-center"><Calendar className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" /><div className="text-[var(--text-muted)]">No IPO data</div></div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                  <th className="text-left px-6 py-3 font-medium">IPO Name</th>
                  <th className="text-left px-6 py-3 font-medium">Type</th>
                  <th className="text-left px-6 py-3 font-medium">Status</th>
                  <th className="text-left px-6 py-3 font-medium">Dates</th>
                  <th className="text-right px-6 py-3 font-medium">Price</th>
                  <th className="text-right px-6 py-3 font-medium">Lot</th>
                  <th className="text-right px-6 py-3 font-medium">Min Amt</th>
                  <th className="text-right px-6 py-3 font-medium">GMP</th>
                  <th className="text-right px-6 py-3 font-medium">Gain %</th>
                  <th className="text-center px-6 py-3 font-medium">Action</th>
                </tr></thead>
                <tbody>
                  {filteredIpos.map((ipo, i) => (
                    <tr key={i} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-tertiary)]">
                      <td className="px-6 py-4">
                        <div className="font-medium">{ipo.name}</div>
                        {ipo.review && <div className="text-sm text-[var(--text-muted)]">{ipo.review}</div>}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${ipo.type?.toUpperCase() === 'MAINBOARD' ? 'bg-[#6366f1]/10 text-[#6366f1]' : 'bg-[#f59e0b]/10 text-[#f59e0b]'}`}>{ipo.type}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${ipo.status === 'OPEN' ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#6366f1]/10 text-[#6366f1]'}`}>{ipo.status}</span>
                      </td>
                      <td className="px-6 py-4 text-[var(--text-muted)] text-sm">{ipo.dates || '-'}</td>
                      <td className="px-6 py-4 text-right tabular font-medium">₹{ipo.price}</td>
                      <td className="px-6 py-4 text-right tabular text-[var(--text-secondary)]">{ipo.lot_size}</td>
                      <td className="px-6 py-4 text-right tabular font-medium">₹{fmt(ipo.min_investment)}</td>
                      <td className="px-6 py-4 text-right">
                        <span className={`tabular font-medium ${ipo.gmp > 0 ? 'text-[#10b981]' : ipo.gmp < 0 ? 'text-[#ef4444]' : 'text-[var(--text-muted)]'}`}>{ipo.gmp > 0 ? '+' : ''}₹{ipo.gmp}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={`inline-block px-2 py-1 rounded text-sm tabular font-medium ${ipo.gmp_pct > 0 ? 'bg-[#10b981]/10 text-[#10b981]' : ipo.gmp_pct < 0 ? 'bg-[#ef4444]/10 text-[#ef4444]' : 'bg-[var(--border)] text-[var(--text-muted)]'}`}>{ipo.gmp_pct > 0 ? '+' : ''}{ipo.gmp_pct}%</span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${getStyle(ipo.action)}`}>{ipo.action}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <p className="mt-4 text-sm text-[var(--text-muted)] text-center">Data from IPO Watch. GMP is indicative. Lot sizes are estimated.</p>
      </main>
    </div>
  );
}
