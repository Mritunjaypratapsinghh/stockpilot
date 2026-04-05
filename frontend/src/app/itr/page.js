'use client';
import { useState, useEffect, useCallback } from 'react';
import { Shield, Upload, CheckCircle, Calculator, AlertTriangle, FileText, Download, ChevronRight, ChevronLeft, Clock, HelpCircle, RefreshCw } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

const STEPS = [
  { id: 'scope', title: 'Scope Check', icon: Shield, desc: 'Verify eligibility' },
  { id: 'upload', title: 'Upload Documents', icon: Upload, desc: 'Form 16, AIS, 26AS' },
  { id: 'reconcile', title: 'Reconciliation', icon: CheckCircle, desc: '3-way match' },
  { id: 'salary', title: 'Salary & HRA', icon: Calculator, desc: 'Confirm income' },
  { id: 'other', title: 'Other Income', icon: FileText, desc: 'Interest, dividends' },
  { id: 'cg', title: 'Capital Gains', icon: Calculator, desc: 'Lot-wise review' },
  { id: 'deductions', title: 'Deductions', icon: FileText, desc: '80C/D/E/G' },
  { id: 'compute', title: 'Tax Computation', icon: Calculator, desc: 'Both regimes' },
  { id: 'validate', title: 'Validation', icon: AlertTriangle, desc: 'Final checks' },
  { id: 'export', title: 'Export & File', icon: Download, desc: 'ITR JSON' },
];

const FY = '2025-26';

