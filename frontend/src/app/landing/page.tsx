'use client';
import Link from 'next/link';
import { ArrowRight, Sparkles, PieChart, BarChart3, Bell, Calculator, Target, Zap, Check, ChevronRight, Shield } from 'lucide-react';
import PublicLayout from '../../components/PublicLayout';

const features = [
  { icon: PieChart, title: 'Portfolio Tracking', desc: 'Real-time P&L, XIRR, and sector allocation across stocks and mutual funds' },
  { icon: BarChart3, title: 'Smart Analytics', desc: 'Performance benchmarking, concentration risk, and historical trends' },
  { icon: Bell, title: 'Price Alerts', desc: 'Instant Telegram notifications on price targets and corporate actions' },
  { icon: Calculator, title: 'Free Calculators', desc: 'SIP, retirement, loan, tax — 8+ calculators, no signup required' },
  { icon: Target, title: 'Goal Planning', desc: 'Map investments to life goals and track progress automatically' },
  { icon: Zap, title: 'AI Signals', desc: 'Buy/sell recommendations with confidence scores and risk assessment' },
];

const calcLinks = [
  { name: 'SIP Step-up', id: 'sip-stepup' },
  { name: 'Asset Allocation', id: 'asset-allocation' },
  { name: 'Retirement Planner', id: 'retirement' },
  { name: 'Loan Analyzer', id: 'loan' },
  { name: 'Salary & Tax', id: 'salary-tax' },
  { name: 'SWP Generator', id: 'swp' },
];

