'use client';

export default function StepCompute({ computation, comparison, optimization, loading, onCompute }) {
  const fmt = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN')}` : '—';

  return (
    <div className="space-y-4">
      <button onClick={onCompute} disabled={loading} className="px-6 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 font-medium">
        {loading ? 'Computing...' : 'Compute Tax (Both Regimes)'}
      </button>
      {comparison && (
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
          <p className="text-green-400 text-lg font-semibold">Recommended: {comparison.recommended?.toUpperCase()} Regime</p>
          <p className="text-[var(--text-secondary)]">{comparison.explanation}</p>
        </div>
      )}
      {computation && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[['Gross Income', computation.gross_total_income], ['Deductions', computation.total_deductions], ['Taxable Income', computation.taxable_normal_income], ['Normal Tax', computation.tax_on_normal], ['STCG Tax', computation.tax_stcg_111a], ['LTCG Tax', computation.tax_ltcg_112a], ['Rebate 87A', computation.rebate_87a], ['Surcharge', (computation.surcharge_normal || 0) + (computation.surcharge_cg || 0)], ['Cess (4%)', computation.cess], ['Gross Tax', computation.gross_tax], ['TDS Paid', computation.total_tax_paid], ['Net Payable', computation.net_tax_payable]].map(([label, val], i) => (
            <div key={i} className={`p-3 rounded-lg border ${i === 11 ? (val < 0 ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30') : 'bg-[var(--bg-tertiary)] border-[var(--border)]'}`}>
              <p className="text-xs text-[var(--text-muted)]">{label}</p>
              <p className={`text-lg font-semibold ${i === 11 && val < 0 ? 'text-green-400' : 'text-[var(--text-primary)]'}`}>
                {i === 11 && val < 0 ? `REFUND ${fmt(Math.abs(val))}` : fmt(val)}
              </p>
            </div>
          ))}
        </div>
      )}
      {optimization?.suggestions?.length > 0 && (
        <div>
          <h3 className="font-medium text-[var(--text-primary)] mb-2">💡 Optimization Tips</h3>
          {optimization.suggestions.map((s, i) => (
            <div key={i} className="p-3 mb-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <p className="font-medium text-blue-300">{s.title}</p>
              <p className="text-sm text-[var(--text-muted)]">{s.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
