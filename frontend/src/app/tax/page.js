'use client';
import { useState, useEffect } from 'react';
import { Receipt, TrendingDown, TrendingUp, AlertTriangle, FileText, Calculator, Download, Calendar, DollarSign, Bell } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function TaxPage() {
  const [summary, setSummary] = useState(null);
  const [harvest, setHarvest] = useState(null);
  const [advance, setAdvance] = useState(null);
  const [dividendTax, setDividendTax] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sumData, harvestData, advData, divData] = await Promise.all([
        api('/api/finance/tax'),
        api('/api/finance/tax/harvest'),
        api('/api/finance/tax/advance'),
        api('/api/finance/tax/dividend-income'),
      ]);
      setSummary(sumData);
      setHarvest(harvestData);
      setAdvance(advData);
      setDividendTax(divData);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const exportReport = async () => {
    const token = localStorage.getItem('token');
    const res = await fetch('/api/finance/tax/export', { headers: { Authorization: `Bearer ${token}` } });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tax_report_${summary?.financial_year || 'FY'}.csv`;
    a.click();
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-4 md:p-6">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6 overflow-x-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2"><Receipt className="w-5 h-5 md:w-6 md:h-6" /> Tax Center</h1>
          <div className="flex items-center gap-3">
            <span className="text-sm text-[var(--text-muted)]">FY {summary?.financial_year}</span>
            <button onClick={exportReport} className="flex items-center gap-2 px-3 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:opacity-90">
              <Download className="w-4 h-4" /> Export
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 xl:grid-cols-5 gap-3 md:gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Realized STCG</div>
            <div className={`text-base md:text-xl font-semibold ${summary?.realized?.stcg >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>₹{fmt(summary?.realized?.stcg)}</div>
            <div className="text-xs text-[var(--text-muted)]">Tax @ 20%</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Realized LTCG</div>
            <div className={`text-base md:text-xl font-semibold ${summary?.realized?.ltcg >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>₹{fmt(summary?.realized?.ltcg)}</div>
            <div className="text-xs text-[var(--text-muted)]">₹1.25L exempt</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Unrealized Gains</div>
            <div className={`text-base md:text-xl font-semibold ${summary?.unrealized?.total >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>₹{fmt(summary?.unrealized?.total)}</div>
            <div className="text-xs text-[var(--text-muted)]">Not taxable yet</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Dividend Income</div>
            <div className="text-base md:text-xl font-semibold text-[#10b981]">₹{fmt(dividendTax?.total_income)}</div>
            <div className="text-xs text-[var(--text-muted)]">Slab rate</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
            <div className="text-xs md:text-sm text-[var(--text-muted)] mb-1">Estimated Tax</div>
            <div className="text-base md:text-xl font-semibold text-[#ef4444]">₹{fmt(summary?.tax_liability?.total_tax)}</div>
            <div className="text-xs text-[var(--text-muted)]">STCG + LTCG</div>
          </div>
        </div>

        {/* Advance Tax Alert */}
        {advance?.next_due?.is_upcoming && (
          <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/30 rounded-lg p-4 mb-6 flex items-start gap-3">
            <Bell className="w-5 h-5 text-[#f59e0b] mt-0.5 shrink-0" />
            <div>
              <div className="font-medium text-[#f59e0b]">Advance Tax Due Soon</div>
              <div className="text-sm text-[var(--text-secondary)]">
                {advance.next_due.label}: Pay ₹{fmt(advance.next_due.amount_due)} by {advance.next_due.due_date}
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-lg overflow-x-auto">
          {['summary', 'harvest', 'dividends', 'advance', 'report'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`px-3 md:px-4 py-2 rounded-md text-sm font-medium capitalize whitespace-nowrap ${activeTab === tab ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-muted)] hover:text-white'}`}>
              {tab === 'harvest' ? 'Harvesting' : tab === 'advance' ? 'Advance Tax' : tab}
            </button>
          ))}
        </div>

        {/* Summary Tab */}
        {activeTab === 'summary' && summary && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 md:p-5">
            <h3 className="font-medium mb-4 flex items-center gap-2"><Calculator className="w-5 h-5 text-[var(--accent)]" /> Tax Calculation</h3>
            <div className="space-y-3 text-sm md:text-base">
              <div className="flex justify-between py-2 border-b border-[var(--border)]"><span>STCG (Short Term)</span><span>₹{fmt(summary.unrealized?.stcg)}</span></div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]"><span>STCG Tax @ 20%</span><span className="text-[#ef4444]">₹{fmt(summary.tax_liability?.stcg_tax)}</span></div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]"><span>LTCG (Long Term)</span><span>₹{fmt(summary.unrealized?.ltcg)}</span></div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]"><span>Less: Exemption (112A)</span><span className="text-[#10b981]">-₹{fmt(summary.tax_liability?.ltcg_exemption)}</span></div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]"><span>Taxable LTCG</span><span>₹{fmt(summary.tax_liability?.taxable_ltcg)}</span></div>
              <div className="flex justify-between py-2 border-b border-[var(--border)]"><span>LTCG Tax @ 12.5%</span><span className="text-[#ef4444]">₹{fmt(summary.tax_liability?.ltcg_tax)}</span></div>
              <div className="flex justify-between py-2 font-semibold text-lg"><span>Total Tax Liability</span><span className="text-[#ef4444]">₹{fmt(summary.tax_liability?.total_tax)}</span></div>
            </div>
          </div>
        )}

        {/* Tax Harvesting Tab */}
        {activeTab === 'harvest' && harvest && (
          <div className="space-y-4">
            <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/30 rounded-lg p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-[#f59e0b] mt-0.5 shrink-0" />
              <div><div className="font-medium text-[#f59e0b]">Tax-Loss Harvesting</div><div className="text-sm text-[var(--text-secondary)]">{harvest.note}</div></div>
            </div>
            <div className="grid grid-cols-2 gap-3 md:gap-4">
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
                <div className="text-xs md:text-sm text-[var(--text-muted)]">Harvestable Loss</div>
                <div className="text-xl md:text-2xl font-semibold text-[#ef4444]">₹{fmt(harvest.total_harvestable_loss)}</div>
              </div>
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 md:p-4">
                <div className="text-xs md:text-sm text-[var(--text-muted)]">Potential Tax Saved</div>
                <div className="text-xl md:text-2xl font-semibold text-[#10b981]">₹{fmt(harvest.potential_tax_saved)}</div>
              </div>
            </div>
            {harvest.suggestions?.length > 0 ? (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[500px]">
                    <thead><tr className="text-[var(--text-muted)] border-b border-[var(--border)] bg-[var(--bg-primary)]">
                      <th className="text-left px-3 md:px-4 py-3">Stock</th><th className="text-right px-3 md:px-4 py-3">Qty</th><th className="text-right px-3 md:px-4 py-3">Loss</th><th className="text-right px-3 md:px-4 py-3">Tax Saved</th>
                    </tr></thead>
                    <tbody>{harvest.suggestions.map((s, i) => (
                      <tr key={i} className="border-b border-[var(--border)]">
                        <td className="px-3 md:px-4 py-3 font-medium">{s.symbol}</td>
                        <td className="px-3 md:px-4 py-3 text-right">{s.quantity}</td>
                        <td className="px-3 md:px-4 py-3 text-right text-[#ef4444]">-₹{fmt(s.loss)}</td>
                        <td className="px-3 md:px-4 py-3 text-right text-[#10b981]">₹{fmt(s.tax_saved)}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
                <TrendingUp className="w-12 h-12 mx-auto mb-4 text-[#10b981]" />
                <div className="text-[var(--text-muted)]">No loss-making holdings to harvest!</div>
              </div>
            )}
          </div>
        )}

        {/* Dividends Tab */}
        {activeTab === 'dividends' && dividendTax && (
          <div className="space-y-4">
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[var(--text-muted)]">Total Dividend Income ({dividendTax.financial_year})</span>
                <span className="text-xl font-semibold text-[#10b981]">₹{fmt(dividendTax.total_income)}</span>
              </div>
              <p className="text-xs text-[var(--text-muted)]">{dividendTax.tax_note}</p>
            </div>
            {dividendTax.dividends?.length > 0 ? (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[400px]">
                    <thead><tr className="text-[var(--text-muted)] border-b border-[var(--border)] bg-[var(--bg-primary)]">
                      <th className="text-left px-3 md:px-4 py-3">Stock</th><th className="text-left px-3 md:px-4 py-3">Date</th><th className="text-right px-3 md:px-4 py-3">Per Share</th><th className="text-right px-3 md:px-4 py-3">Income</th>
                    </tr></thead>
                    <tbody>{dividendTax.dividends.map((d, i) => (
                      <tr key={i} className="border-b border-[var(--border)]">
                        <td className="px-3 md:px-4 py-3 font-medium">{d.symbol}</td>
                        <td className="px-3 md:px-4 py-3">{d.date}</td>
                        <td className="px-3 md:px-4 py-3 text-right">₹{d.per_share?.toFixed(2)}</td>
                        <td className="px-3 md:px-4 py-3 text-right text-[#10b981]">₹{fmt(d.income)}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
                <DollarSign className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                <div className="text-[var(--text-muted)]">No dividend income recorded this FY</div>
              </div>
            )}
          </div>
        )}

        {/* Advance Tax Tab */}
        {activeTab === 'advance' && advance && (
          <div className="space-y-4">
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[var(--text-muted)]">Estimated Tax ({advance.financial_year})</span>
                <span className="text-xl font-semibold">₹{fmt(advance.estimated_tax)}</span>
              </div>
              <p className="text-xs text-[var(--text-muted)]">{advance.note}</p>
            </div>
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
              <h3 className="font-medium mb-4 flex items-center gap-2"><Calendar className="w-5 h-5 text-[var(--accent)]" /> Payment Schedule</h3>
              <div className="space-y-3">
                {advance.schedule?.map((s, i) => (
                  <div key={i} className={`flex items-center justify-between p-3 rounded-lg ${s.is_past ? 'bg-[var(--bg-primary)] opacity-60' : s.is_upcoming ? 'bg-[#f59e0b]/10 border border-[#f59e0b]/30' : 'bg-[var(--bg-primary)]'}`}>
                    <div>
                      <div className="font-medium">{s.label}</div>
                      <div className="text-sm text-[var(--text-muted)]">{s.percent}% of total tax</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">₹{fmt(s.amount_due)}</div>
                      {s.is_past && <span className="text-xs text-[var(--text-muted)]">Past</span>}
                      {s.is_upcoming && <span className="text-xs text-[#f59e0b]">Due Soon</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Report Tab */}
        {activeTab === 'report' && summary && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 md:p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium flex items-center gap-2"><FileText className="w-5 h-5 text-[var(--accent)]" /> ITR Schedule CG</h3>
              <button onClick={exportReport} className="text-sm text-[var(--accent)] hover:underline">Download CSV</button>
            </div>
            <div className="space-y-4">
              <div className="bg-[var(--bg-primary)] rounded-lg p-4">
                <div className="font-medium mb-2">Section 111A - STCG on Equity</div>
                <div className="text-sm text-[var(--text-muted)] mb-2">Short-term capital gains (STT paid)</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-[var(--text-muted)]">Gains:</span> ₹{fmt(summary.unrealized?.stcg)}</div>
                  <div><span className="text-[var(--text-muted)]">Tax Rate:</span> 20%</div>
                </div>
              </div>
              <div className="bg-[var(--bg-primary)] rounded-lg p-4">
                <div className="font-medium mb-2">Section 112A - LTCG on Equity</div>
                <div className="text-sm text-[var(--text-muted)] mb-2">Long-term capital gains (STT paid)</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-[var(--text-muted)]">Gains:</span> ₹{fmt(summary.unrealized?.ltcg)}</div>
                  <div><span className="text-[var(--text-muted)]">Exemption:</span> ₹{fmt(summary.tax_liability?.ltcg_exemption)}</div>
                  <div><span className="text-[var(--text-muted)]">Taxable:</span> ₹{fmt(summary.tax_liability?.taxable_ltcg)}</div>
                  <div><span className="text-[var(--text-muted)]">Tax Rate:</span> 12.5%</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
