'use client';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import PublicLayout from '../../components/PublicLayout';

const values = [
  { title: 'Transparency', desc: 'No hidden fees, no selling your data. Your portfolio information stays yours.' },
  { title: 'Simplicity', desc: 'Powerful tools that are intuitive to use. No learning curve, no clutter.' },
  { title: 'Accuracy', desc: 'Every calculation verified against official standards — RBI guidelines, Income Tax Act, CAGR formulas.' },
];

export default function AboutPage() {
  return (
    <PublicLayout>
      {/* Hero */}
      <section className="pub-hero" style={{ textAlign: 'left', maxWidth: 800, margin: '0 auto', padding: '120px 24px 80px', position: 'relative' }}>
        <div className="pub-hero-bg" aria-hidden="true" />
        <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: 16 }}>About</p>
        <h1 className="pub-h1" style={{ fontSize: 'clamp(36px, 5vw, 56px)' }}>Built for the modern Indian investor</h1>
        <p style={{ fontSize: 20, color: 'var(--text-secondary)', lineHeight: 1.8, margin: '24px 0 0 0', maxWidth: 700 }}>
          StockPilot was founded with a clear vision — to give every investor access to institutional-grade portfolio analytics. We combine real-time market data, intelligent automation, and clean design to help you make better investment decisions.
        </p>
      </section>

      {/* Mission */}
      <div className="pub-section-alt">
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h2 className="pub-h2">Our mission</h2>
          <p style={{ fontSize: 20, color: 'var(--text-secondary)', lineHeight: 1.8, margin: 0 }}>
            To democratize portfolio analytics. Whether you manage ₹10,000 or ₹10 crore, you deserve professional-grade tools to track and grow your wealth. We believe financial clarity is the foundation of smart investing.
          </p>
        </div>
      </div>

      {/* Values */}
      <section className="pub-section">
        <h2 className="pub-h2">What we stand for</h2>
        <div className="pub-grid-3" style={{ marginTop: 48 }}>
          {values.map((v, i) => (
            <div key={i} className="pub-fade-in" style={{ borderTop: '2px solid var(--accent)', paddingTop: 20, animationDelay: `${i * 0.15}s` }}>
              <h3 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 10px 0' }}>{v.title}</h3>
              <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>{v.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Team credibility */}
      <div className="pub-section-alt">
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <h2 className="pub-h2">Our approach</h2>
          <div className="pub-grid-2" style={{ marginTop: 32, gap: 48 }}>
            <div>
              <h3 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 12px 0' }}>Engineering-first</h3>
              <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                StockPilot is built by a team of engineers and finance professionals who understand both technology and markets. Every feature is designed with reliability and performance in mind.
              </p>
            </div>
            <div>
              <h3 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 12px 0' }}>Data integrity</h3>
              <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                We source market data from trusted providers and verify all calculations against official standards. Our calculators are tested against RBI guidelines, Income Tax Act provisions, and standard financial formulas.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="pub-section-alt" style={{ textAlign: 'center', padding: '100px 24px' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 className="pub-h2">Want to get started?</h2>
          <p className="pub-subtitle" style={{ margin: '0 auto 40px' }}>Try our free calculators or create an account to track your portfolio.</p>
          <div className="pub-btn-row" style={{ justifyContent: 'center' }}>
            <Link href="/login?signup=true" className="pub-btn-dark">Get started <ArrowRight style={{ width: 18, height: 18 }} /></Link>
            <Link href="/calculators" className="pub-btn-outline">Try calculators</Link>
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
