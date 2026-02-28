'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { TrendingUp, Menu, X } from 'lucide-react';
import { useState, useEffect } from 'react';

const navLinks = [
  { href: '/services', label: 'Services' },
  { href: '/about', label: 'About' },
  { href: '/calculators', label: 'Calculators' },
];

export default function PublicLayout({ children }) {
  const pathname = usePathname();
  const [theme, setTheme] = useState('dark');
  const [menuOpen, setMenuOpen] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    const s = localStorage.getItem('theme') || 'dark';
    setTheme(s);
    document.documentElement.setAttribute('data-theme', s);
    setLoggedIn(!!localStorage.getItem('token'));
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
      <nav className="pub-nav">
        <div className="pub-nav-inner">
          <Link href="/landing" className="pub-logo">
            <div className="pub-logo-icon"><TrendingUp style={{ width: 20, height: 20, color: '#fff' }} /></div>
            <span className="pub-logo-text">StockPilot</span>
          </Link>

          {/* Desktop links */}
          <div className="pub-nav-links">
            {navLinks.map(l => (
              <Link key={l.href} href={l.href} className={`pub-nav-link ${pathname === l.href ? 'active' : ''}`}>{l.label}</Link>
            ))}
            <button onClick={toggleTheme} className="pub-nav-link" style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit' }}>{theme === 'dark' ? '☀️' : '🌙'}</button>
            {loggedIn ? (
              <Link href="/" className="pub-btn-primary">Dashboard</Link>
            ) : (
              <>
                <Link href="/login" className="pub-nav-link">Login</Link>
                <Link href="/login?signup=true" className="pub-btn-primary">Get Started</Link>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <button className="pub-hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
            {menuOpen ? <X style={{ width: 24, height: 24 }} /> : <Menu style={{ width: 24, height: 24 }} />}
          </button>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="pub-mobile-menu">
            {navLinks.map(l => (
              <Link key={l.href} href={l.href} onClick={() => setMenuOpen(false)} className={`pub-mobile-link ${pathname === l.href ? 'active' : ''}`}>{l.label}</Link>
            ))}
            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '8px 0' }} />
            {loggedIn ? (
              <Link href="/" onClick={() => setMenuOpen(false)} className="pub-mobile-link">Dashboard</Link>
            ) : (
              <>
                <Link href="/login" onClick={() => setMenuOpen(false)} className="pub-mobile-link">Login</Link>
                <Link href="/login?signup=true" onClick={() => setMenuOpen(false)} className="pub-btn-primary" style={{ textAlign: 'center', display: 'block' }}>Get Started</Link>
              </>
            )}
          </div>
        )}
      </nav>

      {/* Content */}
      <main>{children}</main>

      {/* Footer */}
      <footer className="pub-footer">
        <div className="pub-footer-inner">
          <div className="pub-footer-grid">
            {/* Brand */}
            <div className="pub-footer-brand">
              <Link href="/landing" className="pub-logo" style={{ marginBottom: 12 }}>
                <div className="pub-logo-icon"><TrendingUp style={{ width: 16, height: 16, color: '#fff' }} /></div>
                <span style={{ fontSize: 16, fontWeight: 600 }}>StockPilot</span>
              </Link>
              <p style={{ fontSize: 14, color: 'var(--text-muted)', lineHeight: 1.6, margin: 0 }}>Portfolio intelligence platform for the modern Indian investor.</p>
            </div>

            {/* Product */}
            <div>
              <h4 className="pub-footer-heading">Product</h4>
              <Link href="/calculators" className="pub-footer-link">Calculators</Link>
              <Link href="/services" className="pub-footer-link">Services</Link>
              <Link href="/login?signup=true" className="pub-footer-link">Sign Up</Link>
            </div>

            {/* Company */}
            <div>
              <h4 className="pub-footer-heading">Company</h4>
              <Link href="/about" className="pub-footer-link">About Us</Link>
              <a href="mailto:support@stockpilot.in" className="pub-footer-link">Contact</a>
            </div>

            {/* Legal */}
            <div>
              <h4 className="pub-footer-heading">Legal</h4>
              <span className="pub-footer-link" style={{ cursor: 'default' }}>Privacy Policy</span>
              <span className="pub-footer-link" style={{ cursor: 'default' }}>Terms of Service</span>
            </div>
          </div>

          <div className="pub-footer-bottom">
            <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>© 2026 StockPilot. All rights reserved.</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0, maxWidth: 500 }}>StockPilot is not a SEBI-registered investment advisor. All tools are for informational purposes only. Please consult a qualified financial advisor before making investment decisions.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
