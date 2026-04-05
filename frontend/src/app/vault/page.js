'use client';
import { useState, useEffect } from 'react';
import { Shield, Plus, Trash2, X, Pencil, Users, Building2, Heart, TrendingUp, Home, FileText, Smartphone, Phone, Upload, File, Download } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { getVaultEntries, createVaultEntry, updateVaultEntry, deleteVaultEntry, getVaultNominees, addVaultNominee, removeVaultNominee, uploadVaultFile, deleteVaultFile, getVaultFileUrl } from '../../lib/api';
import { useAsyncAction } from '../../lib/useAsyncAction';
import { useConfirm } from '../../lib/confirm';

const CATEGORIES = [
  { id: 'bank', label: 'Bank Accounts', icon: Building2, fields: ['bank_name', 'account_number', 'ifsc', 'branch', 'account_type', 'balance'] },
  { id: 'insurance', label: 'Insurance', icon: Heart, fields: ['company', 'policy_number', 'type', 'sum_assured', 'premium', 'maturity_date', 'nominee'] },
  { id: 'investment', label: 'Investments', icon: TrendingUp, fields: ['type', 'institution', 'account_number', 'value', 'nominee'] },
  { id: 'property', label: 'Property', icon: Home, fields: ['type', 'address', 'value', 'registration_number', 'owner'] },
  { id: 'legal', label: 'Legal', icon: FileText, fields: ['document_type', 'location', 'lawyer_name', 'lawyer_contact'] },
  { id: 'digital', label: 'Digital', icon: Smartphone, fields: ['service', 'username', 'recovery_email', 'notes'] },
  { id: 'contact', label: 'Contacts', icon: Phone, fields: ['name', 'relation', 'phone', 'email', 'role'] },
];

const FIELD_LABELS = {
  bank_name: 'Bank Name', account_number: 'Account Number', ifsc: 'IFSC Code', branch: 'Branch', account_type: 'Account Type', balance: 'Balance',
  company: 'Company', policy_number: 'Policy Number', type: 'Type', sum_assured: 'Sum Assured', premium: 'Premium', maturity_date: 'Maturity Date', nominee: 'Nominee',
  institution: 'Institution', value: 'Value', address: 'Address', registration_number: 'Registration No.', owner: 'Owner',
  document_type: 'Document Type', location: 'Location', lawyer_name: 'Lawyer Name', lawyer_contact: 'Lawyer Contact',
  service: 'Service', username: 'Username', recovery_email: 'Recovery Email', notes: 'Notes',
  name: 'Name', relation: 'Relation', phone: 'Phone', email: 'Email', role: 'Role'
};

