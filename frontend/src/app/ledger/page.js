'use client';
import { useState, useEffect, Fragment } from 'react';
import { HandCoins, Plus, Trash2, X, ArrowUpRight, ArrowDownLeft, Check, Clock, RefreshCw, Calendar, ChevronDown, Pencil } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { getLedger, getLedgerSummary, addLedgerEntry, updateLedgerEntry, settleLedgerEntry, deleteLedgerEntry } from '../../lib/api';

export default function LedgerPage() {
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState({ total_lent: 0, total_borrowed: 0, net_balance: 0, pending_entries: 0, monthly_outgoing: 0 });
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showSettle, setShowSettle] = useState(null);
  const [filter, setFilter] = useState('all');
  const [form, setForm] = useState({ type: 'lent', person_name: '', amount: '', description: '', due_date: '', is_recurring: false, recurring_amount: '', recurring_day: '7', end_date: '' });
  const [settleAmount, setSettleAmount] = useState('');
  const [settleNote, setSettleNote] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [editEntry, setEditEntry] = useState(null);

  const load = async () => {
    setLoading(true);
    const [e, s] = await Promise.all([getLedger(filter !== 'all' ? { type: filter } : {}), getLedgerSummary()]);
    setEntries(e.map(x => ({ ...x, paid: x.settlements?.reduce((sum, s) => sum + s.amount, 0) || 0 })));
    setSummary(s);
    setLoading(false);
  };

  useEffect(() => { load(); }, [filter]);

  useEffect(() => {
    if (editEntry) {
      setForm({
        type: editEntry.type,
        person_name: editEntry.person_name,
        amount: editEntry.amount.toString(),
        description: editEntry.description || '',
        due_date: editEntry.due_date ? editEntry.due_date.split('T')[0] : '',
        is_recurring: editEntry.is_recurring,
        recurring_amount: editEntry.recurring_amount?.toString() || '',
        recurring_day: editEntry.recurring_day?.toString() || '7',
        end_date: editEntry.end_date ? editEntry.end_date.split('T')[0] : ''
      });
    }
  }, [editEntry]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      type: form.type,
      person_name: form.person_name,
      amount: parseFloat(form.amount),
      description: form.description || null,
      due_date: form.due_date || null,
      is_recurring: form.is_recurring,
      recurring_amount: form.is_recurring ? parseFloat(form.recurring_amount) : null,
      recurring_day: form.is_recurring ? parseInt(form.recurring_day) : null,
      end_date: form.is_recurring ? form.end_date : null
    };
    if (editEntry) {
      await updateLedgerEntry(editEntry.id, payload);
      setEditEntry(null);
    } else {
      await addLedgerEntry(payload);
    }
    setForm({ type: 'lent', person_name: '', amount: '', description: '', due_date: '', is_recurring: false, recurring_amount: '', recurring_day: '7', end_date: '' });
    setShowForm(false);
    load();
  };

  const handleSettle = async (id) => {
    await settleLedgerEntry(id, { amount: parseFloat(settleAmount), note: settleNote || null });
    setShowSettle(null);
    setSettleAmount('');
    setSettleNote('');
    load();
  };

  const handleDelete = async (id) => {
    if (confirm('Delete this entry?')) {
      await deleteLedgerEntry(id);
      load();
    }
  };

  const fmt = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold flex items-center gap-2"><HandCoins className="w-6 h-6" /> Ledger</h1>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:opacity-90"><Plus className="w-4 h-4" /> Add Entry</button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">You Lent</div>
            <div className="text-xl font-bold text-[#10b981]">{fmt(summary.total_lent)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">You Borrowed</div>
            <div className="text-xl font-bold text-[#ef4444]">{fmt(summary.total_borrowed)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Net Balance</div>
            <div className={`text-xl font-bold ${summary.net_balance >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{fmt(summary.net_balance)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Monthly EMI</div>
            <div className="text-xl font-bold text-[#f59e0b]">{fmt(summary.monthly_outgoing)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Pending</div>
            <div className="text-xl font-bold">{summary.pending_entries}</div>
          </div>
        </div>

        {/* By Person Summary */}
        {entries.length > 0 && (() => {
          const now = new Date();
          const thisMonth = (d) => { const dt = new Date(d); return dt.getMonth() === now.getMonth() && dt.getFullYear() === now.getFullYear(); };
          const byPerson = entries.filter(e => e.status !== 'settled').reduce((acc, e) => {
            const key = e.person_name;
            if (!acc[key]) acc[key] = { lent: 0, lentEmi: 0, borrowed: 0, borrowedEmi: 0, monthlyEmi: 0, paidThisMonth: 0 };
            const remaining = e.remaining;
            const paidThisMonth = e.settlements?.filter(s => thisMonth(s.date)).reduce((sum, s) => sum + s.amount, 0) || 0;
            if (e.type === 'lent') {
              if (e.is_recurring) { acc[key].lentEmi += remaining; acc[key].monthlyEmi += e.recurring_amount || 0; acc[key].paidThisMonth += paidThisMonth; }
              else acc[key].lent += remaining;
            } else {
              if (e.is_recurring) acc[key].borrowedEmi += remaining;
              else acc[key].borrowed += remaining;
            }
            return acc;
          }, {});
          const people = Object.entries(byPerson).map(([name, v]) => ({ name, ...v, net: (v.lent + v.lentEmi) - (v.borrowed + v.borrowedEmi), dueThisMonth: Math.max(0, v.monthlyEmi - v.paidThisMonth) })).sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
          return people.length > 0 && (
            <div className="mb-6 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
              <div className="text-sm font-medium text-[var(--text-muted)] mb-3">By Person</div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {people.map(p => (
                  <div key={p.name} className="bg-[var(--bg-tertiary)] rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">{p.name}</span>
                      <span className={`font-bold ${p.net >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{p.net >= 0 ? '+' : ''}{fmt(p.net)}</span>
                    </div>
                    <div className="text-xs text-[var(--text-muted)] space-y-1">
                      {(p.lent > 0 || p.lentEmi > 0) && <div className="flex justify-between"><span>Owes you:</span><span className="text-[#10b981]">{fmt(p.lent)}{p.lentEmi > 0 && ` + ${fmt(p.lentEmi)} (EMI)`}</span></div>}
                      {(p.borrowed > 0 || p.borrowedEmi > 0) && <div className="flex justify-between"><span>You owe:</span><span className="text-[#ef4444]">{fmt(p.borrowed)}{p.borrowedEmi > 0 && ` + ${fmt(p.borrowedEmi)} (EMI)`}</span></div>}
                      {(p.dueThisMonth > 0 || p.lent > 0) && <div className="flex justify-between"><span>Due this month:</span><span className="text-[#f59e0b]">{p.dueThisMonth > 0 ? fmt(p.dueThisMonth) : ''}{p.dueThisMonth > 0 && p.lent > 0 ? ' + ' : ''}{p.lent > 0 ? `${fmt(p.lent)} (misc)` : ''}</span></div>}
                      {p.paidThisMonth > 0 && <div className="flex justify-between"><span>Paid this month:</span><span className="text-[#10b981]">{fmt(p.paidThisMonth)}</span></div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}

        {/* Filter */}
        <div className="flex gap-2 mb-4">
          {['all', 'lent', 'borrowed'].map(f => (
            <button key={f} onClick={() => setFilter(f)} className={`px-4 py-2 rounded-lg text-sm font-medium ${filter === f ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-secondary)]'}`}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Entries Table */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
          {loading ? (
            <div className="p-6 space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-[var(--border)] rounded animate-pulse" />)}</div>
          ) : entries.length === 0 ? (
            <div className="p-12 text-center text-[var(--text-muted)]">No entries yet</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                  <th className="w-8"></th>
                  <th className="text-left px-4 py-3 font-medium">Person</th>
                  <th className="text-left px-4 py-3 font-medium">Type</th>
                  <th className="text-right px-4 py-3 font-medium">Amount</th>
                  <th className="text-right px-4 py-3 font-medium">Paid</th>
                  <th className="text-center px-4 py-3 font-medium">EMI</th>
                  <th className="text-left px-4 py-3 pl-12 font-medium">Status</th>
                  <th className="w-24"></th>
                </tr>
              </thead>
              <tbody>
                {entries.map(e => (
                  <Fragment key={e.id}>
                  <tr className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]" onClick={() => setExpanded(expanded === e.id ? null : e.id)}>
                    <td className="px-2 py-3 cursor-pointer">
                      <ChevronDown className={`w-4 h-4 text-[var(--text-muted)] transition-transform ${expanded === e.id ? 'rotate-180' : ''}`} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="font-medium">{e.person_name}</div>
                        {e.is_recurring && <RefreshCw className="w-3 h-3 text-[#f59e0b]" />}
                      </div>
                      {e.description && <div className="text-xs text-[var(--text-muted)]">{e.description}</div>}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${e.type === 'lent' ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>
                        {e.type === 'lent' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownLeft className="w-3 h-3" />}
                        {e.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium tabular">{fmt(e.amount)}</td>
                    <td className="px-4 py-3 text-right tabular">{fmt(e.paid)}</td>
                    <td className="px-4 py-3 text-center">
                      {e.is_recurring ? <span className="font-medium text-[#f59e0b]">{fmt(e.recurring_amount)}/mo</span> : '-'}
                    </td>
                    <td className="px-4 py-3 pl-12">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${e.status === 'settled' ? 'bg-[#10b981]/10 text-[#10b981]' : e.status === 'partial' ? 'bg-[#f59e0b]/10 text-[#f59e0b]' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)]'}`}>
                        {e.status === 'settled' ? <Check className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                        {e.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={(ev) => { ev.stopPropagation(); setEditEntry(e); setShowForm(true); }} className="p-1.5 text-[var(--text-muted)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/10 rounded" title="Edit">
                          <Pencil className="w-4 h-4" />
                        </button>
                        {e.status !== 'settled' && (
                          <button onClick={(ev) => { ev.stopPropagation(); setShowSettle(e.id); setSettleAmount(e.is_recurring ? e.recurring_amount?.toString() : e.remaining.toString()); }} className="p-1.5 text-[var(--text-muted)] hover:text-[#10b981] hover:bg-[#10b981]/10 rounded" title="Settle">
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        <button onClick={(ev) => { ev.stopPropagation(); handleDelete(e.id); }} className="p-1.5 text-[var(--text-muted)] hover:text-[#ef4444] hover:bg-[#ef4444]/10 rounded" title="Delete">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expanded === e.id && (
                    <tr key={`${e.id}-details`} className="bg-[var(--bg-tertiary)]">
                      <td colSpan={8} className="px-6 py-4">
                        <div className="grid grid-cols-2 gap-6 text-sm">
                          <div>
                            <div className="text-[var(--text-muted)] mb-2">Details</div>
                            <div className="space-y-1">
                              <div>Date: {new Date(e.date).toLocaleDateString('en-IN')}</div>
                              {e.due_date && <div>Due: {new Date(e.due_date).toLocaleDateString('en-IN')}</div>}
                              {e.end_date && <div>End: {new Date(e.end_date).toLocaleDateString('en-IN')}</div>}
                              {e.is_recurring && e.recurring_day && <div>EMI Day: {e.recurring_day}</div>}
                              {e.emis_remaining !== null && <div>EMIs Left: {e.emis_remaining}</div>}
                              <div>Remaining: {fmt(e.remaining)}</div>
                            </div>
                          </div>
                          <div>
                            <div className="text-[var(--text-muted)] mb-2">Payments ({e.settlements?.length || 0})</div>
                            {e.settlements?.length > 0 ? (
                              <div className="space-y-1 max-h-32 overflow-y-auto">
                                {e.settlements.map((s, i) => (
                                  <div key={i} className="flex justify-between text-xs">
                                    <span>{new Date(s.date).toLocaleDateString('en-IN')}</span>
                                    <span className="text-[#10b981]">+{fmt(s.amount)}</span>
                                  </div>
                                ))}
                              </div>
                            ) : <div className="text-[var(--text-muted)] text-xs">No payments yet</div>}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Add Entry Modal */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => { setShowForm(false); setEditEntry(null); setForm({ type: 'lent', person_name: '', amount: '', description: '', due_date: '', is_recurring: false, recurring_amount: '', recurring_day: '7', end_date: '' }); }}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">{editEntry ? 'Edit Entry' : 'Add Entry'}</h2>
                <button onClick={() => { setShowForm(false); setEditEntry(null); setForm({ type: 'lent', person_name: '', amount: '', description: '', due_date: '', is_recurring: false, recurring_amount: '', recurring_day: '7', end_date: '' }); }} className="p-2 text-[var(--text-muted)] hover:text-white rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Type</label>
                  <div className="grid grid-cols-2 gap-2">
                    {['lent', 'borrowed'].map(t => (
                      <button key={t} type="button" onClick={() => setForm({ ...form, type: t })} className={`py-2 rounded-lg text-sm font-medium ${form.type === t ? (t === 'lent' ? 'bg-[#10b981] text-white' : 'bg-[#ef4444] text-white') : 'bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-secondary)]'}`}>
                        {t === 'lent' ? 'I Lent / Paying EMI' : 'I Borrowed'}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Person Name</label>
                  <input value={form.person_name} onChange={e => setForm({ ...form, person_name: e.target.value })} placeholder="Rahul" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required />
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Total Amount (₹)</label>
                  <input type="number" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} placeholder="100000" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required />
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Description</label>
                  <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Loan 1 - HDFC" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" />
                </div>
                
                {/* Recurring Toggle */}
                <div className="flex items-center gap-3">
                  <button type="button" onClick={() => setForm({ ...form, is_recurring: !form.is_recurring })} className={`relative w-12 h-6 rounded-full transition-colors ${form.is_recurring ? 'bg-[#f59e0b]' : 'bg-[var(--border)]'}`}>
                    <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${form.is_recurring ? 'left-7' : 'left-1'}`} />
                  </button>
                  <span className="text-sm text-[var(--text-secondary)]">Recurring EMI Payment</span>
                </div>

                {form.is_recurring && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-[var(--text-secondary)] mb-2">EMI Amount (₹)</label>
                        <input type="number" value={form.recurring_amount} onChange={e => setForm({ ...form, recurring_amount: e.target.value })} placeholder="10335" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required />
                      </div>
                      <div>
                        <label className="block text-sm text-[var(--text-secondary)] mb-2">EMI Day</label>
                        <input type="number" min="1" max="31" value={form.recurring_day} onChange={e => setForm({ ...form, recurring_day: e.target.value })} placeholder="7" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm text-[var(--text-secondary)] mb-2">EMI End Date</label>
                      <input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required />
                    </div>
                  </>
                )}

                {!form.is_recurring && (
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">Due Date (optional)</label>
                    <input type="date" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" />
                  </div>
                )}

                <button type="submit" className="w-full py-3 bg-[var(--accent)] text-white rounded-lg font-medium hover:opacity-90">Add Entry</button>
              </form>
            </div>
          </div>
        )}

        {/* Settle Modal */}
        {showSettle && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowSettle(null)}>
            <div className="w-full max-w-sm bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Record Payment</h2>
                <button onClick={() => setShowSettle(null)} className="p-2 text-[var(--text-muted)] hover:text-white rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Amount (₹)</label>
                  <input type="number" value={settleAmount} onChange={e => setSettleAmount(e.target.value)} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" required />
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Note (optional)</label>
                  <input value={settleNote} onChange={e => setSettleNote(e.target.value)} placeholder="Feb 2026 EMI paid" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-white focus:border-[var(--accent)]" />
                </div>
                <button onClick={() => handleSettle(showSettle)} className="w-full py-3 bg-[#10b981] text-white rounded-lg font-medium hover:opacity-90">Record Payment</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
