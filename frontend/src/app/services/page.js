'use client';
import Link from 'next/link';
import { ArrowRight, Check, PieChart, BarChart3, Bell, Calculator, Target, Zap } from 'lucide-react';
import PublicLayout from '../../components/PublicLayout';

const services = [
  { icon: PieChart, title: 'Portfolio Tracking', desc: 'Real-time tracking of stocks and mutual funds with automatic price updates and P&L calculation.', features: ['Live price updates', 'Multi-broker import (Zerodha, Groww)', 'Automatic cost basis', 'Stocks & Mutual Funds'] },
  { icon: BarChart3, title: 'Analytics & Research', desc: 'Deep-dive into portfolio performance with sector analysis and historical trends.', features: ['Sector allocation', 'Concentration risk alerts', 'Performance benchmarking', 'Company financials'] },
  { icon: Bell, title: 'Smart Alerts', desc: 'Instant notifications on price targets, volume spikes, and corporate actions.', features: ['Price target alerts', 'Telegram notifications', 'Daily portfolio digest', 'Hourly market updates'] },
  { icon: Calculator, title: 'Financial Calculators', desc: 'Professional-grade calculators for every financial decision.', features: ['SIP & SWP calculators', 'Retirement planner', 'Loan analyzer', 'Salary & tax calculator'], free: true },
  { icon: Target, title: 'Goal-Based Planning', desc: 'Map investments to life goals and track progress automatically.', features: ['Custom goal creation', 'Auto-progress tracking', 'SIP recommendations', 'Timeline projections'] },
  { icon: Zap, title: 'AI Signals', desc: 'AI-powered buy/sell signals with detailed reasoning and risk assessment.', features: ['Technical analysis', 'Fundamental screening', 'Risk-adjusted scoring', 'Detailed explanations'] },
];

export default function ServicesPage() {
  return (
    <PublicLayout>
      {/* Hero */}
      <section className="pub-hero">
        <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: 16 }}>Our Services</p>
        <h1 className="pub-h1" style={{ fontSize: 'clamp(36px, 5vw, 56px)' }}>Tools built for serious investors</h1>
        <p className="pub-subtitle" style={{ margin: '0 auto' }}>From portfolio tracking to AI-powered signals — everything you need to make informed investment decisions.</p>
      </section>

      {/* Pricing overview */}
      <div className="pub-section-alt">
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div className="pub-grid-2" style={{ maxWidth: 700, margin: '0 auto', gap: 20 }}>
            <div className="pub-card" style={{ textAlign: 'center', background: 'var(--bg-primary)' }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--green)', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 8px 0' }}>Free</p>
              <p style={{ fontSize: 36, fontWeight: 700, margin: '0 0 8px 0' }}>₹0</p>
              <p style={{ fontSize: 14, color: 'var(--text-muted)', margin: '0 0 20px 0' }}>Forever</p>
              <div style={{ textAlign: 'left', display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['All 8+ calculators', 'Portfolio tracking (up to 25 holdings)', 'Basic alerts'].map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-secondary)' }}><Check style={{ width: 16, height: 16, color: 'var(--green)', flexShrink: 0 }} />{f}</div>
                ))}
              </div>
              <Link href="/login?signup=true" className="pub-btn-outline" style={{ marginTop: 24, width: '100%', justifyContent: 'center', padding: '12px 24px', fontSize: 14 }}>Get started</Link>
            </div>
            <div className="pub-card" style={{ textAlign: 'center', border: '2px solid var(--accent)', background: 'var(--bg-primary)' }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 8px 0' }}>Pro</p>
              <p style={{ fontSize: 36, fontWeight: 700, margin: '0 0 8px 0' }}>₹199<span style={{ fontSize: 16, fontWeight: 400, color: 'var(--text-muted)' }}>/mo</span></p>
              <p style={{ fontSize: 14, color: 'var(--text-muted)', margin: '0 0 20px 0' }}>Coming soon</p>
              <div style={{ textAlign: 'left', display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['Everything in Free', 'Unlimited holdings', 'AI signals & smart alerts', 'Telegram bot integration', 'Export reports (CSV/PDF)'].map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-secondary)' }}><Check style={{ width: 16, height: 16, color: 'var(--accent)', flexShrink: 0 }} />{f}</div>
                ))}
              </div>
              <div className="pub-btn-dark" style={{ marginTop: 24, width: '100%', justifyContent: 'center', padding: '12px 24px', fontSize: 14, opacity: 0.6, cursor: 'default' }}>Coming soon</div>
            </div>
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <section className="pub-section">
        <h2 className="pub-h2">What's included</h2>
        <div className="pub-grid-2" style={{ marginTop: 48 }}>
          {services.map((s, i) => (
            <div key={i} className="pub-card" style={{ position: 'relative' }}>
              {s.free && <div style={{ position: 'absolute', top: 20, right: 20, padding: '4px 10px', background: 'var(--green-bg)', borderRadius: 6 }}><span style={{ fontSize: 12, fontWeight: 700, color: 'var(--green)' }}>FREE</span></div>}
              <s.icon style={{ width: 28, height: 28, color: 'var(--accent)', marginBottom: 16 }} />
              <h3 style={{ fontSize: 22, fontWeight: 600, margin: '0 0 10px 0' }}>{s.title}</h3>
              <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 20px 0' }}>{s.desc}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {s.features.map((f, j) => (
                  <div key={j} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-muted)' }}>
                    <Check style={{ width: 14, height: 14, color: 'var(--green)', flexShrink: 0 }} />{f}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="pub-section-alt" style={{ textAlign: 'center', padding: '100px 24px' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 className="pub-h2">Start tracking today</h2>
          <p className="pub-subtitle" style={{ margin: '0 auto 40px' }}>Free to use. No credit card required.</p>
          <div className="pub-btn-row" style={{ justifyContent: 'center' }}>
            <Link href="/login?signup=true" className="pub-btn-dark">Create free account <ArrowRight style={{ width: 18, height: 18 }} /></Link>
            <Link href="/calculators" className="pub-btn-outline">Try calculators</Link>
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
