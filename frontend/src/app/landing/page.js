'use client';
import Link from 'next/link';
import { TrendingUp, ArrowRight, ChevronRight, Sparkles, ArrowUpRight } from 'lucide-react';
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
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark';
    setTheme(saved);
    document.documentElement.setAttribute('data-theme', saved);
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  const isDark = theme === 'dark' || theme === 'oled';

  return (
    <div style={{ minHeight: '100vh', background: isDark ? '#0a0a0b' : '#fafafa', color: isDark ? '#fff' : '#111' }}>
      <style jsx global>{`
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-20px); } }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes glow { 0%, 100% { filter: blur(40px); } 50% { filter: blur(60px); } }
        .animate-float { animation: float 6s ease-in-out infinite; }
        .animate-pulse-slow { animation: pulse 4s ease-in-out infinite; }
        .animate-glow { animation: glow 4s ease-in-out infinite; }
        .animate-slide-up { animation: slideUp 0.8s ease-out forwards; }
        .animate-fade-in { animation: fadeIn 1s ease-out forwards; }
        .delay-100 { animation-delay: 0.1s; opacity: 0; }
        .delay-200 { animation-delay: 0.2s; opacity: 0; }
        .delay-300 { animation-delay: 0.3s; opacity: 0; }
        .delay-400 { animation-delay: 0.4s; opacity: 0; }
        .hover-lift { transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .hover-lift:hover { transform: translateY(-4px); box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
      `}</style>

      {/* Nav */}
      <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, padding: '20px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: isDark ? 'rgba(10,10,11,0.8)' : 'rgba(250,250,250,0.8)', backdropFilter: 'blur(20px)', borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}` }}>
        <Link href="/landing" style={{ display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none', color: 'inherit' }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp style={{ width: 22, height: 22, color: '#fff' }} />
          </div>
          <span style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>StockPilot</span>
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <Link href="/services" style={{ fontSize: 15, color: isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)', textDecoration: 'none', fontWeight: 500 }}>Services</Link>
          <Link href="/about" style={{ fontSize: 15, color: isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)', textDecoration: 'none', fontWeight: 500 }}>About</Link>
          <Link href="/calculators" style={{ fontSize: 15, color: isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)', textDecoration: 'none', fontWeight: 500 }}>Calculators</Link>
          <button onClick={toggleTheme} style={{ fontSize: 15, color: isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>{isDark ? '☀️ Light' : '🌙 Dark'}</button>
          <Link href="/login" style={{ fontSize: 15, color: isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)', textDecoration: 'none', fontWeight: 500 }}>Login</Link>
          <Link href="/login?signup=true" style={{ padding: '12px 24px', background: isDark ? '#fff' : '#111', color: isDark ? '#000' : '#fff', fontSize: 15, fontWeight: 600, borderRadius: 8, textDecoration: 'none' }}>Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '140px 40px 100px', position: 'relative', overflow: 'hidden' }}>
        {/* Animated background orbs - only in dark mode */}
        {isDark && mounted && (
          <>
            <div className="animate-float animate-glow" style={{ position: 'absolute', top: '15%', left: '15%', width: 300, height: 300, background: 'radial-gradient(circle, rgba(99,102,241,0.3) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none' }} />
            <div className="animate-float animate-glow" style={{ position: 'absolute', bottom: '20%', right: '10%', width: 250, height: 250, background: 'radial-gradient(circle, rgba(139,92,246,0.25) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none', animationDelay: '2s' }} />
            <div className="animate-pulse-slow" style={{ position: 'absolute', top: '40%', right: '25%', width: 150, height: 150, background: 'radial-gradient(circle, rgba(236,72,153,0.2) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none' }} />
          </>
        )}
        
        {/* Light mode subtle pattern */}
        {!isDark && (
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 50%, rgba(99,102,241,0.03) 0%, transparent 50%)', pointerEvents: 'none' }} />
        )}
        
        <div className={mounted ? 'animate-slide-up' : ''} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 20px', border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`, borderRadius: 100, marginBottom: 40, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
          <Sparkles style={{ width: 16, height: 16, color: '#8b5cf6' }} />
          <span style={{ fontSize: 14, fontWeight: 500, color: isDark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)' }}>Free calculators — no signup required</span>
        </div>

        <h1 className={mounted ? 'animate-slide-up delay-100' : ''} style={{ fontSize: 'clamp(48px, 8vw, 88px)', fontWeight: 700, lineHeight: 1.05, margin: 0, letterSpacing: '-3px', maxWidth: 900 }}>
          Wealth tracking<br />
          <span style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>for the modern investor</span>
        </h1>
        
        <p className={mounted ? 'animate-slide-up delay-200' : ''} style={{ fontSize: 20, color: isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)', maxWidth: 520, margin: '32px 0 48px', lineHeight: 1.7, fontWeight: 400 }}>
          A refined platform to monitor, analyze, and optimize your investment portfolio with precision and clarity.
        </p>

        <div className={mounted ? 'animate-slide-up delay-300' : ''} style={{ display: 'flex', gap: 16 }}>
          <Link href="/login?signup=true" className="hover-lift" style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '18px 36px', background: isDark ? '#fff' : '#111', color: isDark ? '#000' : '#fff', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>
            Start for free <ArrowRight style={{ width: 18, height: 18 }} />
          </Link>
          <Link href="/calculators" className="hover-lift" style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '18px 36px', border: `1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)'}`, background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)', color: 'inherit', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>
            Try calculators
          </Link>
        </div>

        {/* Scroll indicator */}
        {isDark && mounted && (
          <div className="animate-fade-in delay-400" style={{ position: 'absolute', bottom: 40, left: '50%', transform: 'translateX(-50%)' }}>
            <div style={{ width: 24, height: 40, border: `2px solid ${isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'}`, borderRadius: 12, display: 'flex', justifyContent: 'center', paddingTop: 8 }}>
              <div className="animate-pulse-slow" style={{ width: 4, height: 8, background: isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)', borderRadius: 2 }} />
            </div>
          </div>
        )}
      </section>

      {/* Features */}
      <section style={{ padding: '120px 40px', borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}`, background: isDark ? '#0a0a0b' : '#fff' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <p style={{ fontSize: 14, fontWeight: 600, color: '#8b5cf6', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: 16 }}>Features</p>
          <h2 style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 80px 0', maxWidth: 500 }}>Everything you need, nothing you don't</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '60px 80px' }}>
            {features.map((f, i) => (
              <div key={i} style={{ borderLeft: `2px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`, paddingLeft: 32, transition: 'border-color 0.3s' }}>
                <h3 style={{ fontSize: 24, fontWeight: 600, margin: '0 0 16px 0', letterSpacing: '-0.5px' }}>{f.title}</h3>
                <p style={{ fontSize: 16, color: isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)', lineHeight: 1.7, margin: 0 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Calculators */}
      <section style={{ padding: '120px 40px', background: isDark ? '#111' : '#f5f5f5' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center' }}>
          <div>
            <div style={{ display: 'inline-block', padding: '8px 16px', background: 'rgba(16,185,129,0.15)', borderRadius: 6, marginBottom: 24 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#10b981' }}>FREE FOREVER</span>
            </div>
            <h2 style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 24px 0' }}>Financial calculators</h2>
            <p style={{ fontSize: 18, color: isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)', lineHeight: 1.7, margin: '0 0 40px 0' }}>
              Plan your investments with our suite of professional-grade calculators. No account needed.
            </p>
            <Link href="/calculators" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 16, fontWeight: 600, color: '#8b5cf6', textDecoration: 'none' }}>
              Open calculators <ArrowUpRight style={{ width: 18, height: 18 }} />
            </Link>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {calculators.map((c, i) => (
              <Link key={i} href="/calculators" className="hover-lift" style={{ padding: '20px 24px', background: isDark ? '#0a0a0b' : '#fff', border: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`, borderRadius: 12, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 15, fontWeight: 500, color: 'inherit' }}>{c}</span>
                <ChevronRight style={{ width: 16, height: 16, color: isDark ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)' }} />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '160px 40px', textAlign: 'center', borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}`, background: isDark ? '#0a0a0b' : '#fff' }}>
        <h2 style={{ fontSize: 56, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 24px 0' }}>Ready to begin?</h2>
        <p style={{ fontSize: 20, color: isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)', margin: '0 0 48px 0' }}>Join investors who track smarter, not harder.</p>
        <Link href="/login?signup=true" className="hover-lift" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '20px 48px', background: isDark ? '#fff' : '#111', color: isDark ? '#000' : '#fff', fontSize: 17, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>
          Create free account <ArrowRight style={{ width: 20, height: 20 }} />
        </Link>
      </section>

      {/* Footer */}
      <footer style={{ padding: '40px', borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: isDark ? '#0a0a0b' : '#fafafa' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <TrendingUp style={{ width: 20, height: 20, color: '#8b5cf6' }} />
          <span style={{ fontSize: 15, fontWeight: 600 }}>StockPilot</span>
        </div>
        <div style={{ display: 'flex', gap: 40 }}>
          <Link href="/calculators" style={{ fontSize: 14, color: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Calculators</Link>
          <Link href="/services" style={{ fontSize: 14, color: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Services</Link>
          <Link href="/about" style={{ fontSize: 14, color: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>About</Link>
          <Link href="/login" style={{ fontSize: 14, color: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Login</Link>
        </div>
        <span style={{ fontSize: 13, color: isDark ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)' }}>© 2026</span>
      </footer>
    </div>
  );
}