export default function ITRWizard() {
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState(null);
  const [scopeResult, setScopeResult] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);
  const [checklist, setChecklist] = useState(null);
  const [computation, setComputation] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [validation, setValidation] = useState(null);
  const [hraResult, setHraResult] = useState(null);
  const [optimization, setOptimization] = useState(null);
  const [calendar, setCalendar] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { loadProfile(); loadCalendar(); }, []);

  const loadProfile = async () => {
    try {
      const data = await api(`/api/v1/itr/profile/${FY}?user_id=me`);
      setProfile(data);
    } catch { /* new user */ }
  };

  const loadCalendar = async () => {
    try { setCalendar(await api(`/api/v1/itr/tax-calendar?fy=${FY}`)); } catch {}
  };

  const runScopeCheck = async () => {
    setLoading(true);
    try {
      const res = await api('/api/v1/itr/scope-check?user_id=me', { method: 'POST', body: JSON.stringify({ residency: 'resident', transactions: [] }) });
      setScopeResult(res);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const loadReconciliation = async () => {
    setLoading(true);
    try {
      const [recon, cl] = await Promise.all([
        api(`/api/v1/itr/reconciliation/${FY}?user_id=me`),
        api(`/api/v1/itr/checklist/${FY}?user_id=me`),
      ]);
      setReconciliation(recon);
      setChecklist(cl);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const runComputation = async () => {
    setLoading(true);
    try {
      const [comp, cmp, opt] = await Promise.all([
        api(`/api/v1/itr/compute/${FY}?user_id=me&regime=new`, { method: 'POST' }),
        api(`/api/v1/itr/comparison/${FY}?user_id=me`),
        api(`/api/v1/itr/optimize/${FY}?user_id=me`),
      ]);
      setComputation(comp);
      setComparison(cmp);
      setOptimization(opt);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const runValidation = async () => {
    setLoading(true);
    try {
      setValidation(await api(`/api/v1/itr/validate/${FY}?user_id=me`, { method: 'POST' }));
    } catch (e) { setError(e.message); }
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
          <p className="text-gray-400">We'll check if your tax situation is supported by this system.</p>
          <button onClick={runScopeCheck} disabled={loading} className="px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Checking...' : 'Run Scope Check'}
          </button>
          {scopeResult && (
            <div className={`p-4 rounded-lg ${scopeResult.supported ? 'bg-green-900/30 border border-green-700' : 'bg-red-900/30 border border-red-700'}`}>
              {scopeResult.supported ? (
                <p className="text-green-400 flex items-center gap-2"><CheckCircle size={20} /> Your tax situation is fully supported. Proceed!</p>
              ) : (
                <div>
                  <p className="text-red-400 font-semibold mb-2">⚠️ Unsupported case detected:</p>
                  {scopeResult.blockers?.map((b, i) => (
                    <div key={i} className="mb-2 p-3 bg-red-900/20 rounded">
                      <p className="text-red-300 font-medium">{b.message}</p>
                      <p className="text-gray-400 text-sm mt-1">{b.guidance}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      );

      case 'upload': return (
        <div className="space-y-6">
          <p className="text-gray-400">Upload your tax documents. All data is parsed locally and shown for your confirmation.</p>
          {['Form 16', 'AIS (Annual Information Statement)', 'Form 26AS'].map((doc, i) => (
            <div key={i} className="p-4 border border-gray-700 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">{doc}</h3>
                  <p className="text-sm text-gray-400">{i === 1 ? 'Password: PAN(lowercase) + DOB(DDMMYYYY)' : 'PDF format'}</p>
                </div>
                <label className="px-4 py-2 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600">
                  <Upload size={16} className="inline mr-2" />Upload
                  <input type="file" accept=".pdf" className="hidden" onChange={() => {}} />
                </label>
              </div>
            </div>
          ))}
          <div className="p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
            <p className="text-blue-300 text-sm"><HelpCircle size={14} className="inline mr-1" />Don't have these documents? You can enter data manually in the next steps.</p>
          </div>
        </div>
      );

      case 'reconcile': return (
        <div className="space-y-4">
          <p className="text-gray-400">Every AIS item must be resolved before proceeding. This prevents IT notices.</p>
          <button onClick={loadReconciliation} disabled={loading} className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700">
            {loading ? 'Loading...' : 'Load Reconciliation'}
          </button>
          {checklist && (
            <div>
              <div className="flex items-center gap-4 mb-4">
                <div className="flex-1 bg-gray-700 rounded-full h-3">
                  <div className="bg-green-500 h-3 rounded-full transition-all" style={{ width: `${checklist.progress * 100}%` }} />
                </div>
                <span className="text-sm">{checklist.resolved}/{checklist.total} resolved</span>
              </div>
              {!checklist.can_proceed && (
                <p className="text-yellow-400 text-sm mb-4">⚠️ {checklist.pending} items pending. Resolve all to proceed.</p>
              )}
              {checklist.items?.slice(0, 10).map((item, i) => (
                <div key={i} className={`p-3 mb-2 rounded-lg border ${item.status === 'pending' ? 'border-yellow-700 bg-yellow-900/10' : 'border-green-700 bg-green-900/10'}`}>
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="text-sm font-medium">{item.info_code}</span>
                      <span className="text-gray-400 text-sm ml-2">{item.description || item.source_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{fmt(item.reported_value)}</span>
                      <span className={`text-xs px-2 py-1 rounded ${item.status === 'pending' ? 'bg-yellow-800 text-yellow-300' : 'bg-green-800 text-green-300'}`}>
                        {item.status}
                      </span>
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
          <p className="text-gray-400">Confirm your salary details. Standard deduction (₹75K new / ₹50K old) applied automatically.</p>
          {['Gross Salary', 'Basic + DA', 'HRA Received', 'Professional Tax', 'Employer PF'].map((label, i) => (
            <div key={i} className="flex items-center gap-4">
              <label className="w-40 text-sm text-gray-400">{label}</label>
              <input type="number" className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2" placeholder="₹0" />
            </div>
          ))}
          <div className="mt-6 p-4 border border-gray-700 rounded-lg">
            <h3 className="font-medium mb-3">HRA Calculation</h3>
            {['Rent Paid (Annual)', 'City'].map((label, i) => (
              <div key={i} className="flex items-center gap-4 mb-2">
                <label className="w-40 text-sm text-gray-400">{label}</label>
                <input type={i === 0 ? 'number' : 'text'} className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2" placeholder={i === 0 ? '₹0' : 'e.g. Mumbai'} />
              </div>
            ))}
            {hraResult && (
              <div className="mt-3 p-3 bg-green-900/20 rounded-lg">
                <p className="text-green-400">HRA Exemption: {fmt(hraResult.exemption)}</p>
                <p className="text-sm text-gray-400">Limiting factor: {hraResult.limiting_factor}</p>
              </div>
            )}
          </div>
        </div>
      );

      case 'other': return (
        <div className="space-y-4">
          <p className="text-gray-400">Declare all other income. AIS amounts shown for reference.</p>
          {['Savings Interest', 'FD Interest', 'Dividend (Gross)', 'Interest on IT Refund', 'Other'].map((label, i) => (
            <div key={i} className="flex items-center gap-4">
              <label className="w-48 text-sm text-gray-400">{label}</label>
              <input type="number" className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2" placeholder="₹0" />
            </div>
          ))}
          <div className="p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg text-sm">
            <p className="text-yellow-300">💡 FD interest is taxable when accrued, not when received.</p>
            <p className="text-yellow-300 mt-1">💡 Report GROSS dividend amount (before TDS).</p>
          </div>
        </div>
      );

      case 'cg': return (
        <div className="space-y-4">
          <p className="text-gray-400">Capital gains computed from your portfolio using FIFO lot matching.</p>
          <div className="grid grid-cols-2 gap-4">
            {[
              ['STCG 111A (20%)', computation?.tax_stcg_111a],
              ['LTCG 112A (12.5%)', computation?.tax_ltcg_112a],
              ['STCG Other (slab)', 0],
              ['LTCG Other (12.5%)', computation?.tax_ltcg_other],
            ].map(([label, val], i) => (
              <div key={i} className="p-4 bg-gray-800 rounded-lg">
                <p className="text-sm text-gray-400">{label}</p>
                <p className="text-xl font-semibold">{fmt(val || 0)}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-400">LTCG 112A exemption: ₹1.25L applied to aggregate across all holdings.</p>
        </div>
      );

      case 'deductions': return (
        <div className="space-y-4">
          <p className="text-gray-400">Enter deductions. Limits enforced automatically.</p>
          {[
            ['80C (ELSS, PPF, EPF, LIC)', '₹1,50,000'],
            ['80CCD(1B) (NPS)', '₹50,000'],
            ['80D Self (Health Insurance)', '₹25,000 / ₹50,000'],
            ['80D Parents', '₹25,000 / ₹50,000'],
            ['80E (Education Loan)', 'Unlimited'],
            ['80G (Donations)', 'Varies'],
            ['80TTA (Savings Interest)', '₹10,000'],
          ].map(([label, limit], i) => (
            <div key={i} className="flex items-center gap-4">
              <label className="w-64 text-sm text-gray-400">{label}</label>
              <input type="number" className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2" placeholder="₹0" />
              <span className="text-xs text-gray-500 w-32">Max: {limit}</span>
            </div>
          ))}
        </div>
      );

      case 'compute': return (
        <div className="space-y-4">
          <button onClick={runComputation} disabled={loading} className="px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700">
            {loading ? 'Computing...' : 'Compute Tax (Both Regimes)'}
          </button>
          {comparison && (
            <div className="p-4 bg-green-900/20 border border-green-700 rounded-lg">
              <p className="text-green-400 text-lg font-semibold">Recommended: {comparison.recommended.toUpperCase()} Regime</p>
              <p className="text-gray-300">{comparison.explanation}</p>
            </div>
          )}
          {computation && (
            <div className="grid grid-cols-2 gap-4">
              {[
                ['Gross Total Income', computation.gross_total_income],
                ['Deductions', computation.total_deductions],
                ['Taxable Income', computation.taxable_normal_income],
                ['Tax on Normal', computation.tax_on_normal],
                ['STCG 111A Tax', computation.tax_stcg_111a],
                ['LTCG 112A Tax', computation.tax_ltcg_112a],
                ['Rebate 87A', computation.rebate_87a],
                ['Surcharge', (computation.surcharge_normal || 0) + (computation.surcharge_cg || 0)],
                ['Cess (4%)', computation.cess],
                ['Gross Tax', computation.gross_tax],
                ['TDS/Tax Paid', computation.total_tax_paid],
                ['Net Payable', computation.net_tax_payable],
              ].map(([label, val], i) => (
                <div key={i} className={`p-3 rounded-lg ${i === 11 ? (val < 0 ? 'bg-green-900/30 border border-green-700' : 'bg-red-900/30 border border-red-700') : 'bg-gray-800'}`}>
                  <p className="text-sm text-gray-400">{label}</p>
                  <p className={`text-lg font-semibold ${i === 11 && val < 0 ? 'text-green-400' : ''}`}>
                    {i === 11 && val < 0 ? `REFUND ${fmt(Math.abs(val))}` : fmt(val)}
                  </p>
                </div>
              ))}
            </div>
          )}
          {optimization?.suggestions?.length > 0 && (
            <div className="mt-4">
              <h3 className="font-medium mb-2">💡 Optimization Tips</h3>
              {optimization.suggestions.map((s, i) => (
                <div key={i} className="p-3 mb-2 bg-blue-900/20 border border-blue-700 rounded-lg">
                  <p className="font-medium text-blue-300">{s.title}</p>
                  <p className="text-sm text-gray-400">{s.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      );

      case 'validate': return (
        <div className="space-y-4">
          <button onClick={runValidation} disabled={loading} className="px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700">
            {loading ? 'Validating...' : 'Run Final Validation'}
          </button>
          {validation && (
            <div>
              <div className={`p-4 rounded-lg mb-4 ${validation.can_proceed ? 'bg-green-900/30 border border-green-700' : 'bg-red-900/30 border border-red-700'}`}>
                <p className={validation.can_proceed ? 'text-green-400' : 'text-red-400'}>
                  {validation.can_proceed ? '✅ All checks passed! Ready to export.' : '❌ Issues found. Fix before exporting.'}
                </p>
              </div>
              {validation.hard_blocks?.map((b, i) => (
                <div key={i} className="p-3 mb-2 bg-red-900/20 border border-red-700 rounded-lg">
                  <p className="text-red-300">{b.message}</p>
                  {b.guidance && <p className="text-sm text-gray-400 mt-1">{b.guidance}</p>}
                </div>
              ))}
              {validation.warnings?.map((w, i) => (
                <div key={i} className="p-3 mb-2 bg-yellow-900/20 border border-yellow-700 rounded-lg">
                  <p className="text-yellow-300">{w.message}</p>
                </div>
              ))}
              {validation.itr_form && (
                <div className="p-4 bg-gray-800 rounded-lg mt-4">
                  <p className="font-medium">Recommended Form: {validation.itr_form}</p>
                  {validation.itr_form_reasons?.map((r, i) => (
                    <p key={i} className="text-sm text-gray-400">• {r}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      );

      case 'export': return (
        <div className="space-y-6">
          <div className="p-6 bg-gray-800 rounded-lg text-center">
            <Download size={48} className="mx-auto mb-4 text-blue-400" />
            <h3 className="text-xl font-semibold mb-2">Export ITR JSON</h3>
            <p className="text-gray-400 mb-4">Download the JSON file and upload it on the Income Tax e-filing portal.</p>
            <button className="px-8 py-3 bg-green-600 rounded-lg hover:bg-green-700 font-medium">
              Download {validation?.itr_form || 'ITR-2'} JSON
            </button>
          </div>
          <div className="p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
            <h3 className="font-medium text-blue-300 mb-2">📋 After Filing</h3>
            <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
              <li>Upload JSON on incometax.gov.in → e-File → Income Tax Returns</li>
              <li>E-verify within 30 days (Aadhaar OTP / Net Banking / DSC)</li>
              <li>Save acknowledgment (ITR-V) for your records</li>
              <li>Track refund status on the portal</li>
            </ol>
          </div>
          {calendar?.deadlines && (
            <div className="p-4 bg-gray-800 rounded-lg">
              <h3 className="font-medium mb-2 flex items-center gap-2"><Clock size={16} /> Key Deadlines</h3>
              {calendar.deadlines.map((d, i) => (
                <div key={i} className="flex justify-between py-1 text-sm">
                  <span className="text-gray-400">{d.description}</span>
                  <span>{d.date}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );

      default: return <p>Step not implemented</p>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-bold">ITR Filing Assistant</h1>
          <span className="text-sm text-gray-400 bg-gray-800 px-3 py-1 rounded-full">Step {step + 1} of {STEPS.length}</span>
        </div>
        <p className="text-gray-400 mb-4">FY {FY} • CA-grade accuracy • Zero-error filing</p>

        {/* Progress Bar */}
        <div className="w-full bg-gray-800 rounded-full h-2 mb-6">
          <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${((step + 1) / STEPS.length) * 100}%` }} />
        </div>

        {/* Step Tabs — two rows on mobile, single scrollable row on desktop */}
        <div className="grid grid-cols-5 sm:flex sm:flex-wrap gap-2 mb-6">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const active = i === step;
            const done = i < step;
            return (
              <button key={i} onClick={() => setStep(i)}
                className={`flex items-center justify-center sm:justify-start gap-1.5 px-2.5 py-2 rounded-lg text-xs sm:text-sm whitespace-nowrap transition-all border
                  ${active ? 'bg-blue-600 border-blue-500 text-white' : done ? 'bg-green-900/20 border-green-800 text-green-400' : 'bg-gray-900 border-gray-700 text-gray-500 hover:border-gray-600'}`}>
                {done ? <CheckCircle size={14} className="shrink-0" /> : <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-[10px] shrink-0">{i + 1}</span>}
                <span className="hidden sm:inline">{s.title}</span>
              </button>
            );
          })}
        </div>

        {/* Step Content */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6 min-h-[400px]">
          <h2 className="text-lg font-semibold mb-1">{STEPS[step].title}</h2>
          <p className="text-sm text-gray-400 mb-4">{STEPS[step].desc}</p>
          {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
          {renderStep()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          {step > 0 ? (
            <button onClick={() => setStep(step - 1)}
              className="px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 flex items-center gap-2">
              <ChevronLeft size={16} /> Previous
            </button>
          ) : <div />}
          <button onClick={() => setStep(Math.min(STEPS.length - 1, step + 1))}
            disabled={step === STEPS.length - 1 || !canGoNext()}
            className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-30 flex items-center gap-2">
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
