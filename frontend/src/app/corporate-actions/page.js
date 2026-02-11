'use client';
import { useState, useEffect } from 'react';
import { Calendar, DollarSign, Scissors, Bell } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function CorporateActionsPage() {
  const [actions, setActions] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [dividends, setDividends] = useState([]);
  const [expectedIncome, setExpectedIncome] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('upcoming');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [actionsData, divData] = await Promise.all([
        api('/api/market/corporate-actions'),
        api('/api/finance/dividends')
      ]);
      setActions(actionsData.actions || []);
      setUpcoming([...(actionsData.upcoming || []), ...(divData.upcoming || [])]);
      setDividends(divData.dividends || []);
      setExpectedIncome(divData.expected_income || 0);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '0';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <h1 className="text-2xl font-bold mb-6">Corporate Actions</h1>

        {/* Summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)] mb-1">
              <Calendar className="w-4 h-4" /> Upcoming
            </div>
            <div className="text-xl font-semibold">{upcoming.length}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)] mb-1">
              <DollarSign className="w-4 h-4" /> Expected Dividends
            </div>
            <div className="text-xl font-semibold text-[#10b981]">₹{fmt(expectedIncome)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)] mb-1">
              <Scissors className="w-4 h-4" /> Splits (1Y)
            </div>
            <div className="text-xl font-semibold">{actions.filter(a => a.type === 'SPLIT').length}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)] mb-1">
              <Bell className="w-4 h-4" /> Total Actions
            </div>
            <div className="text-xl font-semibold">{actions.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-lg w-fit">
          {['upcoming', 'dividends', 'all'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 py-2 rounded-md text-sm font-medium capitalize ${activeTab === tab ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-muted)] hover:text-white'}`}>
              {tab}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="h-16 bg-[var(--bg-secondary)] rounded-lg animate-pulse" />)}</div>
        ) : (
          <>
            {/* Upcoming Tab */}
            {activeTab === 'upcoming' && (
              upcoming.length === 0 ? (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
                  <Calendar className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                  <div className="text-[var(--text-muted)]">No upcoming corporate actions for your holdings</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {upcoming.map((a, i) => (
                    <div key={i} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${a.type === 'DIVIDEND' ? 'bg-[#10b981]/10' : 'bg-[var(--accent)]/10'}`}>
                          {a.type === 'DIVIDEND' ? <DollarSign className="w-5 h-5 text-[#10b981]" /> : <Scissors className="w-5 h-5 text-[var(--accent)]" />}
                        </div>
                        <div>
                          <div className="font-medium">{a.symbol}</div>
                          <div className="text-sm text-[var(--text-muted)]">{a.description}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">{a.date}</div>
                        <div className="text-sm text-[var(--text-muted)]">{a.type}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}

            {/* Dividends Tab */}
            {activeTab === 'dividends' && (
              dividends.length === 0 ? (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
                  <DollarSign className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                  <div className="text-[var(--text-muted)]">No dividend history found</div>
                </div>
              ) : (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                        <th className="text-left px-4 py-3">Stock</th>
                        <th className="text-left px-4 py-3">Ex-Date</th>
                        <th className="text-right px-4 py-3">Per Share</th>
                        <th className="text-right px-4 py-3">Qty</th>
                        <th className="text-right px-4 py-3">Income</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dividends.map((d, i) => (
                        <tr key={i} className="border-b border-[var(--border)] hover:bg-[var(--bg-hover)]">
                          <td className="px-4 py-3 font-medium">{d.symbol}</td>
                          <td className="px-4 py-3">{d.date}</td>
                          <td className="px-4 py-3 text-right">₹{fmt(d.value)}</td>
                          <td className="px-4 py-3 text-right">{d.quantity}</td>
                          <td className="px-4 py-3 text-right text-[#10b981] font-medium">₹{fmt(d.expected_income)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            )}

            {/* All Actions Tab */}
            {activeTab === 'all' && (
              actions.length === 0 ? (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
                  <Bell className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                  <div className="text-[var(--text-muted)]">No corporate actions found</div>
                </div>
              ) : (
                <div className="space-y-2">
                  {actions.slice(0, 30).map((a, i) => (
                    <div key={i} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${a.type === 'DIVIDEND' ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[var(--accent)]/10 text-[var(--accent)]'}`}>{a.type}</span>
                        <span className="font-medium">{a.symbol}</span>
                        <span className="text-sm text-[var(--text-muted)]">{a.description}</span>
                      </div>
                      <span className="text-sm">{a.date}</span>
                    </div>
                  ))}
                </div>
              )
            )}
          </>
        )}
      </main>
    </div>
  );
}
