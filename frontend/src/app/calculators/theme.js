import { useState, useEffect } from 'react';

export function useCompact(bp = 1100) {
  const [compact, setCompact] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${bp}px)`);
    setCompact(mq.matches);
    const h = e => setCompact(e.matches);
    mq.addEventListener('change', h);
    return () => mq.removeEventListener('change', h);
  }, [bp]);
  return compact;
}

// Design tokens using CSS variables for theme adaptation
export const C = {
  bg: 'var(--bg-primary)',
  card: 'var(--bg-secondary)',
  cardAlt: 'var(--bg-tertiary)',
  border: 'var(--border)',
  borderLight: 'var(--border-light)',
  accent: '#7C3AED',
  accentLight: 'rgba(124,58,237,0.12)',
  accentMid: 'rgba(124,58,237,0.2)',
  green: 'var(--green)',
  greenBg: 'var(--green-bg)',
  red: 'var(--red)',
  redBg: 'var(--red-bg)',
  cyan: '#06b6d4',
  orange: '#f59e0b',
  text: 'var(--text-primary)',
  textSec: 'var(--text-secondary)',
  textMuted: 'var(--text-muted)',
  blueGrad: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
  greenGrad: 'linear-gradient(135deg, #10b981, #059669)',
  shadow: '0 2px 8px rgba(0,0,0,0.08)',
};

export const card = {
  background: C.card, borderRadius: 16, padding: 32, margin: 0,
  border: `1px solid ${C.border}`,
};

export const grid2 = (compact) => ({ display: 'grid', gridTemplateColumns: compact ? '1fr' : '1fr 1fr', gap: compact ? 18 : 28, margin: 0, padding: 0 });

export const label = { fontSize: 14, color: C.textSec, margin: '0 0 6px 0', padding: 0, display: 'block', fontWeight: 400 };

export const val = { fontSize: 14, fontWeight: 600, color: C.accent, margin: 0, padding: 0 };

export const input = {
  width: '100%', padding: '14px 18px', margin: 0,
  background: C.cardAlt, border: `1.5px solid ${C.border}`, borderRadius: 10,
  fontSize: 16, color: C.text, outline: 'none',
};

export const slider = {
  width: '100%', height: 5, margin: '10px 0 4px', padding: 0,
  accentColor: C.accent, cursor: 'pointer',
};

export const sliderLabels = { display: 'flex', justifyContent: 'space-between', fontSize: 12, color: C.textMuted, margin: 0, padding: 0 };

export const row = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 6px 0', padding: 0 };

export const section = { margin: '0 0 24px 0', padding: 0 };

export const title = { fontSize: 18, fontWeight: 600, color: C.text, margin: '0 0 24px 0', padding: 0 };

export const statCard = {
  background: C.cardAlt, borderRadius: 12, padding: 16, margin: 0, border: `1px solid ${C.border}`,
};

export const statLabel = { fontSize: 12, color: C.textMuted, margin: '0 0 4px 0', padding: 0, textTransform: 'uppercase', letterSpacing: '0.02em' };

export const statVal = { fontSize: 22, fontWeight: 700, margin: 0, padding: 0, color: C.text };

export const gridHalf = (compact) => ({ display: 'grid', gridTemplateColumns: compact ? '1fr' : '1fr 1fr', gap: compact ? 10 : 14, margin: 0, padding: 0 });

export const footer = {
  display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: C.textMuted,
  margin: '24px 0 0 0', padding: '18px 0 0 0', borderTop: `1px solid ${C.border}`,
};

export const footerIcon = {
  width: 22, height: 22, borderRadius: '50%', background: C.accentLight,
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  fontSize: 12, color: C.accent, flexShrink: 0,
};

export const fmt = n => n?.toLocaleString('en-IN') || '0';

export const sCard = { background: C.card, borderRadius: 16, padding: 24, margin: 0, border: `1px solid ${C.border}`, boxShadow: '0 1px 3px rgba(0,0,0,0.04)' };

export const pill = { fontSize: 12, fontWeight: 700, color: C.textMuted, background: C.cardAlt, padding: '4px 8px', borderRadius: 4 };

export const togBtn = (active) => ({
  flex: 1, padding: '10px 8px', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700,
  cursor: 'pointer', background: active ? C.accent : 'transparent', color: active ? '#fff' : C.textMuted,
  transition: 'all 0.15s', margin: 0, boxShadow: active ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
});

export const inputBox = (w = 128) => ({ width: w, paddingLeft: 24, paddingRight: 8, paddingTop: 4, paddingBottom: 4, background: C.cardAlt, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 14, fontWeight: 700, textAlign: 'right', color: C.text, outline: 'none', margin: 0 });

export const suffixBox = (w = 96) => ({ width: w, paddingLeft: 12, paddingRight: 24, paddingTop: 4, paddingBottom: 4, background: C.cardAlt, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 14, fontWeight: 700, textAlign: 'right', color: C.text, outline: 'none', margin: 0 });

/** Shared hook: calls API with loading/error tracking */
export function useCalc(url) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true); setError(null);
    fetch(`/api/v1/calculators/${url}`).then(r => r.json()).then(d => { setResult(d.data || d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [url]);
  return { result, error, loading };
}

/** Tiny inline error/loading banner */
export function CalcStatus({ loading, error }) {
  if (error) return <div style={{ padding: 12, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, color: '#ef4444', fontSize: 13, margin: '0 0 16px 0' }}>⚠ Failed to load: {error}</div>;
  if (loading) return <div style={{ padding: 12, background: C.cardAlt, borderRadius: 8, color: C.textMuted, fontSize: 13, margin: '0 0 16px 0', textAlign: 'center' }}>Loading…</div>;
  return null;
}

export const fmtCr = n => {
  if (!n) return '₹0';
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  return `₹${fmt(n)}`;
};