export default function VaultPage() {
  const [entries, setEntries] = useState([]);
  const [nominees, setNominees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('bank');
  const [showForm, setShowForm] = useState(false);
  const [showNomineeForm, setShowNomineeForm] = useState(false);
  const [editEntry, setEditEntry] = useState(null);
  const [form, setForm] = useState({ title: '', details: {}, notes: '', nominee_visible: true });
  const [nomineeForm, setNomineeForm] = useState({ nominee_name: '', nominee_email: '', relation: '' });
  const confirm = useConfirm();

  const load = async () => {
    setLoading(true);
    try {
      const [e, n] = await Promise.all([getVaultEntries(activeTab), getVaultNominees()]);
      setEntries(e);
      setNominees(n);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [activeTab]);

  const currentCategory = CATEGORIES.find(c => c.id === activeTab);

  const openForm = (entry = null) => {
    if (entry) {
      setEditEntry(entry);
      setForm({ title: entry.title, details: entry.details || {}, notes: entry.notes || '', nominee_visible: entry.nominee_visible });
    } else {
      setEditEntry(null);
      setForm({ title: '', details: {}, notes: '', nominee_visible: true });
    }
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await submitEntry();
  };

  const [submitEntry, submitting] = useAsyncAction(
    async () => {
      const payload = { category: activeTab, title: form.title, details: form.details, notes: form.notes || null, nominee_visible: form.nominee_visible };
      if (editEntry) await updateVaultEntry(editEntry.id, payload);
      else await createVaultEntry(payload);
      setShowForm(false);
      load();
    },
    { successMsg: editEntry ? 'Entry updated' : 'Entry added' }
  );

  const [handleDelete, deleting] = useAsyncAction(
    async (id) => { if (!await confirm('Delete this entry?')) return; await deleteVaultEntry(id); load(); },
    { successMsg: 'Entry deleted' }
  );

  const handleAddNominee = async (e) => {
    e.preventDefault();
    await submitNominee();
  };

  const [submitNominee, addingNominee] = useAsyncAction(
    async () => {
      await addVaultNominee(nomineeForm);
      setNomineeForm({ nominee_name: '', nominee_email: '', relation: '' });
      setShowNomineeForm(false);
      load();
    },
    { successMsg: 'Nominee added' }
  );

  const [handleRemoveNominee, removingNominee] = useAsyncAction(
    async (id) => { if (!await confirm('Remove this nominee?')) return; await removeVaultNominee(id); load(); },
    { successMsg: 'Nominee removed' }
  );

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <h1 className="text-xl md:text-xl md:text-2xl font-bold flex items-center gap-2"><Shield className="w-5 h-5 md:w-6 md:h-6" /> Family Vault</h1>
          <div className="flex gap-2">
            <button onClick={() => setShowNomineeForm(true)} className="flex items-center gap-2 px-3 md:px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] rounded-lg text-sm font-medium hover:bg-[var(--bg-tertiary)]">
              <Users className="w-4 h-4" /> <span className="hidden sm:inline">Nominees</span> ({nominees.length})
            </button>
            <button onClick={() => openForm()} className="flex items-center gap-2 px-3 md:px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:opacity-90">
              <Plus className="w-4 h-4" /> <span className="hidden sm:inline">Add Entry</span>
            </button>
          </div>
        </div>

        {/* Category Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0">
          {CATEGORIES.map(cat => (
            <button key={cat.id} onClick={() => setActiveTab(cat.id)} className={`flex items-center gap-1.5 md:gap-2 px-3 md:px-4 py-2 rounded-lg text-xs md:text-sm font-medium whitespace-nowrap transition-colors ${activeTab === cat.id ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'}`}>
              <cat.icon className="w-4 h-4" /> <span className="hidden sm:inline">{cat.label}</span><span className="sm:hidden">{cat.label.split(' ')[0]}</span>
            </button>
          ))}
        </div>

        {/* Entries Grid */}
        {loading ? (
          <div className="text-center py-12 text-[var(--text-muted)]">Loading...</div>
        ) : entries.length === 0 ? (
          <div className="text-center py-12 text-[var(--text-muted)]">No entries in {currentCategory?.label}. Click "Add Entry" to create one.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {entries.map(entry => (
              <div key={entry.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-[var(--text-primary)]">{entry.title}</h3>
                  <div className="flex gap-1">
                    <label className="p-1.5 rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-muted)] cursor-pointer">
                      <Upload className="w-4 h-4" />
                      <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={async (e) => { if (e.target.files[0]) { await uploadVaultFile(entry.id, e.target.files[0]); load(); } }} />
                    </label>
                    <button onClick={() => openForm(entry)} className="p-1.5 rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-muted)]"><Pencil className="w-4 h-4" /></button>
                    <button onClick={() => handleDelete(entry.id)} className="p-1.5 rounded hover:bg-[#ef4444]/10 text-[var(--text-muted)] hover:text-[#ef4444]"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
                <div className="space-y-1.5 text-sm">
                  {Object.entries(entry.details || {}).filter(([_, v]) => v).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-[var(--text-muted)]">{FIELD_LABELS[k] || k}</span>
                      <span className="text-[var(--text-primary)] font-medium">{v}</span>
                    </div>
                  ))}
                </div>
                {entry.files?.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-[var(--border)]">
                    <div className="text-xs text-[var(--text-muted)] mb-1">Attachments</div>
                    <div className="flex flex-wrap gap-1">
                      {entry.files.map(f => (
                        <div key={f} className="flex items-center gap-1 text-xs bg-[var(--bg-tertiary)] rounded px-2 py-1">
                          <File className="w-3 h-3" />
                          <a href={getVaultFileUrl(f)} target="_blank" className="hover:text-[var(--accent)]">{f.slice(0, 12)}...</a>
                          <button onClick={async () => { await deleteVaultFile(entry.id, f); load(); }} className="hover:text-[#ef4444]"><X className="w-3 h-3" /></button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {entry.notes && <p className="mt-3 text-xs text-[var(--text-muted)] border-t border-[var(--border)] pt-2">{entry.notes}</p>}
                {!entry.nominee_visible && <span className="inline-block mt-2 text-xs px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-[var(--text-muted)]">Hidden from nominees</span>}
              </div>
            ))}
          </div>
        )}

        {/* Entry Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-[var(--bg-secondary)] rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 border-b border-[var(--border)]">
                <h2 className="font-semibold">{editEntry ? 'Edit' : 'Add'} {currentCategory?.label} Entry</h2>
                <button onClick={() => setShowForm(false)} className="p-1 hover:bg-[var(--bg-tertiary)] rounded"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={handleSubmit} className="p-4 space-y-4">
                <div>
                  <label className="block text-sm text-[var(--text-muted)] mb-1">Title *</label>
                  <input type="text" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm" placeholder="e.g., HDFC Savings Account" />
                </div>
                {currentCategory?.fields.map(field => (
                  <div key={field}>
                    <label className="block text-sm text-[var(--text-muted)] mb-1">{FIELD_LABELS[field]}</label>
                    <input type="text" value={form.details[field] || ''} onChange={e => setForm({ ...form, details: { ...form.details, [field]: e.target.value } })} className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm" />
                  </div>
                ))}
                <div>
                  <label className="block text-sm text-[var(--text-muted)] mb-1">Notes</label>
                  <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} rows={2} className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm" placeholder="Additional notes..." />
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={form.nominee_visible} onChange={e => setForm({ ...form, nominee_visible: e.target.checked })} className="rounded" />
                  <span className="text-[var(--text-secondary)]">Visible to nominees</span>
                </label>
                <button type="submit" className="w-full py-2 bg-[var(--accent)] text-white rounded-lg font-medium hover:opacity-90">{editEntry ? 'Update' : 'Add'} Entry</button>
              </form>
            </div>
          </div>
        )}

        {/* Nominee Form Modal */}
        {showNomineeForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-[var(--bg-secondary)] rounded-lg w-full max-w-md">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 border-b border-[var(--border)]">
                <h2 className="font-semibold">Manage Nominees</h2>
                <button onClick={() => setShowNomineeForm(false)} className="p-1 hover:bg-[var(--bg-tertiary)] rounded"><X className="w-5 h-5" /></button>
              </div>
              <div className="p-4">
                {nominees.length > 0 && (
                  <div className="mb-4 space-y-2">
                    {nominees.map(n => (
                      <div key={n.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-[var(--bg-primary)] rounded-lg">
                        <div>
                          <div className="font-medium text-sm">{n.nominee_name}</div>
                          <div className="text-xs text-[var(--text-muted)]">{n.nominee_email} {n.relation && `• ${n.relation}`}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded ${n.accepted ? 'bg-[#10b981]/20 text-[#10b981]' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)]'}`}>{n.accepted ? 'Accepted' : 'Pending'}</span>
                          <button onClick={() => handleRemoveNominee(n.id)} className="p-1 hover:bg-[#ef4444]/10 rounded text-[var(--text-muted)] hover:text-[#ef4444]"><Trash2 className="w-4 h-4" /></button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <form onSubmit={handleAddNominee} className="space-y-3">
                  <input type="text" value={nomineeForm.nominee_name} onChange={e => setNomineeForm({ ...nomineeForm, nominee_name: e.target.value })} required placeholder="Name" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm" />
                  <input type="email" value={nomineeForm.nominee_email} onChange={e => setNomineeForm({ ...nomineeForm, nominee_email: e.target.value })} required placeholder="Email" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm" />
                  <input type="text" value={nomineeForm.relation} onChange={e => setNomineeForm({ ...nomineeForm, relation: e.target.value })} placeholder="Relation (optional)" className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm" />
                  <button type="submit" className="w-full py-2 bg-[var(--accent)] text-white rounded-lg font-medium hover:opacity-90">Add Nominee</button>
                </form>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
