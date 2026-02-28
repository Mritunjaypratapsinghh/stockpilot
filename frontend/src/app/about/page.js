'use client';
import Link from 'next/link';
import { TrendingUp, ArrowRight, Github, Linkedin, Mail } from 'lucide-react';
import { useState, useEffect } from 'react';

const values = [
  { title: 'Transparency', desc: 'No hidden fees, no selling your data. Your portfolio information stays yours.' },
  { title: 'Simplicity', desc: 'Powerful tools that are intuitive to use. No learning curve, no clutter.' },
  { title: 'Accuracy', desc: 'Every calculation verified against official standards. Every data point sourced reliably.' },
];

const stack = ['Next.js 14', 'FastAPI', 'MongoDB', 'Recharts', 'Tailwind CSS', 'Telegram Bot API'];

export default function AboutPage() {
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
          <Link href="/services" style={{ fontSize: 15, fontWeight: 500, color: muted, textDecoration: 'none' }}>Services</Link>
          <Link href="/about" style={{ fontSize: 15, fontWeight: 600, color: '#8b5cf6', textDecoration: 'none' }}>About</Link>
          <Link href="/calculators" style={{ fontSize: 15, fontWeight: 500, color: muted, textDecoration: 'none' }}>Calculators</Link>
          <button onClick={toggleTheme} style={{ fontSize: 15, color: muted, background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>{dk ? '☀️' : '🌙'}</button>
          <Link href="/login" style={{ fontSize: 15, color: muted, textDecoration: 'none', fontWeight: 500 }}>Login</Link>
          <Link href="/login?signup=true" style={{ padding: '12px 24px', background: dk ? '#fff' : '#111', color: dk ? '#000' : '#fff', fontSize: 15, fontWeight: 600, borderRadius: 8, textDecoration: 'none' }}>Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ padding: '120px 40px 80px', maxWidth: 800, margin: '0 auto' }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#8b5cf6', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: 16 }}>About</p>
        <h1 style={{ fontSize: 56, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 32px 0', lineHeight: 1.1 }}>Built for the modern Indian investor</h1>
        <p style={{ fontSize: 20, color: muted, lineHeight: 1.8, margin: 0 }}>
          StockPilot was founded with a clear vision — to give every investor access to institutional-grade portfolio analytics. We combine real-time market data, intelligent automation, and clean design to help you make better investment decisions.
        </p>
      </section>

      {/* Mission */}
      <section style={{ padding: '80px 40px', borderTop: `1px solid ${border}`, background: bg2 }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h2 style={{ fontSize: 40, fontWeight: 700, letterSpacing: '-1.5px', margin: '0 0 24px 0' }}>Our mission</h2>
          <p style={{ fontSize: 20, color: muted, lineHeight: 1.8, margin: 0 }}>
            To democratize portfolio analytics. Whether you manage ₹10,000 or ₹10 crore, you deserve professional-grade tools to track and grow your wealth. We believe financial clarity is the foundation of smart investing.
          </p>
        </div>
      </section>

      {/* Values */}
      <section style={{ padding: '100px 40px', borderTop: `1px solid ${border}` }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <h2 style={{ fontSize: 40, fontWeight: 700, letterSpacing: '-1.5px', margin: '0 0 60px 0' }}>What we stand for</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 40 }}>
            {values.map((v, i) => (
              <div key={i} style={{ borderTop: '2px solid #8b5cf6', paddingTop: 24 }}>
                <h3 style={{ fontSize: 22, fontWeight: 600, margin: '0 0 12px 0' }}>{v.title}</h3>
                <p style={{ fontSize: 16, color: muted, lineHeight: 1.7, margin: 0 }}>{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section style={{ padding: '100px 40px', background: bg2, borderTop: `1px solid ${border}` }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h2 style={{ fontSize: 40, fontWeight: 700, letterSpacing: '-1.5px', margin: '0 0 16px 0' }}>Built with</h2>
          <p style={{ fontSize: 18, color: muted, margin: '0 0 40px 0' }}>Modern, reliable, open-source technologies.</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            {stack.map((s, i) => (
              <span key={i} style={{ padding: '12px 24px', background: bg, border: `1px solid ${border}`, borderRadius: 8, fontSize: 15, fontWeight: 500 }}>{s}</span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '120px 40px', textAlign: 'center', borderTop: `1px solid ${border}` }}>
        <h2 style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', margin: '0 0 24px 0' }}>Want to contribute?</h2>
        <p style={{ fontSize: 20, color: muted, margin: '0 0 40px 0', maxWidth: 500, marginLeft: 'auto', marginRight: 'auto' }}>StockPilot is open to feedback and collaboration. Reach out or start using it today.</p>
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
          <Link href="/login?signup=true" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '18px 36px', background: dk ? '#fff' : '#111', color: dk ? '#000' : '#fff', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>Get started <ArrowRight style={{ width: 18, height: 18 }} /></Link>
          <Link href="/calculators" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '18px 36px', border: `1px solid ${border}`, color: 'inherit', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }}>Try calculators</Link>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: '40px', borderTop: `1px solid ${border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><TrendingUp style={{ width: 20, height: 20, color: '#8b5cf6' }} /><span style={{ fontSize: 15, fontWeight: 600 }}>StockPilot</span></div>
        <div style={{ display: 'flex', gap: 40 }}>
          <Link href="/landing" style={{ fontSize: 14, color: dk ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Home</Link>
          <Link href="/services" style={{ fontSize: 14, color: dk ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Services</Link>
          <Link href="/calculators" style={{ fontSize: 14, color: dk ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', textDecoration: 'none' }}>Calculators</Link>
        </div>
        <span style={{ fontSize: 13, color: dk ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)' }}>© 2026</span>
      </footer>
    </div>
  );
}
