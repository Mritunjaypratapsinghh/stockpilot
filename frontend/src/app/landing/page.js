'use client';
import Link from 'next/link';
import { TrendingUp, ArrowRight, Check, ChevronRight, Sparkles, ArrowUpRight } from 'lucide-react';
import { useState, useEffect } from 'react';

const features = [
  { title: 'Portfolio Analytics', desc: 'Track holdings, P&L, XIRR returns, and sector allocation in real-time' },
  { title: 'Smart Alerts', desc: 'Price targets, volume spikes, and corporate actions delivered to Telegram' },
  { title: 'Goal Tracking', desc: 'Map investments to life goals and monitor progress automatically' },
  { title: 'Tax Optimization', desc: 'Harvest losses, track dividends, and generate tax reports effortlessly' },
];

const calculators = ['SIP Step-up', 'Asset Allocation', 'Retirement Planner', 'Loan Analyzer', 'Salary & Tax', 'SWP Generator'];

export default function LandingPage() {
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark';
    setTheme(saved);
    document.documentElement.setAttribute('data-theme', saved);
  }, []);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Nav */}
      <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, padding: '20px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(var(--bg-primary-rgb), 0.8)', backdropFilter: 'blur(20px)' }}>
        <Link href="/landing" style={{ display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none', color: 'var(--text-primary)' }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp style={{ width: 22, height: 22, color: '#fff' }} />
          </div>
          <span style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>StockPilot</span>
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <Link href="/calculators" style={{ fontSize: 15, color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 500 }}>Calculators</Link>
          <button onClick={toggleTheme} style={{ fontSize: 15, color: 'var(--text-secondary)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>{theme === 'dark' ? 'Light' : 'Dark'}</button>
          <Link href="/login" style={{ fontSize: 15, color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 500 }}>Login</Link>
          <Link href="/login?signup=true" style={{ padding: '12px 24px', background: 'var(--text-primary)', color: 'var(--bg-primary)', fontSize: 15, fontWeight: 600, borderRadius: 8, textDecoration: 'none' }}>Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '140px 40px 100px', position: 'relative' }}>
        <div style={{ position: 'absolute', top: '20%', left: '10%', width: 400, height: 400, background: 'radial-gradient(circle, var(--accent) 0%, transparent 70%)', opacity: 0.03, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: '20%', right: '10%', width: 300, height: 300, background: 'radial-gradient(circle, var(--accent) 0%, transparent 70%)', opacity: 0.05, pointerEvents: 'none' }} />
        
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 20px', border: '1px solid var(--border)', borderRadius: 100, marginBottom: 40 }}>
          <Sparkles style={{ width: 16, height: 16, color: 'var(--accent)' }} />
          <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)' }}>Free calculators available — no signup required</span>
        </div>

        <h1 style={{ fontSize: 'clamp(48px, 8vw, 88px)', fontWeight: 700, lineHeight: 1.05, margin: 0, letterSpacing: '-3px', maxWidth: 900 }}>
          Wealth tracking<br />for the modern investor
        </h1>
        
        <p style={{ fontSize: 20, color: 'var(--text-secondary)', maxWidth: 520, margin: '32px 0 48px', lineHeight: 1.7, fontWeight: 400 }}>
          A refined platform to monitor, analyze, and optimize your investment portfolio with precision and clarity.
        </p>

        <div style={{ display: 'flex', gap: 16 }}>
          <Link href="/login?signup=true" style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '18px 36px', background: 'var(--text-primary)', color: 'var(--bg-primary)', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>
            Start for free <ArrowRight style={{ width: 18, height: 18 }} />
          </Link>
          <Link href="/calculators" style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '18px 36px', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>
            Try calculators
          </Link>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: '120px 40px', borderTop: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: 16 }}>Features</p>
          <h2 style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 80px 0', maxWidth: 500 }}>Everything you need, nothing you don't</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '60px 80px' }}>
            {features.map((f, i) => (
              <div key={i} style={{ borderLeft: '1px solid var(--border)', paddingLeft: 32 }}>
                <h3 style={{ fontSize: 24, fontWeight: 600, margin: '0 0 16px 0', letterSpacing: '-0.5px' }}>{f.title}</h3>
                <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Calculators */}
      <section style={{ padding: '120px 40px', background: 'var(--bg-secondary)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center' }}>
          <div>
            <div style={{ display: 'inline-block', padding: '8px 16px', background: 'rgba(16,185,129,0.1)', borderRadius: 6, marginBottom: 24 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#10b981' }}>FREE FOREVER</span>
            </div>
            <h2 style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 24px 0' }}>Financial calculators</h2>
            <p style={{ fontSize: 18, color: 'var(--text-secondary)', lineHeight: 1.7, margin: '0 0 40px 0' }}>
              Plan your investments with our suite of professional-grade calculators. No account needed.
            </p>
            <Link href="/calculators" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 16, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none' }}>
              Open calculators <ArrowUpRight style={{ width: 18, height: 18 }} />
            </Link>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {calculators.map((c, i) => (
              <Link key={i} href="/calculators" style={{ padding: '20px 24px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 12, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)' }}>{c}</span>
                <ChevronRight style={{ width: 16, height: 16, color: 'var(--text-muted)' }} />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '160px 40px', textAlign: 'center', borderTop: '1px solid var(--border)' }}>
        <h2 style={{ fontSize: 56, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 24px 0' }}>Ready to begin?</h2>
        <p style={{ fontSize: 20, color: 'var(--text-secondary)', margin: '0 0 48px 0' }}>Join investors who track smarter, not harder.</p>
        <Link href="/login?signup=true" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '20px 48px', background: 'var(--text-primary)', color: 'var(--bg-primary)', fontSize: 17, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>
          Create free account <ArrowRight style={{ width: 20, height: 20 }} />
        </Link>
      </section>

      {/* Footer */}
      <footer style={{ padding: '40px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <TrendingUp style={{ width: 20, height: 20, color: 'var(--accent)' }} />
          <span style={{ fontSize: 15, fontWeight: 600 }}>StockPilot</span>
        </div>
        <div style={{ display: 'flex', gap: 40 }}>
          <Link href="/calculators" style={{ fontSize: 14, color: 'var(--text-muted)', textDecoration: 'none' }}>Calculators</Link>
          <Link href="/login" style={{ fontSize: 14, color: 'var(--text-muted)', textDecoration: 'none' }}>Login</Link>
        </div>
        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>© 2026</span>
      </footer>
    </div>
  );
}
