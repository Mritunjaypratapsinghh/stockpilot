'use client';
import Link from 'next/link';
import { TrendingUp, PieChart, Bell, Calculator, Zap, BarChart3, Target, ArrowRight, Check, ChevronRight, Sparkles, Shield, LineChart, Wallet } from 'lucide-react';
import { useState, useEffect } from 'react';

const features = [
  { icon: PieChart, title: 'Portfolio Tracking', desc: 'Real-time portfolio value with P&L tracking across stocks and mutual funds', color: '#6366f1' },
  { icon: BarChart3, title: 'Smart Analytics', desc: 'Sector allocation, XIRR returns, and performance metrics at a glance', color: '#10b981' },
  { icon: Bell, title: 'Price Alerts', desc: 'Set target prices and get notified via Telegram when stocks hit your targets', color: '#f59e0b' },
  { icon: Calculator, title: 'Financial Calculators', desc: 'SIP, SWP, retirement planning, loan analyzer, and tax calculators - all free', color: '#8b5cf6' },
  { icon: Target, title: 'Goal Planning', desc: 'Map investments to goals and track progress towards financial milestones', color: '#ec4899' },
  { icon: Zap, title: 'Smart Signals', desc: 'AI-powered buy/sell recommendations with detailed explanations', color: '#06b6d4' },
];

const calculators = [
  { name: 'Asset Allocation', desc: 'Optimize your portfolio mix' },
  { name: 'SIP Step-up', desc: 'Plan increasing SIP investments' },
  { name: 'Retirement Planner', desc: 'Calculate your retirement corpus' },
  { name: 'Loan Analyzer', desc: 'Compare prepayment strategies' },
];

const stats = [
  { value: '8+', label: 'Free Calculators' },
  { value: '₹0', label: 'Forever Free Tier' },
  { value: '100%', label: 'Privacy Focused' },
];

