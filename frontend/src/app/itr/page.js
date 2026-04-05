'use client';
import { useState, useEffect } from 'react';
import { Shield, Upload, CheckCircle, Calculator, AlertTriangle, FileText, Download, ChevronRight, ChevronLeft, Clock, HelpCircle, RefreshCw } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';
import { useToast } from '../../lib/toast';

const STEPS = [
  { id: 'scope', title: 'Scope Check', desc: 'Verify eligibility' },
  { id: 'upload', title: 'Upload Docs', desc: 'Form 16, AIS, 26AS' },
  { id: 'reconcile', title: 'Reconciliation', desc: '3-way match' },
  { id: 'salary', title: 'Salary & HRA', desc: 'Confirm income' },
  { id: 'other', title: 'Other Income', desc: 'Interest, dividends' },
  { id: 'cg', title: 'Capital Gains', desc: 'Lot-wise review' },
  { id: 'deductions', title: 'Deductions', desc: '80C/D/E/G' },
  { id: 'compute', title: 'Computation', desc: 'Both regimes' },
  { id: 'validate', title: 'Validation', desc: 'Final checks' },
  { id: 'export', title: 'Export & File', desc: 'ITR JSON' },
];

const FY = '2025-26';

const errMsg = (e) => (typeof e === 'string' ? e : e?.message || e?.detail || JSON.stringify(e) || 'Something went wrong');

