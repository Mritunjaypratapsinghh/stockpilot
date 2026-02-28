'use client';
import Link from 'next/link';
import { TrendingUp, ArrowRight, PieChart, BarChart3, Bell, Calculator, Target, Zap, Shield, LineChart, Wallet, FileText, Check } from 'lucide-react';
import { useState, useEffect } from 'react';

const services = [
  { icon: PieChart, title: 'Portfolio Tracking', desc: 'Real-time tracking of stocks and mutual funds with automatic price updates, P&L calculation, and XIRR returns.', features: ['Live price updates', 'Multi-broker import (Zerodha, Groww)', 'Automatic cost basis calculation', 'Stocks & Mutual Funds support'] },
  { icon: BarChart3, title: 'Analytics & Research', desc: 'Deep-dive into your portfolio performance with sector analysis, concentration risk, and historical trends.', features: ['Sector allocation breakdown', 'Concentration risk alerts', 'Performance benchmarking', 'Company financials & ratios'] },
  { icon: Bell, title: 'Smart Alerts', desc: 'Never miss a move. Get instant notifications on price targets, volume spikes, and corporate actions.', features: ['Price target alerts', 'Telegram notifications', 'Daily portfolio digest', 'Hourly market updates'] },
  { icon: Calculator, title: 'Financial Calculators', desc: 'Professional-grade calculators for every financial decision. Free for everyone, no signup required.', features: ['SIP & SWP calculators', 'Retirement planner', 'Loan analyzer', 'Salary & tax calculator'], free: true },
  { icon: Target, title: 'Goal-Based Planning', desc: 'Map your investments to life goals — retirement, house, education — and track progress automatically.', features: ['Custom goal creation', 'Auto-progress tracking', 'SIP recommendations', 'Timeline projections'] },
  { icon: Zap, title: 'AI Signals', desc: 'AI-powered buy/sell signals with detailed reasoning, confidence scores, and risk assessment.', features: ['Technical analysis signals', 'Fundamental screening', 'Risk-adjusted scoring', 'Detailed explanations'] },
];

export default function ServicesPage() {
  const [theme, setTheme] = useState('dark');
  useEffect(() => { const s = localStorage.getItem('theme') || 'dark'; setTheme(s); document.documentElement.setAttribute('data-theme', s); }, []);
  const toggleTheme = () => { const n = theme === 'dark' ? 'light' : 'dark'; setTheme(n); localStorage.setItem('theme', n); document.documentElement.setAttribute('data-theme', n); };
  const dk = theme === 'dark' || theme === 'oled';
  const muted = dk ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)';
  const border = dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.08)';
  const bg = dk ? '#0a0a0b' : '#fafafa';
  const bg2 = dk ? '#111' : '#fff';

  return (
    <div style={{ minHeight: '100vh', background: bg, color: dk ? '#fff' : '#111' }}>
      {/* Nav */}
      <nav style={{ position: 'sticky', top: 0, zIndex: 100, padding: '20px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: dk ? 'rgba(10,10,11,0.8)' : 'rgba(250,250,250,0.8)', backdropFilter: 'blur(20px)', borderBottom: `1px solid ${border}` }}>
        <Link href="/landing" style={{ display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none', color: 'inherit' }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><TrendingUp style={{ width: 22, height: 22, color: '#fff' }} /></div>
          <span style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>StockPilot</span>
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <Link href="/services" style={{ fontSize: 15, fontWeight: 600, color: '#8b5cf6', textDecoration: 'none' }}>Services</Link>
          <Link href="/about" style={{ fontSize: 15, fontWeight: 500, color: muted, textDecoration: 'none' }}>About</Link>
          <Link href="/calculators" style={{ fontSize: 15, fontWeight: 500, color: muted, textDecoration: 'none' }}>Calculators</Link>
          <button onClick={toggleTheme} style={{ fontSize: 15, color: muted, background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>{dk ? '☀️' : '🌙'}</button>
          <Link href="/login" style={{ fontSize: 15, color: muted, textDecoration: 'none', fontWeight: 500 }}>Login</Link>
          <Link href="/login?signup=true" style={{ padding: '12px 24px', background: dk ? '#fff' : '#111', color: dk ? '#000' : '#fff', fontSize: 15, fontWeight: 600, borderRadius: 8, textDecoration: 'none' }}>Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ padding: '120px 40px 80px', textAlign: 'center' }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#8b5cf6', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: 16 }}>Our Services</p>
        <h1 style={{ fontSize: 56, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 24px 0' }}>Tools built for serious investors</h1>
        <p style={{ fontSize: 20, color: muted, maxWidth: 600, margin: '0 auto', lineHeight: 1.7 }}>From portfolio tracking to AI-powered signals — everything you need to make informed investment decisions.</p>
      </section>

      {/* Services Grid */}
      <section style={{ padding: '40px 40px 120px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 24 }}>
          {services.map((s, i) => (
            <div key={i} style={{ padding: 40, background: bg2, border: `1px solid ${border}`, borderRadius: 20, position: 'relative', overflow: 'hidden' }}>
              {s.free && <div style={{ position: 'absolute', top: 20, right: 20, padding: '6px 12px', background: 'rgba(16,185,129,0.15)', borderRadius: 6 }}><span style={{ fontSize: 12, fontWeight: 700, color: '#10b981' }}>FREE</span></div>}
              <s.icon style={{ width: 32, height: 32, color: '#8b5cf6', marginBottom: 20 }} />
              <h3 style={{ fontSize: 24, fontWeight: 600, margin: '0 0 12px 0', letterSpacing: '-0.5px' }}>{s.title}</h3>
              <p style={{ fontSize: 16, color: muted, lineHeight: 1.7, margin: '0 0 24px 0' }}>{s.desc}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {s.features.map((f, j) => (
                  <div key={j} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Check style={{ width: 16, height: 16, color: '#10b981', flexShrink: 0 }} />
                    <span style={{ fontSize: 14, color: muted }}>{f}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '120px 40px', textAlign: 'center', borderTop: `1px solid ${border}`, background: bg }}>
        <h2 style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 24px 0' }}>Start tracking today</h2>
        <p style={{ fontSize: 20, color: muted, margin: '0 0 40px 0' }}>Free to use. No credit card required.</p>
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
          <Link href="/login?signup=true" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '18px 36px', background: dk ? '#fff' : '#111', color: dk ? '#000' : '#fff', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>Create free account <ArrowRight style={{ width: 18, height: 18 }} /></Link>
          <Link href="/calculators" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '18px 36px', border: `1px solid ${border}`, color: 'inherit', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>Try calculators</Link>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: '40px', borderTop: `1px solid ${border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><TrendingUp style={{ width: 20, height: 20, color: '#8b5cf6' }} /><span style={{ fontSize: 15, fontWeight: 600 }}>StockPilot</span></div>
        <div style={{ display: 'flex', gap: 40 }}>
          <Link href="/landing" style={{ fontSize: 14, color: dk ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Home</Link>
          <Link href="/about" style={{ fontSize: 14, color: dk ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>About</Link>
          <Link href="/calculators" style={{ fontSize: 14, color: dk ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Calculators</Link>
        </div>
        <span style={{ fontSize: 13, color: dk ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)' }}>© 2026</span>
      </footer>
    </div>
  );
}