export default function LandingPage() {
  return (
    <PublicLayout>
      {/* Hero */}
      <section className="pub-hero" style={{ position: 'relative' }}>
        <div className="pub-hero-bg" aria-hidden="true" />
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 20px', border: '1px solid var(--border)', borderRadius: 100, marginBottom: 40, background: 'var(--bg-secondary)' }}>
          <Sparkles style={{ width: 16, height: 16, color: 'var(--accent)' }} />
          <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)' }}>Free calculators — no signup required</span>
        </div>

        <h1 className="pub-h1">
          Wealth tracking<br />
          <span style={{ color: 'var(--accent)' }}>for the modern investor</span>
        </h1>

        <p className="pub-subtitle" style={{ margin: '0 auto 48px' }}>
          A refined platform to monitor, analyze, and optimize your investment portfolio with precision and clarity.
        </p>

        <div className="pub-btn-row" style={{ justifyContent: 'center' }}>
          <Link href="/login?signup=true" className="pub-btn-dark">Start for free <ArrowRight style={{ width: 18, height: 18 }} /></Link>
          <Link href="/calculators" className="pub-btn-outline">Try calculators</Link>
        </div>

        {/* Trust bar */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 48, marginTop: 64, flexWrap: 'wrap' }}>
          {[{ v: '8+', l: 'Free Calculators' }, { v: '₹0', l: 'Forever Free Tier' }, { v: '100%', l: 'Privacy Focused' }].map((s, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--text-primary)' }}>{s.v}</div>
              <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>{s.l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Product Preview */}
      <div className="pub-section-alt">
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 16, padding: 20, overflow: 'hidden' }}>
            {/* Mock dashboard */}
            <div style={{ background: 'var(--bg-tertiary)', borderRadius: 12, padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Top bar */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: 8 }}><div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ef4444' }} /><div style={{ width: 12, height: 12, borderRadius: '50%', background: '#f59e0b' }} /><div style={{ width: 12, height: 12, borderRadius: '50%', background: '#10b981' }} /></div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>StockPilot Dashboard</div>
                <div style={{ width: 60 }} />
              </div>
              {/* Mock content */}
              <div className="pub-mock-stats" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                {[{ l: 'Portfolio Value', v: '₹12,45,800', c: 'var(--text-primary)' }, { l: 'Today\'s P&L', v: '+₹8,420', c: 'var(--green)' }, { l: 'Total Returns', v: '+18.4%', c: 'var(--green)' }, { l: 'XIRR', v: '22.1%', c: 'var(--accent)' }].map((s, i) => (
                  <div key={i} style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: 16, border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{s.l}</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: s.c }}>{s.v}</div>
                  </div>
                ))}
              </div>
              {/* Mock chart area */}
              <div className="pub-mock-charts" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: 20, border: '1px solid var(--border)', height: 180 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 16 }}>Portfolio Growth</div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 120 }}>
                    {[35, 42, 38, 55, 48, 62, 58, 72, 68, 78, 85, 92].map((h, i) => (
                      <div key={i} style={{ flex: 1, background: `var(--accent)`, borderRadius: 3, height: `${h}%`, opacity: 0.3 + (i / 15) }} />
                    ))}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: 20, border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 16 }}>Allocation</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {[{ n: 'Large Cap', p: 45, c: 'var(--accent)' }, { n: 'Mid Cap', p: 25, c: '#8b5cf6' }, { n: 'Small Cap', p: 15, c: '#ec4899' }, { n: 'Debt', p: 15, c: '#f59e0b' }].map((s, i) => (
                      <div key={i}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}><span>{s.n}</span><span>{s.p}%</span></div>
                        <div style={{ height: 4, background: 'var(--bg-tertiary)', borderRadius: 2 }}><div style={{ height: '100%', width: `${s.p}%`, background: s.c, borderRadius: 2 }} /></div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <section className="pub-section">
        <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: 16 }}>Features</p>
        <h2 className="pub-h2" style={{ maxWidth: 500 }}>Everything you need, nothing you don't</h2>
        <div className="pub-grid-3" style={{ marginTop: 48 }}>
          {features.map((f, i) => (
            <div key={i} className="pub-card">
              <f.icon style={{ width: 28, height: 28, color: 'var(--accent)', marginBottom: 16 }} />
              <h3 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 10px 0' }}>{f.title}</h3>
              <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Calculators */}
      <div className="pub-section-alt">
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div className="pub-grid-2" style={{ gap: 64, alignItems: 'center' }}>
            <div>
              <div style={{ display: 'inline-block', padding: '6px 14px', background: 'var(--green-bg)', borderRadius: 6, marginBottom: 20 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--green)' }}>FREE FOREVER</span>
              </div>
              <h2 className="pub-h2">Financial calculators</h2>
              <p style={{ fontSize: 18, color: 'var(--text-secondary)', lineHeight: 1.7, margin: '0 0 32px 0' }}>
                Professional-grade calculators for every financial decision. No account needed.
              </p>
              <Link href="/calculators" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 16, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none' }}>
                Open calculators <ChevronRight style={{ width: 18, height: 18 }} />
              </Link>
            </div>
            <div className="pub-grid-2" style={{ gap: 12 }}>
              {calcLinks.map((c, i) => (
                <Link key={i} href={`/calculators?tab=${c.id}`} className="pub-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px' }}>
                  <span style={{ fontSize: 15, fontWeight: 500 }}>{c.name}</span>
                  <ChevronRight style={{ width: 16, height: 16, color: 'var(--text-muted)' }} />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Trust */}
      <section className="pub-section" style={{ textAlign: 'center' }}>
        <Shield style={{ width: 32, height: 32, color: 'var(--accent)', marginBottom: 16 }} />
        <h2 className="pub-h2">Built with trust in mind</h2>
        <div className="pub-grid-3" style={{ marginTop: 48, textAlign: 'left' }}>
          {[
            { t: 'Your data stays yours', d: 'We never sell or share your portfolio data. Your financial information is encrypted and private.' },
            { t: 'Verified calculations', d: 'Every calculator is tested against official standards — RBI guidelines, Income Tax Act, and CAGR formulas.' },
            { t: 'No hidden charges', d: 'All calculators are free forever. Portfolio features have a generous free tier with no credit card required.' },
          ].map((v, i) => (
            <div key={i} style={{ borderTop: '2px solid var(--accent)', paddingTop: 20 }}>
              <h3 style={{ fontSize: 18, fontWeight: 600, margin: '0 0 10px 0' }}>{v.t}</h3>
              <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>{v.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="pub-section-alt" style={{ textAlign: 'center', padding: '120px 24px' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 className="pub-h2">Ready to begin?</h2>
          <p className="pub-subtitle" style={{ margin: '0 auto 40px' }}>Join investors who track smarter, not harder.</p>
          <div className="pub-btn-row" style={{ justifyContent: 'center' }}>
            <Link href="/login?signup=true" className="pub-btn-dark">Create free account <ArrowRight style={{ width: 18, height: 18 }} /></Link>
            <Link href="/calculators" className="pub-btn-outline">Try calculators</Link>
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