export default function ITRWizard() {
  const [step, setStep] = useState(0);
  const [scopeResult, setScopeResult] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);
  const [checklist, setChecklist] = useState(null);
  const [computation, setComputation] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [validation, setValidation] = useState(null);
  const [optimization, setOptimization] = useState(null);
  const [calendar, setCalendar] = useState(null);
  const [cgData, setCgData] = useState(null);
  const [uploads, setUploads] = useState({ form16: null, ais: null, form26as: null });
  const [uploadResults, setUploadResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState({});
  const [uploadErrors, setUploadErrors] = useState({});
  const [salary, setSalary] = useState({ gross: '', basic: '', hra_received: '', professional_tax: '', employer_pf: '' });
  const [hra, setHra] = useState({ rent_paid: '', city_name: '' });
  const [otherIncome, setOtherIncome] = useState({ savings_interest: '', fd_interest: '', dividend_income_gross: '', interest_on_it_refund: '', other: '' });
  const [deductions, setDeductions] = useState({ sec_80c: '', sec_80ccd_1b: '', sec_80d_self: '', sec_80d_parents: '', sec_80e: '', sec_80g: '', sec_80tta: '' });
  const toast = useToast();

  const saveProfile = async () => {
    try {
      await api(`/api/v1/itr/profile/${FY}`, {
        method: 'PUT',
        body: JSON.stringify({
          salary: Object.fromEntries(Object.entries(salary).map(([k, v]) => [k, Number(v) || 0])),
          hra: { rent_paid: Number(hra.rent_paid) || 0, city_name: hra.city_name },
          other_income: Object.fromEntries(Object.entries(otherIncome).map(([k, v]) => [k, Number(v) || 0])),
          deductions: Object.fromEntries(Object.entries(deductions).map(([k, v]) => [k, Number(v) || 0])),
        }),
      });
      toast?.success('Profile saved');
    } catch { toast?.error('Failed to save profile'); }
  };

  const loadCG = async () => {
    try { setCgData(await api(`/api/v1/itr/capital-gains/${FY}`)); } catch { toast?.error('Failed to load capital gains'); }
  };

  const exportITR = async () => {
    setLoading(true); setError('');
    try {
      const res = await api(`/api/v1/itr/export/${FY}`, { method: 'POST' });
      const blob = new Blob([res.json_string], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `ITR_${FY}.json`; a.click();
      URL.revokeObjectURL(url);
      toast?.success('ITR exported');
    } catch (e) { setError(errMsg(e)); }
    setLoading(false);
  };

  const [pdfPasswords, setPdfPasswords] = useState({ form16: '', ais: '', form26as: '' });

  const resolveAISItem = async (itemId, status) => {
    try {
      await api(`/api/v1/itr/ais-item/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify({ status, is_exempt: status === 'exempt' }),
      });
      await loadReconciliation(); // refresh
    } catch (e) { setError(errMsg(e)); }
  };

  const resolveAllAIS = async () => {
    setLoading(true);
    for (const item of (checklist?.items || [])) {
      if (item.status === 'pending') {
        await resolveAISItem(item.id, 'accepted');
      }
    }
    setLoading(false);
  };

  const handleUpload = async (endpoint, file) => {
    if (!file) return;
    setUploading(prev => ({ ...prev, [endpoint]: true }));
    setUploadErrors(prev => ({ ...prev, [endpoint]: null }));
    // Clear old results for this file
    setUploadResults(prev => ({ ...prev, [endpoint]: null }));
    setUploads(prev => ({ ...prev, [endpoint]: null }));
    try {
      const formData = new FormData();
      formData.append('file', file);
      const pw = pdfPasswords[endpoint];
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({ fy: FY });
      if (pw) params.append('password', pw);
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/itr/upload/${endpoint}?${params}`,
        { method: 'POST', body: formData, headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setUploads(prev => ({ ...prev, [endpoint]: file.name }));
      setUploadResults(prev => ({ ...prev, [endpoint]: data }));
      toast?.success(`${file.name} uploaded successfully`);
    } catch (e) {
      setUploadErrors(prev => ({ ...prev, [endpoint]: errMsg(e) }));
      toast?.error(`Upload failed: ${errMsg(e)}`);
    }
    setUploading(prev => ({ ...prev, [endpoint]: false }));
  };

  useEffect(() => { loadCalendar(); }, []);

  const loadCalendar = async () => {
    try { setCalendar(await api(`/api/v1/itr/tax-calendar?fy=${FY}`)); } catch {}
  };

  const runScopeCheck = async () => {
    setLoading(true); setError('');
    try {
      const res = await api('/api/v1/itr/scope-check', { method: 'POST', body: JSON.stringify({ residency: 'resident', transactions: [] }) });
      setScopeResult(res);
    } catch (e) { setError(errMsg(e)); }
    setLoading(false);
  };

  const loadReconciliation = async () => {
    setLoading(true); setError('');
    try {
      const [recon, cl] = await Promise.all([
        api(`/api/v1/itr/reconciliation/${FY}`),
        api(`/api/v1/itr/checklist/${FY}`),
      ]);
      setReconciliation(recon);
      setChecklist(cl);
    } catch (e) { setError(errMsg(e)); }
    setLoading(false);
  };

  const runComputation = async () => {
    setLoading(true); setError('');
    try {
      const [comp, cmp, opt] = await Promise.all([
        api(`/api/v1/itr/compute/${FY}&regime=new`, { method: 'POST' }),
        api(`/api/v1/itr/comparison/${FY}`),
        api(`/api/v1/itr/optimize/${FY}`),
      ]);
      setComputation(comp); setComparison(cmp); setOptimization(opt);
    } catch (e) { setError(errMsg(e)); }
    setLoading(false);
  };

  const runValidation = async () => {
    setLoading(true); setError('');
    try {
      setValidation(await api(`/api/v1/itr/validate/${FY}`, { method: 'POST' }));
    } catch (e) { setError(errMsg(e)); }
    setLoading(false);
  };

  const canGoNext = () => {
    if (step === 0 && scopeResult && !scopeResult.supported) return false;
    if (step === 2 && checklist && !checklist.can_proceed) return false;
    if (step === 8 && validation && !validation.can_proceed) return false;
    return true;
  };

  const fmt = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN')}` : '—';

  const renderStep = () => {
    switch (STEPS[step].id) {
      case 'scope': return (
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">We'll check if your tax situation is supported by this system.</p>
          <button onClick={runScopeCheck} disabled={loading} className="px-6 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50 font-medium">
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

      case 'upload': return (
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">Upload your tax documents. All data is parsed locally and shown for your confirmation.</p>
          {[
            { name: 'Form 16', hint: 'PDF from employer', endpoint: 'form16', needsPassword: false },
            { name: 'AIS (Annual Information Statement)', hint: 'Password: PAN(lowercase) + DOB(DDMMYYYY)', endpoint: 'ais', needsPassword: true },
            { name: 'Form 26AS', hint: 'Download from TRACES portal', endpoint: 'form26as', needsPassword: true },
          ].map((doc) => (
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
                    <input type="file" accept=".pdf" className="hidden" onChange={(e) => { handleUpload(doc.endpoint, e.target.files[0]); e.target.value = ''; }} />
                  </label>
                </div>
              </div>
              {uploadErrors[doc.endpoint] && (
                <div className="mt-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{uploadErrors[doc.endpoint]}</div>
              )}
              {doc.needsPassword && (
                <div className="mt-3">
                  <label className="text-xs text-[var(--text-muted)] mb-1 block">PDF Password (if protected)</label>
                  <input type="text" value={pdfPasswords[doc.endpoint]} onChange={e => setPdfPasswords(p => ({ ...p, [doc.endpoint]: e.target.value }))}
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
                      <div><span className="text-[var(--text-muted)]">Confidence:</span> <span className={uploadResults[doc.endpoint].confidence >= 0.8 ? 'text-green-400' : 'text-yellow-400'}>{Math.round(uploadResults[doc.endpoint].confidence * 100)}%</span></div>
                    </div>
                  )}
                  {doc.endpoint === 'ais' && uploadResults[doc.endpoint].summary && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                      <div><span className="text-[var(--text-muted)]">Entries:</span> <span className="text-[var(--text-primary)]">{uploadResults[doc.endpoint].summary.total_entries}</span></div>
                      <div><span className="text-[var(--text-muted)]">TDS:</span> <span className="text-[var(--text-primary)]">{uploadResults[doc.endpoint].summary.tds_entries}</span></div>
                      <div><span className="text-[var(--text-muted)]">Exempt:</span> <span className="text-[var(--text-primary)]">{uploadResults[doc.endpoint].summary.exempt_entries}</span></div>
                    </div>
                  )}
                  {doc.endpoint === 'form26as' && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                      <div><span className="text-[var(--text-muted)]">Total TDS:</span> <span className="text-[var(--text-primary)]">{fmt(uploadResults[doc.endpoint].total_tds)}</span></div>
                      <div><span className="text-[var(--text-muted)]">Entries:</span> <span className="text-[var(--text-primary)]">{uploadResults[doc.endpoint].tds_entries?.length || 0}</span></div>
                      <div><span className="text-[var(--text-muted)]">Advance Tax:</span> <span className="text-[var(--text-primary)]">{fmt(uploadResults[doc.endpoint].total_advance_tax)}</span></div>
                    </div>
                  )}
                  {uploadResults[doc.endpoint].warnings?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {uploadResults[doc.endpoint].warnings.map((w, i) => (
                        <p key={i} className="text-yellow-400 text-xs">⚠️ {w}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          {loading && <p className="text-[var(--text-muted)] text-sm">Parsing document...</p>}
          <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <p className="text-blue-300 text-sm flex items-center gap-2"><HelpCircle size={14} />Don't have these? You can enter data manually in the next steps.</p>
          </div>
        </div>
      );

      case 'reconcile': return (
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">Every AIS item must be resolved before proceeding. This prevents IT notices.</p>
          <button onClick={loadReconciliation} disabled={loading} className="px-5 py-2.5 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 font-medium">
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
                  <p className="text-yellow-400 text-sm">⚠️ {checklist.pending} items pending. Resolve all to proceed.</p>
                  <button onClick={resolveAllAIS} disabled={loading} className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs hover:bg-green-700 disabled:opacity-50">
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
                          <button onClick={() => resolveAISItem(item.id, 'accepted')} className="px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700">✓ Accept</button>
                          <button onClick={() => resolveAISItem(item.id, 'disputed')} className="px-2 py-1 bg-red-600/20 text-red-400 border border-red-500/30 rounded text-xs hover:bg-red-600/30">✗ Dispute</button>
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

      case 'salary': return (
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">Confirm your salary details. Standard deduction (₹75K new / ₹50K old) applied automatically.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[['Gross Salary', 'gross'], ['Basic + DA', 'basic'], ['HRA Received', 'hra_received'], ['Professional Tax', 'professional_tax'], ['Employer PF', 'employer_pf']].map(([label, key]) => (
              <div key={key}>
                <label className="text-xs text-[var(--text-muted)] mb-1 block">{label}</label>
                <input type="number" value={salary[key]} onChange={e => setSalary(p => ({ ...p, [key]: e.target.value }))}
                  className="w-full bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)]" placeholder="₹0" />
              </div>
            ))}
          </div>
          <div className="border-t border-[var(--border)] pt-4 mt-4">
            <h3 className="font-medium text-[var(--text-primary)] mb-3">HRA Calculation</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-[var(--text-muted)] mb-1 block">Rent Paid (Annual)</label>
                <input type="number" value={hra.rent_paid} onChange={e => setHra(p => ({ ...p, rent_paid: e.target.value }))}
                  className="w-full bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)]" placeholder="₹0" />
              </div>
              <div>
                <label className="text-xs text-[var(--text-muted)] mb-1 block">City</label>
                <input type="text" value={hra.city_name} onChange={e => setHra(p => ({ ...p, city_name: e.target.value }))}
                  className="w-full bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)]" placeholder="e.g. Mumbai" />
              </div>
            </div>
          </div>
          <button onClick={saveProfile} className="px-5 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 text-sm font-medium">Save Salary Details</button>
        </div>
      );

      case 'other': return (
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">Declare all other income. AIS amounts shown for reference.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[['Savings Interest', 'savings_interest'], ['FD Interest', 'fd_interest'], ['Dividend (Gross)', 'dividend_income_gross'], ['Interest on IT Refund', 'interest_on_it_refund'], ['Other Income', 'other']].map(([label, key]) => (
              <div key={key}>
                <label className="text-xs text-[var(--text-muted)] mb-1 block">{label}</label>
                <input type="number" value={otherIncome[key]} onChange={e => setOtherIncome(p => ({ ...p, [key]: e.target.value }))}
                  className="w-full bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)]" placeholder="₹0" />
              </div>
            ))}
          </div>
          <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-sm space-y-1">
            <p className="text-yellow-300">💡 FD interest is taxable when accrued, not when received.</p>
            <p className="text-yellow-300">💡 Report GROSS dividend amount (before TDS).</p>
          </div>
          <button onClick={saveProfile} className="px-5 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 text-sm font-medium">Save Other Income</button>
        </div>
      );

      case 'cg': return (
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">Capital gains computed from your portfolio using FIFO lot matching.</p>
          {!cgData && <button onClick={loadCG} className="px-5 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 text-sm font-medium">Load Capital Gains</button>}
          <div className="grid grid-cols-2 gap-3">
            {[['STCG 111A (20%)', cgData?.stcg_111a], ['LTCG 112A (12.5%)', cgData?.ltcg_112a_gross], ['STCG Other (slab)', cgData?.stcg_other], ['LTCG Other (12.5%)', cgData?.ltcg_other]].map(([label, val], i) => (
              <div key={i} className="p-4 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg">
                <p className="text-xs text-[var(--text-muted)]">{label}</p>
                <p className="text-xl font-semibold text-[var(--text-primary)] mt-1">{fmt(val || 0)}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-[var(--text-muted)]">LTCG 112A exemption: ₹1.25L applied to aggregate across all holdings.</p>
        </div>
      );

      case 'deductions': return (
        <div className="space-y-4">
          <p className="text-[var(--text-secondary)]">Enter deductions. Limits enforced automatically.</p>
          <div className="space-y-3">
            {[['80C (ELSS, PPF, EPF, LIC)', 'sec_80c', '₹1,50,000'], ['80CCD(1B) (NPS)', 'sec_80ccd_1b', '₹50,000'], ['80D Self (Health Insurance)', 'sec_80d_self', '₹25,000 / ₹50,000'], ['80D Parents', 'sec_80d_parents', '₹25,000 / ₹50,000'], ['80E (Education Loan)', 'sec_80e', 'Unlimited'], ['80G (Donations)', 'sec_80g', 'Varies'], ['80TTA (Savings Interest)', 'sec_80tta', '₹10,000']].map(([label, key, limit]) => (
              <div key={key} className="flex items-center gap-3">
                <div className="flex-1">
                  <label className="text-xs text-[var(--text-muted)] mb-1 block">{label}</label>
                  <input type="number" value={deductions[key]} onChange={e => setDeductions(p => ({ ...p, [key]: e.target.value }))}
                    className="w-full bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)]" placeholder="₹0" />
                </div>
                <span className="text-xs text-[var(--text-muted)] w-28 text-right pt-4">Max: {limit}</span>
              </div>
            ))}
          </div>
          <button onClick={saveProfile} className="px-5 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 text-sm font-medium">Save Deductions</button>
        </div>
      );

      case 'compute': return (
        <div className="space-y-4">
          <button onClick={runComputation} disabled={loading} className="px-6 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 font-medium">
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

      case 'validate': return (
        <div className="space-y-4">
          <button onClick={runValidation} disabled={loading} className="px-6 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 font-medium">
            {loading ? 'Validating...' : 'Run Final Validation'}
          </button>
          {validation && (
            <div>
              <div className={`p-4 rounded-lg mb-4 border ${validation.can_proceed ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                <p className={validation.can_proceed ? 'text-green-400 font-medium' : 'text-red-400 font-medium'}>
                  {validation.can_proceed ? '✅ All checks passed! Ready to export.' : '❌ Issues found. Fix before exporting.'}
                </p>
              </div>
              {validation.hard_blocks?.map((b, i) => (
                <div key={i} className="p-3 mb-2 bg-red-500/5 border border-red-500/30 rounded-lg">
                  <p className="text-red-300">{b.message}</p>
                  {b.guidance && <p className="text-sm text-[var(--text-muted)] mt-1">{b.guidance}</p>}
                </div>
              ))}
              {validation.warnings?.map((w, i) => (
                <div key={i} className="p-3 mb-2 bg-yellow-500/5 border border-yellow-500/30 rounded-lg">
                  <p className="text-yellow-300">{w.message}</p>
                </div>
              ))}
              {validation.itr_form && (
                <div className="p-4 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg mt-3">
                  <p className="font-medium text-[var(--text-primary)]">Recommended Form: {validation.itr_form}</p>
                  {validation.itr_form_reasons?.map((r, i) => (
                    <p key={i} className="text-sm text-[var(--text-muted)]">• {r}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      );

      case 'export': return (
        <div className="space-y-6">
          <div className="p-8 bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-xl text-center">
            <Download size={40} className="mx-auto mb-4 text-[var(--accent)]" />
            <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">Export ITR JSON</h3>
            <p className="text-[var(--text-muted)] mb-5">Download the JSON file and upload it on the Income Tax e-filing portal.</p>
            <button onClick={exportITR} disabled={loading} className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium disabled:opacity-50">
              {loading ? 'Generating...' : `Download ${validation?.itr_form || 'ITR-2'} JSON`}
            </button>
          </div>
          <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <h3 className="font-medium text-blue-300 mb-2">📋 After Filing</h3>
            <ol className="text-sm text-[var(--text-muted)] space-y-1 list-decimal list-inside">
              <li>Upload JSON on incometax.gov.in → e-File → Income Tax Returns</li>
              <li>E-verify within 30 days (Aadhaar OTP / Net Banking / DSC)</li>
              <li>Save acknowledgment (ITR-V) for your records</li>
              <li>Track refund status on the portal</li>
            </ol>
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

      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-1">
          <h1 className="text-xl md:text-2xl font-bold text-[var(--text-primary)]">ITR Filing Assistant</h1>
          <span className="text-xs text-[var(--text-muted)] bg-[var(--bg-secondary)] border border-[var(--border)] px-3 py-1 rounded-full">
            Step {step + 1} / {STEPS.length}
          </span>
        </div>
        <p className="text-sm text-[var(--text-muted)] mb-5">FY {FY} • CA-grade accuracy • Zero-error filing</p>

        {/* Progress Bar */}
        <div className="w-full bg-[var(--bg-tertiary)] rounded-full h-1.5 mb-5">
          <div className="bg-[var(--accent)] h-1.5 rounded-full transition-all duration-500" style={{ width: `${((step + 1) / STEPS.length) * 100}%` }} />
        </div>

        {/* Step Tabs */}
        <div className="flex flex-wrap gap-1.5 mb-5">
          {STEPS.map((s, i) => {
            const active = i === step;
            const done = i < step;
            return (
              <button key={i} onClick={() => setStep(i)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all
                  ${active ? 'bg-[var(--accent)] text-white' : done ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-[var(--bg-secondary)] text-[var(--text-muted)] border border-[var(--border)] hover:text-[var(--text-secondary)]'}`}>
                {done ? <CheckCircle size={12} /> : <span className="w-4 h-4 rounded-full border border-current flex items-center justify-center text-[9px]">{i + 1}</span>}
                {s.title}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl p-5 md:p-6 mb-5">
          <h2 className="text-base font-semibold text-[var(--text-primary)] mb-0.5">{STEPS[step].title}</h2>
          <p className="text-xs text-[var(--text-muted)] mb-4">{STEPS[step].desc}</p>
          {error && <div className="p-3 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">{error}</div>}
          {renderStep()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          {step > 0 ? (
            <button onClick={() => { setStep(step - 1); setError(''); }} className="px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] flex items-center gap-2 text-sm">
              <ChevronLeft size={16} /> Previous
            </button>
          ) : <div />}
          <button onClick={() => { setStep(Math.min(STEPS.length - 1, step + 1)); setError(''); }}
            disabled={step === STEPS.length - 1 || !canGoNext()}
            className="px-4 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-30 flex items-center gap-2 text-sm font-medium">
            Next <ChevronRight size={16} />
          </button>
        </div>
      </main>
    </div>
  );
}
