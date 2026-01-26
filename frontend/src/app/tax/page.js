'use client';
import { useState, useEffect } from 'react';
import { Receipt, TrendingDown, TrendingUp, AlertTriangle, FileText, Calculator } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function TaxPage() {
  const [summary, setSummary] = useState(null);
  const [harvest, setHarvest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sumData, harvestData] = await Promise.all([api('/api/tax/summary'), api('/api/tax/harvest')]);
      setSummary(sumData);
      setHarvest(harvestData);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-6">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Tax Center</h1>
          <span className="text-sm text-[var(--text-muted)]">FY {summary?.financial_year}</span>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Realized STCG</div>
            <div className={`text-xl font-semibold ${summary?.realized?.stcg >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              ₹{fmt(summary?.realized?.stcg)}
            </div>
            <div className="text-xs text-[var(--text-muted)]">Tax @ 20%</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Realized LTCG</div>
            <div className={`text-xl font-semibold ${summary?.realized?.ltcg >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              ₹{fmt(summary?.realized?.ltcg)}
            </div>
            <div className="text-xs text-[var(--text-muted)]">₹1.25L exempt, then 12.5%</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Unrealized Gains</div>
            <div className={`text-xl font-semibold ${summary?.unrealized?.total >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              ₹{fmt(summary?.unrealized?.total)}
            </div>
            <div className="text-xs text-[var(--text-muted)]">Not taxable until sold</div>
          </div>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
            <div className="text-sm text-[var(--text-muted)] mb-1">Estimated Tax</div>
            <div className="text-xl font-semibold text-[#ef4444]">₹{fmt(summary?.tax_liability?.total_tax)}</div>
            <div className="text-xs text-[var(--text-muted)]">STCG + LTCG</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-lg w-fit">
          {['summary', 'harvest', 'report'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 py-2 rounded-md text-sm font-medium capitalize ${activeTab === tab ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-muted)] hover:text-white'}`}>
              {tab === 'harvest' ? 'Tax Harvesting' : tab}
            </button>
          ))}
        </div>

        {/* Summary Tab */}
        {activeTab === 'summary' && summary && (
          <div className="space-y-4">
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
              <h3 className="font-medium mb-4 flex items-center gap-2"><Calculator className="w-5 h-5 text-[var(--accent)]" /> Tax Calculation</h3>
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-[var(--border)]">
                  <span>STCG (Short Term Capital Gains)</span>
                  <span>₹{fmt(summary.realized.stcg)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--border)]">
                  <span>STCG Tax @ 20%</span>
                  <span className="text-[#ef4444]">₹{fmt(summary.tax_liability.stcg_tax)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--border)]">
                  <span>LTCG (Long Term Capital Gains)</span>
                  <span>₹{fmt(summary.realized.ltcg)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--border)]">
                  <span>Less: Exemption (Section 112A)</span>
                  <span className="text-[#10b981]">-₹{fmt(summary.tax_liability.ltcg_exemption)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--border)]">
                  <span>Taxable LTCG</span>
                  <span>₹{fmt(summary.tax_liability.taxable_ltcg)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--border)]">
                  <span>LTCG Tax @ 12.5%</span>
                  <span className="text-[#ef4444]">₹{fmt(summary.tax_liability.ltcg_tax)}</span>
                </div>
                <div className="flex justify-between py-2 font-semibold text-lg">
                  <span>Total Tax Liability</span>
                  <span className="text-[#ef4444]">₹{fmt(summary.tax_liability.total_tax)}</span>
                </div>
              </div>
            </div>

            {summary.transactions?.length > 0 && (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
                <h3 className="font-medium mb-4">Realized Transactions</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-[var(--text-muted)] border-b border-[var(--border)]">
                        <th className="text-left py-2">Stock</th>
                        <th className="text-left py-2">Date</th>
                        <th className="text-right py-2">Qty</th>
                        <th className="text-right py-2">Buy</th>
                        <th className="text-right py-2">Sell</th>
                        <th className="text-right py-2">Gain/Loss</th>
                        <th className="text-left py-2">Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.transactions.map((t, i) => (
                        <tr key={i} className="border-b border-[var(--border)]">
                          <td className="py-2 font-medium">{t.symbol}</td>
                          <td className="py-2">{t.date}</td>
                          <td className="py-2 text-right">{t.quantity}</td>
                          <td className="py-2 text-right">₹{fmt(t.buy_price)}</td>
                          <td className="py-2 text-right">₹{fmt(t.sell_price)}</td>
                          <td className={`py-2 text-right font-medium ${t.gain >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                            {t.gain >= 0 ? '+' : ''}₹{fmt(t.gain)}
                          </td>
                          <td className="py-2"><span className={`px-2 py-0.5 rounded text-xs ${t.type === 'LTCG' ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#f59e0b]/10 text-[#f59e0b]'}`}>{t.type}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tax Harvesting Tab */}
        {activeTab === 'harvest' && harvest && (
          <div className="space-y-4">
            <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/30 rounded-lg p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-[#f59e0b] mt-0.5" />
              <div>
                <div className="font-medium text-[#f59e0b]">Tax-Loss Harvesting</div>
                <div className="text-sm text-[var(--text-secondary)]">{harvest.note}</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <div className="text-sm text-[var(--text-muted)]">Harvestable Loss</div>
                <div className="text-2xl font-semibold text-[#ef4444]">₹{fmt(harvest.total_harvestable_loss)}</div>
              </div>
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <div className="text-sm text-[var(--text-muted)]">Potential Tax Saved</div>
                <div className="text-2xl font-semibold text-[#10b981]">₹{fmt(harvest.potential_tax_saved)}</div>
              </div>
            </div>

            {harvest.suggestions?.length > 0 ? (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-[var(--text-muted)] border-b border-[var(--border)] bg-[var(--bg-primary)]">
                      <th className="text-left px-4 py-3">Stock</th>
                      <th className="text-right px-4 py-3">Qty</th>
                      <th className="text-right px-4 py-3">Avg</th>
                      <th className="text-right px-4 py-3">CMP</th>
                      <th className="text-right px-4 py-3">Loss</th>
                      <th className="text-right px-4 py-3">Tax Saved</th>
                    </tr>
                  </thead>
                  <tbody>
                    {harvest.suggestions.map((s, i) => (
                      <tr key={i} className="border-b border-[var(--border)] hover:bg-[var(--bg-hover)]">
                        <td className="px-4 py-3 font-medium">{s.symbol}</td>
                        <td className="px-4 py-3 text-right">{s.quantity}</td>
                        <td className="px-4 py-3 text-right">₹{fmt(s.avg_price)}</td>
                        <td className="px-4 py-3 text-right">₹{fmt(s.current_price)}</td>
                        <td className="px-4 py-3 text-right text-[#ef4444]">-₹{fmt(s.loss)} ({s.loss_pct}%)</td>
                        <td className="px-4 py-3 text-right text-[#10b981]">₹{fmt(s.tax_saved)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
                <TrendingUp className="w-12 h-12 mx-auto mb-4 text-[#10b981]" />
                <div className="text-[var(--text-muted)]">No loss-making holdings to harvest. Your portfolio is doing well!</div>
              </div>
            )}
          </div>
        )}

        {/* Report Tab */}
        {activeTab === 'report' && summary && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium flex items-center gap-2"><FileText className="w-5 h-5 text-[var(--accent)]" /> ITR Schedule CG</h3>
            </div>
            <div className="space-y-4">
              <div className="bg-[var(--bg-primary)] rounded-lg p-4">
                <div className="font-medium mb-2">Section 111A - STCG on Equity</div>
                <div className="text-sm text-[var(--text-muted)] mb-2">Short-term capital gains on sale of equity shares where STT is paid</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-[var(--text-muted)]">Gains:</span> ₹{fmt(summary.realized.stcg)}</div>
                  <div><span className="text-[var(--text-muted)]">Tax Rate:</span> 20%</div>
                </div>
              </div>
              <div className="bg-[var(--bg-primary)] rounded-lg p-4">
                <div className="font-medium mb-2">Section 112A - LTCG on Equity</div>
                <div className="text-sm text-[var(--text-muted)] mb-2">Long-term capital gains on sale of equity shares where STT is paid</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-[var(--text-muted)]">Gains:</span> ₹{fmt(summary.realized.ltcg)}</div>
                  <div><span className="text-[var(--text-muted)]">Exemption:</span> ₹{fmt(summary.tax_liability.ltcg_exemption)}</div>
                  <div><span className="text-[var(--text-muted)]">Taxable:</span> ₹{fmt(summary.tax_liability.taxable_ltcg)}</div>
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
