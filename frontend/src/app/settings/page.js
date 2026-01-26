'use client';
import { useState, useEffect } from 'react';
import { Bell, MessageCircle, Mail, Save, Check, ExternalLink } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState({ daily_digest: false, alerts_enabled: true, email_alerts: true, hourly_alerts: false, telegram_chat_id: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [email, setEmail] = useState('');

  useEffect(() => {
    api('/api/auth/me').then(u => {
      setSettings({ daily_digest: u.settings?.daily_digest || false, alerts_enabled: u.settings?.alerts_enabled ?? true, email_alerts: u.settings?.email_alerts ?? true, hourly_alerts: u.settings?.hourly_alerts || false, telegram_chat_id: u.telegram_chat_id || '' });
      setEmail(u.email || '');
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api('/api/auth/settings', { method: 'PUT', body: JSON.stringify({ ...settings, email }) });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) { alert(e.message); }
    setSaving(false);
  };

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-6">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6 max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Settings</h1>

        <div className="space-y-6">
          {/* Telegram */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <div className="flex items-center gap-3 mb-4">
              <MessageCircle className="w-5 h-5 text-[#0088cc]" />
              <span className="font-medium">Telegram Notifications</span>
            </div>
            <p className="text-sm text-[var(--text-muted)] mb-4">Link your Telegram to receive alerts and daily digest.</p>
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-2">Chat ID</label>
                <input value={settings.telegram_chat_id} onChange={e => setSettings({...settings, telegram_chat_id: e.target.value})} placeholder="e.g. 123456789" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" />
              </div>
              <a href="https://t.me/StockPilotAlertsBot" target="_blank" className="inline-flex items-center gap-2 text-sm text-[#0088cc] hover:underline">
                <ExternalLink className="w-4 h-4" /> Open Bot & send /start to get Chat ID
              </a>
            </div>
          </div>

          {/* Email */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <div className="flex items-center gap-3 mb-4">
              <Mail className="w-5 h-5 text-[#ea4335]" />
              <span className="font-medium">Email Notifications</span>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-[var(--text-secondary)] mb-2">Email Address</label>
              <input value={email} onChange={e => setEmail(e.target.value)} type="email" placeholder="your@email.com" className="w-full px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:border-[var(--accent)]" />
            </div>
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-medium">Email Alerts</div>
                <div className="text-sm text-[var(--text-muted)]">Receive alerts and digest via email</div>
              </div>
              <input type="checkbox" checked={settings.email_alerts} onChange={e => setSettings({...settings, email_alerts: e.target.checked})} className="w-5 h-5 accent-[var(--accent)]" />
            </label>
          </div>

          {/* Alert Preferences */}
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
            <div className="flex items-center gap-3 mb-4">
              <Bell className="w-5 h-5 text-[#f59e0b]" />
              <span className="font-medium">Alert Preferences</span>
            </div>
            <div className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <div className="font-medium">Hourly Updates</div>
                  <div className="text-sm text-[var(--text-muted)]">Portfolio snapshot every hour (9 AM - 4 PM)</div>
                </div>
                <input type="checkbox" checked={settings.hourly_alerts} onChange={e => setSettings({...settings, hourly_alerts: e.target.checked})} className="w-5 h-5 accent-[var(--accent)]" />
              </label>
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <div className="font-medium">Daily Digest</div>
                  <div className="text-sm text-[var(--text-muted)]">Receive portfolio summary at 6 PM daily</div>
                </div>
                <input type="checkbox" checked={settings.daily_digest} onChange={e => setSettings({...settings, daily_digest: e.target.checked})} className="w-5 h-5 accent-[var(--accent)]" />
              </label>
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <div className="font-medium">Price Alerts</div>
                  <div className="text-sm text-[var(--text-muted)]">Get notified when stocks hit target prices</div>
                </div>
                <input type="checkbox" checked={settings.alerts_enabled} onChange={e => setSettings({...settings, alerts_enabled: e.target.checked})} className="w-5 h-5 accent-[var(--accent)]" />
              </label>
            </div>
          </div>

          <button onClick={save} disabled={saving} className="w-full flex items-center justify-center gap-2 py-3 bg-[var(--accent)] text-white rounded-lg font-medium hover:bg-[#5558e3] disabled:opacity-50">
            {saved ? <><Check className="w-5 h-5" /> Saved!</> : <><Save className="w-5 h-5" /> {saving ? 'Saving...' : 'Save Settings'}</>}
          </button>
        </div>
      </main>
    </div>
  );
}
