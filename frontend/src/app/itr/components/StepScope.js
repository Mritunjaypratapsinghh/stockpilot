'use client';
import { CheckCircle } from 'lucide-react';

export default function StepScope({ scopeResult, loading, onRunCheck }) {
  return (
    <div className="space-y-4">
      <p className="text-[var(--text-secondary)]">We'll check if your tax situation is supported by this system.</p>
      <button onClick={onRunCheck} disabled={loading} className="px-6 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50 font-medium">
        {loading ? 'Checking...' : 'Run Scope Check'}
      </button>
      {scopeResult && (
        <div className={`p-4 rounded-lg border ${scopeResult.supported ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
          {scopeResult.supported ? (
            <p className="text-green-400 flex items-center gap-2"><CheckCircle size={18} /> Your tax situation is fully supported. Proceed!</p>
          ) : (
            <div>
              <p className="text-red-400 font-semibold mb-2">⚠️ Unsupported case detected:</p>
              {scopeResult.blockers?.map((b, i) => (
                <div key={i} className="mb-2 p-3 bg-red-500/5 rounded">
                  <p className="text-red-300 font-medium">{b.message}</p>
                  <p className="text-[var(--text-muted)] text-sm mt-1">{b.guidance}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