export default function LandingPage() {
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark';
    setTheme(saved);
    document.documentElement.setAttribute('data-theme', saved);
  }, []);

  const cycleTheme = () => {
    const themes = ['dark', 'light', 'oled'];
    const next = themes[(themes.indexOf(theme) + 1) % 3];
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Navbar */}
      <nav style={{ position: 'sticky', top: 0, zIndex: 50, background: 'var(--bg-primary)', borderBottom: '1px solid var(--border)', backdropFilter: 'blur(12px)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link href="/landing" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp style={{ width: 20, height: 20, color: '#fff' }} />
            </div>
            <span style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>StockPilot</span>
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Link href="/calculators" style={{ padding: '8px 16px', fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)', textDecoration: 'none', borderRadius: 8, transition: 'all 0.15s' }}>Calculators</Link>
            <button onClick={cycleTheme} style={{ padding: '8px 12px', fontSize: 13, fontWeight: 500, color: 'var(--text-muted)', background: 'var(--bg-tertiary)', border: 'none', borderRadius: 8, cursor: 'pointer' }}>
              {theme === 'dark' ? '🌙' : theme === 'light' ? '☀️' : '🖤'}
            </button>
            <Link href="/login" style={{ padding: '8px 16px', fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)', textDecoration: 'none' }}>Login</Link>
            <Link href="/login?signup=true" style={{ padding: '10px 20px', fontSize: 14, fontWeight: 600, color: '#fff', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 10, textDecoration: 'none' }}>Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: -200, right: -200, width: 600, height: 600, background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -100, left: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%)', pointerEvents: 'none' }} />
        
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 24px 100px', textAlign: 'center', position: 'relative' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: 'linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1))', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 50, marginBottom: 24 }}>
            <Sparkles style={{ width: 16, height: 16, color: '#8b5cf6' }} />
            <span style={{ fontSize: 14, fontWeight: 500, color: '#8b5cf6' }}>Free Financial Calculators • No Signup Required</span>
          </div>
          
          <h1 style={{ fontSize: 'clamp(40px, 6vw, 72px)', fontWeight: 800, lineHeight: 1.1, margin: '0 0 24px 0', color: 'var(--text-primary)' }}>
            Track Your Wealth<br />
            <span style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Like a Pro</span>
          </h1>
          
          <p style={{ fontSize: 20, color: 'var(--text-secondary)', maxWidth: 600, margin: '0 auto 40px', lineHeight: 1.6 }}>
            The all-in-one platform to track, analyze, and grow your investment portfolio with powerful tools and real-time insights.
          </p>
          
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 60 }}>
            <Link href="/login?signup=true" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '16px 32px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff', fontSize: 16, fontWeight: 600, borderRadius: 12, textDecoration: 'none', boxShadow: '0 4px 20px rgba(99,102,241,0.4)' }}>
              Start Free <ArrowRight style={{ width: 18, height: 18 }} />
            </Link>
            <Link href="/calculators" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '16px 32px', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: 16, fontWeight: 600, borderRadius: 12, textDecoration: 'none', border: '1px solid var(--border)' }}>
              <Calculator style={{ width: 18, height: 18 }} /> Try Calculators
            </Link>
          </div>

          {/* Stats */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 48, flexWrap: 'wrap' }}>
            {stats.map((s, i) => (
              <div key={i} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--text-primary)' }}>{s.value}</div>
                <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ background: 'var(--bg-secondary)', padding: '100px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 60 }}>
            <h2 style={{ fontSize: 40, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 16px 0' }}>Everything You Need</h2>
            <p style={{ fontSize: 18, color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto' }}>Powerful tools to manage your investments like a pro</p>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
            {features.map((f, i) => (
              <div key={i} style={{ padding: 32, background: 'var(--bg-primary)', borderRadius: 20, border: '1px solid var(--border)', transition: 'all 0.2s' }}>
                <div style={{ width: 56, height: 56, borderRadius: 16, background: `${f.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
                  <f.icon style={{ width: 28, height: 28, color: f.color }} />
                </div>
                <h3 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 12px 0' }}>{f.title}</h3>
                <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Calculators */}
      <section style={{ padding: '100px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center' }}>
            <div>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px', background: '#10b98120', borderRadius: 20, marginBottom: 20 }}>
                <Check style={{ width: 14, height: 14, color: '#10b981' }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#10b981' }}>100% FREE</span>
              </div>
              <h2 style={{ fontSize: 40, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 20px 0' }}>Financial Calculators</h2>
              <p style={{ fontSize: 17, color: 'var(--text-secondary)', lineHeight: 1.7, margin: '0 0 32px 0' }}>
                No signup required. Use our comprehensive suite of calculators to plan your finances better. From SIP planning to retirement corpus calculation.
              </p>
              <Link href="/calculators" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 16, fontWeight: 600, color: '#6366f1', textDecoration: 'none' }}>
                Open Calculators <ChevronRight style={{ width: 20, height: 20 }} />
              </Link>
            </div>
            
            <div style={{ background: 'var(--bg-secondary)', borderRadius: 24, padding: 8, border: '1px solid var(--border)' }}>
              {calculators.map((c, i) => (
                <Link key={i} href="/calculators" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 20, background: i === 0 ? 'var(--bg-primary)' : 'transparent', borderRadius: 16, textDecoration: 'none', marginBottom: i < 3 ? 4 : 0 }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{c.name}</div>
                    <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{c.desc}</div>
                  </div>
                  <ChevronRight style={{ width: 20, height: 20, color: 'var(--text-muted)' }} />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '100px 24px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
        <div style={{ maxWidth: 700, margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: 40, fontWeight: 700, color: '#fff', margin: '0 0 20px 0' }}>Ready to Take Control?</h2>
          <p style={{ fontSize: 18, color: 'rgba(255,255,255,0.8)', margin: '0 0 40px 0' }}>Join thousands of investors tracking their portfolios with StockPilot</p>
          <Link href="/login?signup=true" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '18px 40px', background: '#fff', color: '#6366f1', fontSize: 17, fontWeight: 700, borderRadius: 14, textDecoration: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
            Create Free Account <ArrowRight style={{ width: 20, height: 20 }} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: '60px 24px', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp style={{ width: 16, height: 16, color: '#fff' }} />
            </div>
            <span style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>StockPilot</span>
          </div>
          <div style={{ display: 'flex', gap: 32 }}>
            <Link href="/calculators" style={{ fontSize: 14, color: 'var(--text-secondary)', textDecoration: 'none' }}>Calculators</Link>
            <Link href="/login" style={{ fontSize: 14, color: 'var(--text-secondary)', textDecoration: 'none' }}>Login</Link>
            <Link href="/login?signup=true" style={{ fontSize: 14, color: 'var(--text-secondary)', textDecoration: 'none' }}>Sign Up</Link>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>© 2026 StockPilot</p>
        </div>
      </footer>
    </div>
  );
}
