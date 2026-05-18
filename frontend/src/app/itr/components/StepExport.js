'use client';
import { Download, Shield, Clock } from 'lucide-react';

export default function StepExport({ validation, calendar, loading, onExport }) {
  return (
    <div className="space-y-6">
      <div className="p-6 sm:p-8 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-xl text-center">
        <Download size={40} className="mx-auto mb-4 text-[var(--accent)]" />
        <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">Export ITR JSON</h3>
        <p className="text-[var(--text-muted)] mb-5">Download the JSON file and upload it on the Income Tax e-filing portal.</p>
        <button onClick={onExport} disabled={loading} className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium disabled:opacity-50">
          {loading ? 'Generating...' : `Download ${validation?.itr_form || 'ITR-2'} JSON`}
        </button>
      </div>

      <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
        <h3 className="font-medium text-green-300 mb-3 flex items-center gap-2"><Shield size={16} /> E-Verification (Mandatory within 30 days)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          {[['🔐 Aadhaar OTP', 'Instant • Mobile linked to Aadhaar'], ['🏦 Net Banking', 'Login via bank → IT portal'], ['💳 Bank EVC', 'Pre-validated bank account'], ['📝 DSC', 'Digital Signature Certificate']].map(([title, desc], i) => (
            <div key={i} className="p-3 bg-[var(--bg-primary)] rounded-lg">
              <p className="font-medium text-[var(--text-primary)] mb-1">{title}</p>
              <p className="text-xs text-[var(--text-muted)]">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {calendar?.deadlines && (
        <div className="p-4 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg">
          <h3 className="font-medium text-[var(--text-primary)] mb-2 flex items-center gap-2"><Clock size={16} /> Key Deadlines</h3>
          {calendar.deadlines.map((d, i) => (
            <div key={i} className="flex justify-between py-1.5 text-sm border-b border-[var(--border)] last:border-0">
              <span className="text-[var(--text-muted)]">{d.description}</span>
              <span className="text-[var(--text-primary)]">{d.date}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
