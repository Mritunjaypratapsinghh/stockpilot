'use client';
import { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Edit2, X, TrendingUp, BarChart3, Search, Upload, PieChart, Percent, ArrowDownLeft, ArrowUpRight, Calendar, Download, DollarSign } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { getDashboard, addTransaction, importHoldings, api, getDividendSummary, addDividend, getDividends, deleteDividend, downloadExport } from '../../lib/api';

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [xirr, setXirr] = useState(null);
  const [summary, setSummary] = useState({ invested: 0, current: 0, pnl: 0, pnl_pct: 0 });
  const [dividends, setDividends] = useState([]);
  const [divSummary, setDivSummary] = useState({ total_dividend: 0, dividend_yield: 0, by_year: [], by_symbol: [] });
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [showTxn, setShowTxn] = useState(false);
  const [showDiv, setShowDiv] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [importing, setImporting] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ symbol: '', name: '', quantity: '', avg_price: '', holding_type: 'EQUITY' });
  const [txnForm, setTxnForm] = useState({ symbol: '', type: 'BUY', quantity: '', price: '', date: new Date().toISOString().split('T')[0], amount: '', inputMode: 'qty', holding_type: 'EQUITY' });
  const [divForm, setDivForm] = useState({ symbol: '', amount: '', ex_date: new Date().toISOString().split('T')[0] });
  const [activeTab, setActiveTab] = useState('holdings');
  const [holdingFilter, setHoldingFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [symbolSearch, setSymbolSearch] = useState('');
  const [symbolResults, setSymbolResults] = useState([]);
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);
  const searchTimeout = useRef(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [data, divs, divSum] = await Promise.all([getDashboard(), getDividends(), getDividendSummary()]);
      setHoldings(data.holdings || []);
      setSectors(data.sectors || []);
      setXirr(data.xirr);
      setTransactions(data.transactions || []);
      setSummary(data.summary || { invested: 0, current: 0, pnl: 0, pnl_pct: 0 });
      setDividends(divs || []);
      setDivSummary(divSum || { total_dividend: 0, dividend_yield: 0, by_year: [], by_symbol: [] });
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const searchSymbol = async (query) => {
    if (query.length < 2) { setSymbolResults([]); return; }
    try {
      const results = await api(`/api/market/search?q=${query}`);
      setSymbolResults(results.slice(0, 5));
      setShowSymbolDropdown(true);
    } catch { setSymbolResults([]); }
  };

  const handleSymbolInput = (value) => {
    setSymbolSearch(value);
    setTxnForm({ ...txnForm, symbol: value.toUpperCase() });
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => searchSymbol(value), 300);
  };

  const selectSymbol = (symbol, name) => {
    setTxnForm({ ...txnForm, symbol });
    setSymbolSearch(symbol);
    setShowSymbolDropdown(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await api(`/api/portfolio/holdings/${editId}`, { method: 'PUT', body: JSON.stringify({ quantity: parseFloat(form.quantity), avg_price: parseFloat(form.avg_price) }) });
      } else {
        await api('/api/portfolio/holdings', { method: 'POST', body: JSON.stringify({ ...form, quantity: parseFloat(form.quantity), avg_price: parseFloat(form.avg_price) }) });
      }
      setShowForm(false); setEditId(null); setForm({ symbol: '', name: '', quantity: '', avg_price: '', holding_type: 'EQUITY' });
      loadData();
    } catch (err) { alert(err.message); }
  };

  const handleTxnSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { symbol: txnForm.symbol, type: txnForm.type, price: parseFloat(txnForm.price), date: txnForm.date, holding_type: txnForm.holding_type };
      if (txnForm.inputMode === 'amt') {
        payload.amount = parseFloat(txnForm.amount);
      } else {
        payload.quantity = parseFloat(txnForm.quantity);
      }
      await addTransaction(payload);
      setShowTxn(false);
      setTxnForm({ symbol: '', type: 'BUY', quantity: '', price: '', date: new Date().toISOString().split('T')[0], amount: '', inputMode: 'qty', holding_type: 'EQUITY' });
      setSymbolSearch('');
      loadData();
    } catch (err) { alert(err.message); }
  };

  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const result = await importHoldings(file);
      alert(`Imported ${result.imported} holdings from ${result.broker} (${result.skipped} skipped)`);
      setShowImport(false);
      loadData();
    } catch (err) { alert(err.message); }
    finally { setImporting(false); }
  };

  const deleteHolding = async (id) => { if (confirm('Delete?')) { await api(`/api/portfolio/holdings/${id}`, { method: 'DELETE' }); loadData(); } };
  const editHolding = (h) => { setForm({ symbol: h.symbol, name: h.name, quantity: h.quantity, avg_price: h.avg_price, holding_type: h.holding_type }); setEditId(h._id); setShowForm(true); };
  const recordTxnFor = (symbol) => { setTxnForm({ ...txnForm, symbol }); setSymbolSearch(symbol); setShowTxn(true); };
  const handleDivSubmit = async (e) => {
    e.preventDefault();
    try {
      await addDividend({ ...divForm, amount: parseFloat(divForm.amount) });
      setShowDiv(false);
      setDivForm({ symbol: '', amount: '', ex_date: new Date().toISOString().split('T')[0] });
      loadData();
    } catch (err) { alert(err.message); }
  };
  const handleDeleteDiv = async (id) => { if (confirm('Delete?')) { await deleteDividend(id); loadData(); } };
  const handleExport = async (type) => { try { await downloadExport(type); } catch { alert('Export failed'); } };
  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '0';
  
  // Filter holdings and calculate dynamic summary
  const getFilteredHoldings = () => {
    return holdings.filter(h => {
      if (holdingFilter === 'stocks') return h.holding_type !== 'MF';
      if (holdingFilter === 'mf') return h.holding_type === 'MF';
      return true;
    });
  };
  
  const filteredHoldingsBase = getFilteredHoldings();
  const filteredHoldings = filteredHoldingsBase.filter(h => h.symbol.toLowerCase().includes(search.toLowerCase()) || h.name?.toLowerCase().includes(search.toLowerCase()));
  
  const dynamicSummary = (() => {
    const fh = filteredHoldingsBase;
    const invested = fh.reduce((sum, h) => sum + h.quantity * h.avg_price, 0);
    const current = fh.reduce((sum, h) => sum + h.quantity * (h.current_price || h.avg_price), 0);
    const pnl = current - invested;
    const pnl_pct = invested > 0 ? (pnl / invested * 100) : 0;
    return { invested, current, pnl, pnl_pct };
  })();
  
  const dynamicSectors = (() => {
    const fh = filteredHoldingsBase;
    const total = fh.reduce((sum, h) => sum + h.quantity * (h.current_price || h.avg_price), 0);
    const bySector = {};
    fh.forEach(h => {
      const sector = h.sector || 'Others';
      bySector[sector] = (bySector[sector] || 0) + h.quantity * (h.current_price || h.avg_price);
    });
    return Object.entries(bySector).map(([sector, value]) => ({ sector, percentage: total > 0 ? Math.round(value / total * 1000) / 10 : 0 })).sort((a, b) => b.percentage - a.percentage);
  })();

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Portfolio</h1>
          <div className="flex gap-2">
            <button onClick={() => setShowExport(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] rounded-lg text-sm font-medium hover:bg-[var(--bg-tertiary)]">
              <Download className="w-4 h-4" /> Export
            </button>
            <button onClick={() => setShowImport(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] rounded-lg text-sm font-medium hover:bg-[var(--bg-tertiary)]">
              <Upload className="w-4 h-4" /> Import
            </button>
            <button onClick={() => setShowTxn(true)} className="flex items-center gap-2 px-4 py-2 bg-[#10b981] text-white rounded-lg text-sm font-medium hover:bg-[#0d9668]">
              <Plus className="w-4 h-4" /> Record Trade
            </button>
          </div>
        </div>

        {/* Asset Type Filter */}
        <div className="flex gap-2 mb-6">
          {[{k: 'all', l: 'All'}, {k: 'stocks', l: 'Stocks'}, {k: 'mf', l: 'Mutual Funds'}].map(f => (
            <button key={f.k} onClick={() => setHoldingFilter(f.k)} className={`px-4 py-2 rounded-lg text-sm font-medium ${holdingFilter === f.k ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-muted)] hover:text-white'}`}>{f.l}</button>
          ))}
        </div>

        {/* Summary Row */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Invested</div>
            <div className="text-xl font-semibold tabular">₹{fmt(dynamicSummary.invested)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Current Value</div>
            <div className="text-xl font-semibold tabular">₹{fmt(dynamicSummary.current)}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Total P&L</div>
            <div className={`text-xl font-semibold tabular ${dynamicSummary.pnl >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              {dynamicSummary.pnl >= 0 ? '+' : ''}₹{fmt(dynamicSummary.pnl)} ({dynamicSummary.pnl_pct?.toFixed(2) || 0}%)
            </div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">XIRR</div>
            <div className={`text-xl font-semibold tabular ${(xirr || 0) >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              {xirr !== null ? `${xirr >= 0 ? '+' : ''}${xirr.toFixed(2)}%` : '—'}
            </div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Dividends</div>
            <div className="text-xl font-semibold tabular text-[#10b981]">₹{fmt(divSummary.total_dividend)}</div>
            <div className="text-xs text-[var(--text-muted)]">{divSummary.dividend_yield}% yield</div>
          </div>
        </div>

        {/* Sector Allocation */}
        {dynamicSectors.length > 0 && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <PieChart className="w-5 h-5 text-[var(--accent)]" />
              <span className="font-medium">{holdingFilter === 'mf' ? 'Fund' : holdingFilter === 'stocks' ? 'Stock' : 'Sector'} Allocation</span>
            </div>
            <div className="flex h-4 rounded-full overflow-hidden mb-3">
              {dynamicSectors.map((s, i) => (
                <div key={s.sector} style={{ width: `${s.percentage}%`, backgroundColor: COLORS[i % COLORS.length] }} title={`${s.sector}: ${s.percentage}%`} />
              ))}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-2">
              {dynamicSectors.map((s, i) => (
                <div key={s.sector} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span>{s.sector}</span>
                  <span className="text-[var(--text-muted)]">{s.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-lg w-fit">
          {['holdings', 'transactions', 'dividends'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 py-2 rounded-md text-sm font-medium capitalize ${activeTab === tab ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-muted)] hover:text-white'}`}>
              {tab}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative mb-4 w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..." className="w-full pl-10 pr-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-white placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]" />
        </div>

        {/* Holdings Tab */}
        {activeTab === 'holdings' && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
            {loading ? (
              <div className="p-6 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-[var(--border)] rounded animate-pulse" />)}</div>
            ) : filteredHoldings.length === 0 ? (
              <div className="p-12 text-center">
                <TrendingUp className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                <div className="text-[var(--text-muted)]">{holdingFilter === 'all' ? 'No holdings yet. Record a trade to get started.' : `No ${holdingFilter === 'mf' ? 'mutual funds' : 'stocks'} in portfolio.`}</div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                      <th className="text-left px-6 py-3 font-medium">{holdingFilter === 'mf' ? 'Fund' : 'Stock'}</th>
                      <th className="text-right px-6 py-3 font-medium">{holdingFilter === 'mf' ? 'Units' : 'Qty'}</th>
                      <th className="text-right px-6 py-3 font-medium">{holdingFilter === 'mf' ? 'Avg NAV' : 'Avg'}</th>
                      <th className="text-right px-6 py-3 font-medium">{holdingFilter === 'mf' ? 'NAV' : 'LTP'}</th>
                      <th className="text-right px-6 py-3 font-medium">P&L</th>
                      <th className="text-right px-6 py-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredHoldings.map(h => (
                      <tr key={h._id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
                        <td className="px-6 py-4">
                          <a href={`/stock?s=${h.symbol}`} className="hover:text-[var(--accent)]">
                            <div className="font-medium">{h.symbol}</div>
                            <div className="text-sm text-[var(--text-muted)]">{h.name}</div>
                          </a>
                        </td>
                        <td className="px-6 py-4 text-right tabular">{h.quantity}</td>
                        <td className="px-6 py-4 text-right tabular">₹{fmt(h.avg_price)}</td>
                        <td className="px-6 py-4 text-right tabular">₹{fmt(h.current_price)}</td>
                        <td className="px-6 py-4 text-right">
                          <div className={`tabular font-medium ${h.pnl >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{h.pnl >= 0 ? '+' : ''}₹{fmt(h.pnl)}</div>
                          <div className={`text-sm tabular ${h.pnl >= 0 ? 'text-[#10b981]/70' : 'text-[#ef4444]/70'}`}>{h.pnl_pct >= 0 ? '+' : ''}{h.pnl_pct?.toFixed(2)}%</div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button onClick={() => recordTxnFor(h.symbol)} className="p-2 text-[var(--text-muted)] hover:text-[#10b981] hover:bg-[#10b981]/10 rounded-lg" title="Record trade"><Plus className="w-4 h-4" /></button>
                          <button onClick={() => deleteHolding(h._id)} className="p-2 text-[var(--text-muted)] hover:text-[#ef4444] hover:bg-[#ef4444]/10 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Transactions Tab */}
        {activeTab === 'transactions' && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
            {transactions.length === 0 ? (
              <div className="p-12 text-center">
                <Calendar className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                <div className="text-[var(--text-muted)]">No transactions recorded yet.</div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                      <th className="text-left px-6 py-3 font-medium">Date</th>
                      <th className="text-left px-6 py-3 font-medium">Stock</th>
                      <th className="text-left px-6 py-3 font-medium">Type</th>
                      <th className="text-right px-6 py-3 font-medium">Qty</th>
                      <th className="text-right px-6 py-3 font-medium">Price</th>
                      <th className="text-right px-6 py-3 font-medium">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.filter(t => t.symbol.toLowerCase().includes(search.toLowerCase())).map((t, i) => (
                      <tr key={i} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
                        <td className="px-6 py-4 text-sm">{t.date}</td>
                        <td className="px-6 py-4 font-medium">{t.symbol}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${t.type === 'BUY' ? 'bg-[#10b981]/20 text-[#10b981]' : 'bg-[#ef4444]/20 text-[#ef4444]'}`}>
                            {t.type === 'BUY' ? <ArrowDownLeft className="w-3 h-3" /> : <ArrowUpRight className="w-3 h-3" />}
                            {t.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right tabular">{t.quantity}</td>
                        <td className="px-6 py-4 text-right tabular">₹{fmt(t.price)}</td>
                        <td className="px-6 py-4 text-right tabular font-medium">₹{fmt(t.quantity * t.price)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Dividends Tab */}
        {activeTab === 'dividends' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button onClick={() => setShowDiv(true)} className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:bg-[#5558e3]">
                <Plus className="w-4 h-4" /> Add Dividend
              </button>
            </div>
            {divSummary.by_symbol.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-sm text-[var(--text-muted)] mb-3">By Year</div>
                  {divSummary.by_year.map(y => (
                    <div key={y.year} className="flex justify-between py-1">
                      <span>{y.year}</span>
                      <span className="text-[#10b981]">₹{fmt(y.amount)}</span>
                    </div>
                  ))}
                </div>
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-sm text-[var(--text-muted)] mb-3">Top Dividend Stocks</div>
                  {divSummary.by_symbol.slice(0, 5).map(s => (
                    <div key={s.symbol} className="flex justify-between py-1">
                      <span>{s.symbol}</span>
                      <span className="text-[#10b981]">₹{fmt(s.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
              {dividends.length === 0 ? (
                <div className="p-12 text-center">
                  <DollarSign className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                  <div className="text-[var(--text-muted)]">No dividends recorded yet.</div>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-[var(--text-muted)] text-xs uppercase">
                        <th className="text-left px-6 py-3 font-medium">Ex-Date</th>
                        <th className="text-left px-6 py-3 font-medium">Stock</th>
                        <th className="text-right px-6 py-3 font-medium">Per Share</th>
                        <th className="text-right px-6 py-3 font-medium">Qty</th>
                        <th className="text-right px-6 py-3 font-medium">Total</th>
                        <th className="text-right px-6 py-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dividends.filter(d => d.symbol.toLowerCase().includes(search.toLowerCase())).map(d => (
                        <tr key={d._id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-hover)]">
                          <td className="px-6 py-4 text-sm">{d.ex_date}</td>
                          <td className="px-6 py-4 font-medium">{d.symbol}</td>
                          <td className="px-6 py-4 text-right tabular">₹{d.amount}</td>
                          <td className="px-6 py-4 text-right tabular">{d.quantity}</td>
                          <td className="px-6 py-4 text-right tabular font-medium text-[#10b981]">₹{fmt(d.total)}</td>
                          <td className="px-6 py-4 text-right">
                            <button onClick={() => handleDeleteDiv(d._id)} className="p-2 text-[var(--text-muted)] hover:text-[#ef4444] hover:bg-[#ef4444]/10 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Record Trade Modal */}
        {showTxn && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => { setShowTxn(false); setShowSymbolDropdown(false); }}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Record Trade</h2>
                <button onClick={() => setShowTxn(false)} className="p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={handleTxnSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Asset Type</label>
                  <div className="flex gap-2">
                    {[{k: 'EQUITY', l: 'Stock'}, {k: 'MF', l: 'Mutual Fund'}].map(t => (
                      <button key={t.k} type="button" onClick={() => setTxnForm({...txnForm, holding_type: t.k, inputMode: t.k === 'MF' ? 'amt' : 'qty'})} className={`flex-1 py-2 rounded-lg text-sm font-medium ${txnForm.holding_type === t.k ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-secondary)]'}`}>{t.l}</button>
                    ))}
                  </div>
                </div>
                <div className="relative">
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">{txnForm.holding_type === 'MF' ? 'Fund Name' : 'Symbol'}</label>
                  <input 
                    value={symbolSearch} 
                    onChange={e => handleSymbolInput(e.target.value)} 
                    onFocus={() => symbolResults.length > 0 && setShowSymbolDropdown(true)}
                    placeholder={txnForm.holding_type === 'MF' ? 'e.g. AXIS-LIQ' : 'Search stock (e.g. Reliance)'} 
                    className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" 
                    required 
                    autoComplete="off"
                  />
                  {showSymbolDropdown && symbolResults.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg shadow-lg max-h-48 overflow-y-auto">
                      {symbolResults.map(s => (
                        <button
                          key={s.symbol}
                          type="button"
                          onClick={() => selectSymbol(s.symbol, s.name)}
                          className="w-full px-4 py-3 text-left hover:bg-[var(--bg-tertiary)] flex justify-between items-center"
                        >
                          <span className="font-medium text-[var(--text-primary)]">{s.symbol}</span>
                          <span className="text-sm text-[var(--text-muted)] truncate ml-2">{s.name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Type</label>
                  <div className="flex gap-2">
                    {['BUY', 'SELL'].map(t => (
                      <button key={t} type="button" onClick={() => setTxnForm({...txnForm, type: t})} className={`flex-1 py-2 rounded-lg text-sm font-medium ${txnForm.type === t ? (t === 'BUY' ? 'bg-[#10b981] text-white' : 'bg-[#ef4444] text-white') : 'bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-secondary)]'}`}>{t}</button>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">Input By</label>
                    <div className="flex gap-2">
                      {[{k: 'qty', l: 'Units'}, {k: 'amt', l: 'Amount'}].map(m => (
                        <button key={m.k} type="button" onClick={() => setTxnForm({...txnForm, inputMode: m.k})} className={`flex-1 py-2 rounded-lg text-sm font-medium ${txnForm.inputMode === m.k ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-secondary)]'}`}>{m.l}</button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-[var(--text-secondary)] mb-2">{txnForm.inputMode === 'amt' ? 'Amount (₹)' : 'Quantity'}</label>
                    {txnForm.inputMode === 'amt' ? (
                      <input type="number" step="0.01" value={txnForm.amount} onChange={e => setTxnForm({...txnForm, amount: e.target.value})} placeholder="e.g. 10000" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" required />
                    ) : (
                      <input type="number" step="0.0001" value={txnForm.quantity} onChange={e => setTxnForm({...txnForm, quantity: e.target.value})} placeholder="e.g. 10.5" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" required />
                    )}
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">NAV / Price (₹)</label>
                  <input type="number" step="0.01" value={txnForm.price} onChange={e => setTxnForm({...txnForm, price: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" required />
                </div>
                {txnForm.inputMode === 'amt' && txnForm.amount && txnForm.price && (
                  <div className="text-sm text-[var(--text-muted)] bg-[var(--bg-primary)] p-3 rounded-lg">
                    Units: <span className="text-[var(--text-primary)] font-medium">{(parseFloat(txnForm.amount) / parseFloat(txnForm.price)).toFixed(4)}</span>
                  </div>
                )}
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Date</label>
                  <input type="date" value={txnForm.date} onChange={e => setTxnForm({...txnForm, date: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" required />
                </div>
                <button type="submit" className={`w-full py-3 text-white rounded-lg font-medium ${txnForm.type === 'BUY' ? 'bg-[#10b981] hover:bg-[#0d9668]' : 'bg-[#ef4444] hover:bg-[#dc2626]'}`}>
                  {txnForm.type === 'BUY' ? 'Record Buy' : 'Record Sell'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Import Modal */}
        {showImport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowImport(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Import Holdings</h2>
                <button onClick={() => setShowImport(false)} className="p-2 text-[var(--text-muted)] hover:text-white rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button>
              </div>
              <div className="space-y-4">
                <p className="text-sm text-[var(--text-muted)]">Upload a CSV file from your broker:</p>
                <ul className="text-sm text-[var(--text-muted)] list-disc list-inside space-y-1">
                  <li><strong>Zerodha:</strong> Console → Reports → Tradebook → Download</li>
                  <li><strong>Groww:</strong> Stocks → Export → Download CSV</li>
                </ul>
                <label className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-[var(--border)] rounded-lg cursor-pointer hover:border-[var(--accent)] ${importing ? 'opacity-50' : ''}`}>
                  <Upload className="w-8 h-8 text-[var(--text-muted)] mb-2" />
                  <span className="text-sm text-[var(--text-muted)]">{importing ? 'Importing...' : 'Click to upload CSV'}</span>
                  <input type="file" accept=".csv" className="hidden" onChange={handleImport} disabled={importing} />
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Add Dividend Modal */}
        {showDiv && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowDiv(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Add Dividend</h2>
                <button onClick={() => setShowDiv(false)} className="p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={handleDivSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Symbol</label>
                  <select value={divForm.symbol} onChange={e => setDivForm({...divForm, symbol: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" required>
                    <option value="">Select stock</option>
                    {holdings.map(h => <option key={h.symbol} value={h.symbol}>{h.symbol}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Dividend per Share (₹)</label>
                  <input type="number" step="0.01" value={divForm.amount} onChange={e => setDivForm({...divForm, amount: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" required />
                </div>
                <div>
                  <label className="block text-sm text-[var(--text-secondary)] mb-2">Ex-Date</label>
                  <input type="date" value={divForm.ex_date} onChange={e => setDivForm({...divForm, ex_date: e.target.value})} className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" required />
                </div>
                <button type="submit" className="w-full py-3 bg-[var(--accent)] text-white rounded-lg font-medium hover:bg-[#5558e3]">Add Dividend</button>
              </form>
            </div>
          </div>
        )}

        {/* Export Modal */}
        {showExport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowExport(false)}>
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Export Reports</h2>
                <button onClick={() => setShowExport(false)} className="p-2 text-[var(--text-muted)] hover:text-white rounded-lg hover:bg-[var(--border)]"><X className="w-5 h-5" /></button>
              </div>
              <div className="space-y-3">
                {[{type: 'holdings', label: 'Holdings', desc: 'Current portfolio with P&L'}, {type: 'transactions', label: 'Transactions', desc: 'All buy/sell history'}, {type: 'dividends', label: 'Dividends', desc: 'Dividend income records'}, {type: 'summary', label: 'Full Summary', desc: 'Complete portfolio report'}].map(e => (
                  <button key={e.type} onClick={() => { handleExport(e.type); setShowExport(false); }} className="w-full flex items-center justify-between p-4 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg hover:border-[var(--accent)]">
                    <div className="text-left">
                      <div className="font-medium">{e.label}</div>
                      <div className="text-sm text-[var(--text-muted)]">{e.desc}</div>
                    </div>
                    <Download className="w-5 h-5 text-[var(--text-muted)]" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
