'use client';
import { CheckCircle } from 'lucide-react';

export default function StepReconcile({ checklist, loading, onLoad, onResolveItem, onResolveAll }) {
  const fmt = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN')}` : '—';

  return (
    <div className="space-y-4">
      <p className="text-[var(--text-secondary)]">Every AIS item must be resolved before proceeding. This prevents IT notices.</p>
      <button onClick={onLoad} disabled={loading} className="px-5 py-2.5 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 font-medium">
        {loading ? 'Loading...' : 'Load Reconciliation'}
      </button>
      {checklist && (
        <div>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1 bg-[var(--bg-tertiary)] rounded-full h-2.5">
              <div className="bg-green-500 h-2.5 rounded-full transition-all" style={{ width: `${checklist.progress * 100}%` }} />
            </div>
            <span className="text-sm text-[var(--text-muted)]">{checklist.resolved}/{checklist.total}</span>
          </div>
          {checklist.pending > 0 && (
            <div className="flex items-center justify-between mb-3">
              <p className="text-yellow-400 text-sm">⚠️ {checklist.pending} items pending.</p>
              <button onClick={onResolveAll} disabled={loading} className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs hover:bg-green-700 disabled:opacity-50">
                {loading ? 'Accepting...' : 'Accept All'}
              </button>
            </div>
          )}
          {checklist.items?.map((item, i) => (
            <div key={item.id || i} className={`p-3 mb-2 rounded-lg border ${item.status === 'pending' ? 'border-yellow-500/30 bg-yellow-500/5' : 'border-green-500/30 bg-green-500/5'}`}>
              <div className="flex justify-between items-start gap-2">
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium text-[var(--text-primary)]">{item.info_code}</span>
                  <p className="text-[var(--text-muted)] text-xs truncate">{item.description || item.source_name}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-sm font-medium">{fmt(item.reported_value)}</span>
                  {item.status === 'pending' ? (
                    <div className="flex gap-1">
                      <button onClick={() => onResolveItem(item.id, 'accepted')} className="px-2 py-1 bg-green-600 text-white rounded text-xs">✓</button>
                      <button onClick={() => onResolveItem(item.id, 'disputed')} className="px-2 py-1 bg-red-600/20 text-red-400 border border-red-500/30 rounded text-xs">✗</button>
                    </div>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-300">{item.status}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
