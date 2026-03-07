'use client';
import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Shield, Users, ChevronRight, Building2, Heart, TrendingUp, Home, FileText, Smartphone, Phone, File } from 'lucide-react';
import Navbar from '../../../components/Navbar';
import { getSharedVaults, viewSharedVault, acceptVaultInvite, getVaultFileUrl } from '../../../lib/api';

const CATEGORY_ICONS = { bank: Building2, insurance: Heart, investment: TrendingUp, property: Home, legal: FileText, digital: Smartphone, contact: Phone };
const CATEGORY_LABELS = { bank: 'Bank Accounts', insurance: 'Insurance', investment: 'Investments', property: 'Property', legal: 'Legal', digital: 'Digital', contact: 'Contacts' };
const FIELD_LABELS = {
  bank_name: 'Bank Name', account_number: 'Account Number', ifsc: 'IFSC Code', branch: 'Branch', account_type: 'Account Type', balance: 'Balance',
  company: 'Company', policy_number: 'Policy Number', type: 'Type', sum_assured: 'Sum Assured', premium: 'Premium', maturity_date: 'Maturity Date', nominee: 'Nominee',
  institution: 'Institution', value: 'Value', address: 'Address', registration_number: 'Registration No.', owner: 'Owner',
  document_type: 'Document Type', location: 'Location', lawyer_name: 'Lawyer Name', lawyer_contact: 'Lawyer Contact',
  service: 'Service', username: 'Username', recovery_email: 'Recovery Email', notes: 'Notes',
  name: 'Name', relation: 'Relation', phone: 'Phone', email: 'Email', role: 'Role'
};

function SharedVaultsContent() {
  const searchParams = useSearchParams();
  const [sharedVaults, setSharedVaults] = useState([]);
  const [selectedVault, setSelectedVault] = useState(null);
  const [vaultData, setVaultData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      handleAcceptInvite(token);
    } else {
      loadSharedVaults();
    }
  }, [searchParams]);

  const handleAcceptInvite = async (token) => {
    setAccepting(true);
    try {
      await acceptVaultInvite(token);
      setMessage('Invitation accepted! You can now view the shared vault.');
      loadSharedVaults();
    } catch (e) {
      setMessage(e.message || 'Failed to accept invite');
    }
    setAccepting(false);
  };

  const loadSharedVaults = async () => {
    setLoading(true);
    const vaults = await getSharedVaults();
    setSharedVaults(vaults);
    setLoading(false);
  };

  const openVault = async (email) => {
    setSelectedVault(email);
    const data = await viewSharedVault(email);
    setVaultData(data);
  };

  const groupedEntries = vaultData?.entries?.reduce((acc, e) => {
    acc[e.category] = acc[e.category] || [];
    acc[e.category].push(e);
    return acc;
  }, {}) || {};

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-6"><Users className="w-6 h-6" /> Shared Vaults</h1>

        {message && <div className="mb-4 p-4 bg-[var(--accent)]/20 border border-[var(--accent)] rounded-lg text-sm">{message}</div>}
        {accepting && <div className="text-center py-12 text-[var(--text-muted)]">Accepting invitation...</div>}

        {!selectedVault ? (
          loading ? (
            <div className="text-center py-12 text-[var(--text-muted)]">Loading...</div>
          ) : sharedVaults.length === 0 ? (
            <div className="text-center py-12 text-[var(--text-muted)]">No vaults have been shared with you yet.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sharedVaults.map(v => (
                <button key={v.owner_email} onClick={() => openVault(v.owner_email)} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 text-left hover:border-[var(--accent)] transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-[var(--text-primary)]">{v.owner_name}</div>
                      <div className="text-sm text-[var(--text-muted)]">{v.relation || 'Family member'}</div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-[var(--text-muted)]" />
                  </div>
                </button>
              ))}
            </div>
          )
        ) : (
          <div>
            <button onClick={() => { setSelectedVault(null); setVaultData(null); }} className="mb-4 text-sm text-[var(--accent)] hover:underline">← Back to all vaults</button>
            <h2 className="text-xl font-semibold mb-4">{vaultData?.owner_name}'s Vault</h2>
            
            {Object.keys(groupedEntries).length === 0 ? (
              <div className="text-center py-12 text-[var(--text-muted)]">No entries visible to you.</div>
            ) : (
              <div className="space-y-6">
                {Object.entries(groupedEntries).map(([cat, entries]) => {
                  const Icon = CATEGORY_ICONS[cat] || Shield;
                  return (
                    <div key={cat}>
                      <h3 className="flex items-center gap-2 text-lg font-medium mb-3"><Icon className="w-5 h-5" /> {CATEGORY_LABELS[cat] || cat}</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {entries.map(entry => (
                          <div key={entry.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                            <h4 className="font-semibold text-[var(--text-primary)] mb-3">{entry.title}</h4>
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
                                    <a key={f} href={getVaultFileUrl(f)} target="_blank" className="flex items-center gap-1 text-xs bg-[var(--bg-tertiary)] rounded px-2 py-1 hover:text-[var(--accent)]">
                                      <File className="w-3 h-3" />{f.slice(0, 12)}...
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}
                            {entry.notes && <p className="mt-3 text-xs text-[var(--text-muted)] border-t border-[var(--border)] pt-2">{entry.notes}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default function SharedVaultsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><main className="p-6"><div className="text-center py-12 text-[var(--text-muted)]">Loading...</div></main></div>}>
      <SharedVaultsContent />
    </Suspense>
  );
}
