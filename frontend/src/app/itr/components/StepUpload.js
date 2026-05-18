'use client';
import { Upload, CheckCircle, RefreshCw, HelpCircle } from 'lucide-react';

export default function StepUpload({ uploads, uploadResults, uploadErrors, uploading, pdfPasswords, onUpload, onPasswordChange }) {
  const fmt = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN')}` : '—';
  const docs = [
    { name: 'Form 16', hint: 'PDF from employer', endpoint: 'form16', needsPassword: false },
    { name: 'AIS (Annual Information Statement)', hint: 'Password: PAN(lowercase) + DOB(DDMMYYYY)', endpoint: 'ais', needsPassword: true },
    { name: 'Form 26AS', hint: 'Download from TRACES portal', endpoint: 'form26as', needsPassword: true },
  ];

  return (
    <div className="space-y-4">
      <p className="text-[var(--text-secondary)]">Upload your tax documents. All data is parsed locally and shown for your confirmation.</p>
      {docs.map((doc) => (
        <div key={doc.endpoint} className="p-4 border border-[var(--border)] rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-[var(--text-primary)]">{doc.name}</h3>
              <p className="text-xs text-[var(--text-muted)]">{doc.hint}</p>
            </div>
            <div className="flex items-center gap-3">
              {uploads[doc.endpoint] && (
                <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle size={12} />{uploads[doc.endpoint]}</span>
              )}
              <label className={`px-4 py-2 rounded-lg cursor-pointer text-sm flex items-center gap-2 ${uploading[doc.endpoint] ? 'opacity-50 pointer-events-none' : ''} ${uploads[doc.endpoint] ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-[var(--bg-tertiary)] border border-[var(--border)] hover:bg-[var(--border)] text-[var(--text-secondary)]'}`}>
                {uploading[doc.endpoint] ? <><RefreshCw size={14} className="animate-spin" />Uploading...</> : <><Upload size={14} />{uploads[doc.endpoint] ? 'Re-upload' : 'Upload'}</>}
                <input type="file" accept=".pdf" className="hidden" onChange={(e) => { onUpload(doc.endpoint, e.target.files[0]); e.target.value = ''; }} />
              </label>
            </div>
          </div>
          {uploadErrors[doc.endpoint] && (
            <div className="mt-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{uploadErrors[doc.endpoint]}</div>
          )}
          {doc.needsPassword && (
            <div className="mt-3">
              <label className="text-xs text-[var(--text-muted)] mb-1 block">PDF Password (if protected)</label>
              <input type="text" value={pdfPasswords[doc.endpoint]} onChange={e => onPasswordChange(doc.endpoint, e.target.value)}
                placeholder={doc.endpoint === 'ais' ? 'e.g. abcde1234f01011990' : 'Enter password'}
                className="w-full sm:w-80 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] text-sm" />
            </div>
          )}
          {uploadResults[doc.endpoint] && (
            <div className="mt-3 p-3 bg-[var(--bg-tertiary)] rounded-lg text-sm">
              {doc.endpoint === 'form16' && uploadResults[doc.endpoint].part_b && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                  <div><span className="text-[var(--text-muted)]">Gross Salary:</span> <span className="text-[var(--text-primary)]">{fmt(uploadResults[doc.endpoint].part_b.gross_salary)}</span></div>
                  <div><span className="text-[var(--text-muted)]">TDS:</span> <span className="text-[var(--text-primary)]">{fmt(uploadResults[doc.endpoint].part_a?.total_tds)}</span></div>
                </div>
              )}
              {doc.endpoint === 'ais' && uploadResults[doc.endpoint].summary && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                  <div><span className="text-[var(--text-muted)]">Entries:</span> <span className="text-[var(--text-primary)]">{uploadResults[doc.endpoint].summary.total_entries}</span></div>
                  <div><span className="text-[var(--text-muted)]">TDS:</span> <span className="text-[var(--text-primary)]">{uploadResults[doc.endpoint].summary.tds_entries}</span></div>
                </div>
              )}
              {doc.endpoint === 'form26as' && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                  <div><span className="text-[var(--text-muted)]">Total TDS:</span> <span className="text-[var(--text-primary)]">{fmt(uploadResults[doc.endpoint].total_tds)}</span></div>
                  <div><span className="text-[var(--text-muted)]">Entries:</span> <span className="text-[var(--text-primary)]">{uploadResults[doc.endpoint].tds_entries?.length || 0}</span></div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
      <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <p className="text-blue-300 text-sm flex items-center gap-2"><HelpCircle size={14} />Don't have these? You can enter data manually in the next steps.</p>
      </div>
    </div>
  );
}
