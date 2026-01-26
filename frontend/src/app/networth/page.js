'use client';
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Wallet, Plus, Trash2, TrendingUp, Building, Landmark, PiggyBank, Coins, Pencil, ChevronLeft, ChevronRight, CheckCircle, XCircle, Upload, Camera } from 'lucide-react';
import { api } from '../../lib/api';
import Navbar from '../../components/Navbar';

const COLORS = ['#6366f1', '#22c55e', '#eab308', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899'];
const ICONS = { 'Stocks': TrendingUp, 'Mutual Funds': Landmark, 'Fixed Deposits': Building, 'PPF': PiggyBank, 'Gold': Coins, 'Real Estate': Building };

export default function NetWorthPage() {
  const [data, setData] = useState(null);
  const [assets, setAssets] = useState([]);
  const [history, setHistory] = useState([]);
  const [monthly, setMonthly] = useState(null);
  const [historyDetail, setHistoryDetail] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [year, setYear] = useState(new Date().getFullYear());
  const [view, setView] = useState('overview');
  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [importText, setImportText] = useState('');
  const [editAsset, setEditAsset] = useState(null);
  const [newAsset, setNewAsset] = useState({ name: '', category: 'Fixed Deposits', value: '' });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [nw, assetList, hist, monthlyData, detail] = await Promise.all([
        api('/api/networth/'),
        api('/api/networth/assets'),
        api('/api/networth/history'),
        api(`/api/networth/monthly?year=${year}`),
        api(`/api/networth/history-detail?year=${year}`)
      ]);
      setData(nw);
      setAssets(assetList.assets || []);
      setHistory(hist.history || []);
      setMonthly(monthlyData);
      setHistoryDetail(detail.history || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [year]);

  const addAsset = async () => {
    if (!newAsset.name || !newAsset.value) return;
    try {
      await api('/api/networth/asset', { method: 'POST', body: JSON.stringify({ ...newAsset, value: parseFloat(newAsset.value) }) });
      setShowAdd(false);
      setNewAsset({ name: '', category: 'Fixed Deposits', value: '' });
      fetchData();
    } catch (e) { console.error(e); }
  };

  const deleteAsset = async (id) => {
    try {
      await api(`/api/networth/asset/${id}`, { method: 'DELETE' });
      fetchData();
    } catch (e) { console.error(e); }
  };

  const updateAsset = async () => {
    if (!editAsset) return;
    try {
      await api(`/api/networth/asset/${editAsset._id}`, { method: 'PUT', body: JSON.stringify({ name: editAsset.name, category: editAsset.category, value: parseFloat(editAsset.value) }) });
      setEditAsset(null);
      fetchData();
    } catch (e) { console.error(e); }
  };

  const importHistory = async () => {
    try {
      // Parse detailed format: date, total, then breakdown items
      // Example: "2025-01-01, 274422, Union:143352, Mutual:80461, Stocks:26609"
      const lines = importText.trim().split('\n').filter(l => l.trim());
      const snapshots = lines.map(line => {
        const parts = line.split(',').map(s => s.trim());
        const date = parts[0];
        const total = parseFloat(parts[1]?.replace(/[₹,]/g, '') || 0);
        const breakdown = {};
        
        for (let i = 2; i < parts.length; i++) {
          const [key, val] = parts[i].split(':').map(s => s.trim());
          if (key && val) breakdown[key] = parseFloat(val.replace(/[₹,]/g, ''));
        }
        
        return { date, total, breakdown };
      }).filter(s => s.date && s.total);
      
      await api('/api/networth/import-history', { method: 'POST', body: JSON.stringify({ snapshots }) });
      setShowImport(false);
      setImportText('');
      fetchData();
    } catch (e) { console.error(e); }
  };

  const takeSnapshot = async () => {
    try {
      await api('/api/networth/snapshot', { method: 'POST' });
      fetchData();
    } catch (e) { console.error(e); }
  };

  const chartData = data ? Object.entries(data.categories || {}).map(([name, value], i) => ({ name, value, color: COLORS[i % COLORS.length] })) : [];

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-6">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Net Worth</h1>
            <p className="text-[var(--text-secondary)]">Track all your assets in one place</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex gap-1 bg-[var(--bg-tertiary)] rounded-lg p-1">
              <button onClick={() => setView('overview')} className={`px-3 py-1.5 rounded text-sm ${view === 'overview' ? 'bg-[#6366f1] text-white' : 'text-[var(--text-secondary)]'}`}>Overview</button>
              <button onClick={() => setView('monthly')} className={`px-3 py-1.5 rounded text-sm ${view === 'monthly' ? 'bg-[#6366f1] text-white' : 'text-[var(--text-secondary)]'}`}>Monthly</button>
            </div>
            <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] text-white rounded-lg">
              <Plus className="w-4 h-4" />Add Asset
            </button>
          </div>
        </div>

        {view === 'overview' ? (
          <>
        {/* Total Net Worth Card */}
        <div className="bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <Wallet className="w-8 h-8" />
            <span className="text-lg opacity-90">Total Net Worth</span>
          </div>
          <div className="text-4xl font-bold">₹{(data?.total_networth || 0).toLocaleString('en-IN')}</div>
          <div className="text-sm opacity-75 mt-1">{data?.assets_count || 0} assets tracked</div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Allocation Chart */}
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Asset Allocation</h2>
            {chartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}>
                      {chartData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip formatter={(v) => `₹${v.toLocaleString('en-IN')}`} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-[var(--text-secondary)]">Add assets to see allocation</div>
            )}
          </div>

          {/* Category Breakdown */}
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Breakdown</h2>
            <div className="space-y-3">
              {chartData.map((item, i) => {
                const Icon = ICONS[item.name] || Wallet;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <div className="p-2 rounded-lg" style={{ backgroundColor: `${item.color}20` }}>
                      <Icon className="w-5 h-5" style={{ color: item.color }} />
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between">
                        <span className="text-[var(--text-primary)]">{item.name}</span>
                        <span className="font-medium text-[var(--text-primary)]">₹{item.value.toLocaleString('en-IN')}</span>
                      </div>
                      <div className="w-full bg-[var(--bg-tertiary)] rounded-full h-1.5 mt-1">
                        <div className="h-1.5 rounded-full" style={{ width: `${data?.allocation?.[item.name] || 0}%`, backgroundColor: item.color }}></div>
                      </div>
                    </div>
                    <span className="text-sm text-[var(--text-secondary)] w-12 text-right">{data?.allocation?.[item.name] || 0}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Other Assets List */}
        {assets.length > 0 && (
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Other Assets</h2>
            <div className="space-y-2">
              {assets.map((a) => (
                <div key={a._id} className="flex items-center justify-between p-3 bg-[var(--bg-tertiary)] rounded-lg">
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">{a.name}</div>
                    <div className="text-sm text-[var(--text-secondary)]">{a.category}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-medium text-[var(--text-primary)]">₹{(a.value || 0).toLocaleString('en-IN')}</span>
                    <button onClick={() => setEditAsset(a)} className="p-1 text-[var(--text-secondary)] hover:text-[#6366f1]">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => deleteAsset(a._id)} className="p-1 text-[var(--text-secondary)] hover:text-[#ef4444]">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
          </>
        ) : (
          <>
            {/* Monthly View */}
            <div className="flex items-center justify-between">
              <button onClick={() => setYear(year - 1)} className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg">
                <ChevronLeft className="w-5 h-5 text-[var(--text-secondary)]" />
              </button>
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">{year}</h2>
              <div className="flex items-center gap-2">
                <button onClick={takeSnapshot} className="flex items-center gap-1 px-3 py-1.5 bg-[#22c55e] text-white rounded-lg text-sm hover:bg-[#16a34a]">
                  <Camera className="w-4 h-4" />Snapshot
                </button>
                <button onClick={() => setShowImport(true)} className="flex items-center gap-1 px-3 py-1.5 bg-[var(--bg-tertiary)] text-[var(--text-secondary)] rounded-lg text-sm hover:bg-[var(--border)]">
                  <Upload className="w-4 h-4" />Import
                </button>
                <button onClick={() => setYear(year + 1)} className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg">
                  <ChevronRight className="w-5 h-5 text-[var(--text-secondary)]" />
                </button>
              </div>
            </div>

            {/* Performance Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
                <div className="text-sm text-[var(--text-secondary)]">YTD Growth</div>
                <div className={`text-2xl font-bold ${(monthly?.ytd_growth || 0) >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                  {(monthly?.ytd_growth || 0) >= 0 ? '+' : ''}{monthly?.ytd_growth || 0}%
                </div>
              </div>
              <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
                <div className="text-sm text-[var(--text-secondary)]">Annualized</div>
                <div className={`text-2xl font-bold ${(monthly?.annualized_growth || 0) >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                  {(monthly?.annualized_growth || 0) >= 0 ? '+' : ''}{monthly?.annualized_growth || 0}%
                </div>
              </div>
              <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
                <div className="text-sm text-[var(--text-secondary)]">Rating</div>
                <div className={`text-2xl font-bold ${monthly?.rating === 'Excellent' || monthly?.rating === 'Good' ? 'text-[#22c55e]' : monthly?.rating === 'Average' ? 'text-[#eab308]' : 'text-[#ef4444]'}`}>
                  {monthly?.rating || '-'}
                </div>
              </div>
              <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
                <div className="text-sm text-[var(--text-secondary)]">Target (15%)</div>
                <div className="text-2xl font-bold">
                  {monthly?.performance?.good_growth ? <CheckCircle className="w-6 h-6 text-[#22c55e]" /> : <XCircle className="w-6 h-6 text-[#ef4444]" />}
                </div>
              </div>
            </div>

            {/* Benchmark Comparison */}
            <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Benchmark Comparison</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Inflation (6%)', key: 'beating_inflation' },
                  { label: 'FD Rate (7%)', key: 'beating_fd' },
                  { label: 'Nifty Avg (12%)', key: 'beating_nifty' },
                  { label: 'Good Growth (15%)', key: 'good_growth' }
                ].map(b => (
                  <div key={b.key} className={`p-3 rounded-lg flex items-center gap-2 ${monthly?.performance?.[b.key] ? 'bg-[#22c55e]/10' : 'bg-[#ef4444]/10'}`}>
                    {monthly?.performance?.[b.key] ? <CheckCircle className="w-5 h-5 text-[#22c55e]" /> : <XCircle className="w-5 h-5 text-[#ef4444]" />}
                    <span className="text-sm text-[var(--text-primary)]">{b.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Monthly Breakdown */}
            <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Monthly Net Worth</h3>
              <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {monthly?.monthly?.map(m => {
                  const detail = historyDetail.find(h => new Date(h.date).getMonth() + 1 === m.month);
                  return (
                    <div 
                      key={m.month} 
                      onClick={() => detail?.breakdown && Object.keys(detail.breakdown).length > 0 && setSelectedMonth({ ...m, breakdown: detail.breakdown, date: detail.date })}
                      className={`p-3 rounded-lg border cursor-pointer hover:scale-105 transition-transform ${!m.has_data ? 'border-[var(--border)] bg-[var(--bg-tertiary)] opacity-50' : m.change >= 0 ? 'border-[#22c55e]/30 bg-[#22c55e]/5' : 'border-[#ef4444]/30 bg-[#ef4444]/5'}`}
                    >
                      <div className="text-sm text-[var(--text-secondary)]">{m.month_name}</div>
                      <div className="text-sm font-medium text-[var(--text-primary)]">₹{(m.value / 100000).toFixed(1)}L</div>
                      {m.has_data ? (
                        <div className={`text-xs ${m.change_pct >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                          {m.change_pct >= 0 ? '+' : ''}{m.change_pct.toFixed(1)}%
                        </div>
                      ) : (
                        <div className="text-xs text-[var(--text-secondary)]">No data</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* Add Asset Modal */}
        {showAdd && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-[var(--bg-secondary)] rounded-xl p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Add Asset</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Asset Name</label>
                  <input value={newAsset.name} onChange={(e) => setNewAsset({ ...newAsset, name: e.target.value })} className="w-full mt-1 px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)]" placeholder="e.g., SBI FD, PPF Account" />
                </div>
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Category</label>
                  <select value={newAsset.category} onChange={(e) => setNewAsset({ ...newAsset, category: e.target.value })} className="w-full mt-1 px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)]">
                    <option>Fixed Deposits</option>
                    <option>PPF</option>
                    <option>NPS</option>
                    <option>EPF</option>
                    <option>Gold</option>
                    <option>Real Estate</option>
                    <option>Savings</option>
                    <option>Others</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Current Value (₹)</label>
                  <input type="number" value={newAsset.value} onChange={(e) => setNewAsset({ ...newAsset, value: e.target.value })} className="w-full mt-1 px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)]" placeholder="100000" />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button onClick={() => setShowAdd(false)} className="flex-1 px-4 py-2 bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-lg">Cancel</button>
                <button onClick={addAsset} className="flex-1 px-4 py-2 bg-[#6366f1] text-white rounded-lg">Add Asset</button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Asset Modal */}
        {editAsset && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-[var(--bg-secondary)] rounded-xl p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Edit Asset</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Asset Name</label>
                  <input value={editAsset.name} onChange={(e) => setEditAsset({ ...editAsset, name: e.target.value })} className="w-full mt-1 px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)]" />
                </div>
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Category</label>
                  <select value={editAsset.category} onChange={(e) => setEditAsset({ ...editAsset, category: e.target.value })} className="w-full mt-1 px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)]">
                    <option>Fixed Deposits</option><option>PPF</option><option>NPS</option><option>EPF</option><option>Gold</option><option>Real Estate</option><option>Savings</option><option>Others</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Current Value (₹)</label>
                  <input type="number" value={editAsset.value} onChange={(e) => setEditAsset({ ...editAsset, value: e.target.value })} className="w-full mt-1 px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)]" />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button onClick={() => setEditAsset(null)} className="flex-1 px-4 py-2 bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-lg">Cancel</button>
                <button onClick={updateAsset} className="flex-1 px-4 py-2 bg-[#6366f1] text-white rounded-lg">Save</button>
              </div>
            </div>
          </div>
        )}

        {/* Month Detail Modal */}
        {selectedMonth && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedMonth(null)}>
            <div className="bg-[var(--bg-secondary)] rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">{selectedMonth.month_name} {year}</h3>
              <p className="text-sm text-[var(--text-secondary)] mb-4">{selectedMonth.date}</p>
              <div className="text-2xl font-bold text-[var(--text-primary)] mb-4">₹{selectedMonth.value.toLocaleString('en-IN')}</div>
              <div className="space-y-2">
                {Object.entries(selectedMonth.breakdown || {}).sort((a, b) => b[1] - a[1]).map(([name, value]) => (
                  <div key={name} className="flex justify-between items-center p-2 bg-[var(--bg-tertiary)] rounded-lg">
                    <span className="text-[var(--text-primary)]">{name}</span>
                    <span className="font-medium text-[var(--text-primary)]">₹{value.toLocaleString('en-IN')}</span>
                  </div>
                ))}
              </div>
              <button onClick={() => setSelectedMonth(null)} className="w-full mt-4 px-4 py-2 bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-lg">Close</button>
            </div>
          </div>
        )}

        {/* Import History Modal */}
        {showImport && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-[var(--bg-secondary)] rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Import Net Worth History</h3>
              <p className="text-sm text-[var(--text-secondary)] mb-4">Paste your data with detailed breakdown:</p>
              <div className="text-xs text-[var(--text-secondary)] mb-2 bg-[var(--bg-tertiary)] p-3 rounded font-mono">
                Format: <code>Date, Total, Asset1:Value, Asset2:Value, ...</code><br/><br/>
                Example:<br/>
                2025-01-01, 274422, Union:143352, Mutual:80461, Stocks:26609, Cash:3000, Savings:21000<br/>
                2025-02-01, 271142, Union:102834, Mutual:85461, Stocks:61247, Cash:600, Savings:21000
              </div>
              <textarea 
                value={importText} 
                onChange={(e) => setImportText(e.target.value)} 
                className="w-full h-48 px-3 py-2 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] text-xs font-mono"
                placeholder="2025-01-01, 274422, Union:143352, Mutual:80461, Stocks:26609, Cash:3000, Savings:21000"
              />
              <div className="flex gap-3 mt-4">
                <button onClick={() => { setShowImport(false); setImportText(''); }} className="flex-1 px-4 py-2 bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-lg">Cancel</button>
                <button onClick={importHistory} className="flex-1 px-4 py-2 bg-[#6366f1] text-white rounded-lg">Import</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
