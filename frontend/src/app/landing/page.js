'use client';
import Link from 'next/link';
import { TrendingUp, PieChart, Bell, Calculator, Shield, Zap, BarChart3, Target, ArrowRight, Check, Star, ChevronRight } from 'lucide-react';
import PublicNavbar from '../../components/PublicNavbar';

const features = [
  { icon: PieChart, title: 'Portfolio Tracking', desc: 'Real-time portfolio value with P&L tracking across stocks and mutual funds' },
  { icon: BarChart3, title: 'Smart Analytics', desc: 'Sector allocation, XIRR returns, and performance metrics at a glance' },
  { icon: Bell, title: 'Price Alerts', desc: 'Set target prices and get notified via Telegram when stocks hit your targets' },
  { icon: Calculator, title: 'Financial Calculators', desc: 'SIP, SWP, retirement planning, loan analyzer, and tax calculators - all free' },
  { icon: Target, title: 'Goal Planning', desc: 'Map investments to goals and track progress towards financial milestones' },
  { icon: Zap, title: 'Smart Signals', desc: 'AI-powered buy/sell recommendations with detailed explanations' },
];

const calculators = [
  'Asset Allocation', 'SIP Step-up', 'StockPilot Score', 'Retirement Planner', 
  'SWP Generator', 'Loan Analyzer', 'Salary & Tax', 'Cashflow Planner'
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <PublicNavbar />

      {/* Hero */}
      <section className="px-6 py-20 max-w-6xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--accent)]/10 rounded-full text-[var(--accent)] text-sm font-medium mb-6">
          <Star className="w-4 h-4" /> Free Financial Calculators Available
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-[var(--text-primary)] mb-6 leading-tight">
          Your Personal<br />
          <span className="text-[var(--accent)]">Portfolio Intelligence</span><br />
          Platform
        </h1>
        <p className="text-xl text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto">
          Track, analyze, and optimize your stock investments with real-time data, smart insights, and powerful calculators.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link href="/login?signup=true" className="inline-flex items-center gap-2 px-8 py-4 bg-[var(--accent)] text-white rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity">
            Start Free <ArrowRight className="w-5 h-5" />
          </Link>
          <Link href="/calculators" className="inline-flex items-center gap-2 px-8 py-4 bg-[var(--bg-secondary)] text-[var(--text-primary)] rounded-xl font-semibold text-lg border border-[var(--border)] hover:bg-[var(--bg-tertiary)] transition-colors">
            Try Calculators <Calculator className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20 bg-[var(--bg-secondary)]">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-[var(--text-primary)] mb-4">Everything You Need</h2>
          <p className="text-center text-[var(--text-secondary)] mb-12 max-w-xl mx-auto">Powerful tools to manage your investments like a pro</p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div key={i} className="p-6 bg-[var(--bg-primary)] rounded-2xl border border-[var(--border)] hover:border-[var(--accent)]/50 transition-colors">
                <div className="w-12 h-12 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center mb-4">
                  <f.icon className="w-6 h-6 text-[var(--accent)]" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">{f.title}</h3>
                <p className="text-[var(--text-secondary)] text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Free Calculators */}
      <section className="px-6 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="flex-1">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-green-500/10 rounded-full text-green-500 text-sm font-medium mb-4">
                100% Free
              </div>
              <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-4">Financial Calculators</h2>
              <p className="text-[var(--text-secondary)] mb-6">
                No signup required. Use our comprehensive suite of calculators to plan your finances better.
              </p>
              <div className="grid grid-cols-2 gap-3 mb-8">
                {calculators.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                    <Check className="w-4 h-4 text-green-500" /> {c}
                  </div>
                ))}
              </div>
              <Link href="/calculators" className="inline-flex items-center gap-2 text-[var(--accent)] font-semibold hover:underline">
                Open Calculators <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="flex-1 bg-[var(--bg-secondary)] rounded-2xl p-8 border border-[var(--border)]">
              <div className="space-y-4">
                {['SIP Step-up Calculator', 'Retirement Planner', 'Loan Analyzer'].map((name, i) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-[var(--bg-primary)] rounded-xl">
                    <span className="font-medium text-[var(--text-primary)]">{name}</span>
                    <ArrowRight className="w-4 h-4 text-[var(--text-muted)]" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-20 bg-[var(--accent)]">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Take Control?</h2>
          <p className="text-white/80 mb-8">Join thousands of investors tracking their portfolios with StockPilot</p>
          <Link href="/login?signup=true" className="inline-flex items-center gap-2 px-8 py-4 bg-white text-[var(--accent)] rounded-xl font-semibold text-lg hover:bg-white/90 transition-colors">
            Create Free Account <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 bg-[var(--bg-secondary)] border-t border-[var(--border)]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-[var(--text-primary)]">StockPilot</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-[var(--text-secondary)]">
            <Link href="/calculators" className="hover:text-[var(--text-primary)]">Calculators</Link>
            <Link href="/login" className="hover:text-[var(--text-primary)]">Login</Link>
            <Link href="/login?signup=true" className="hover:text-[var(--text-primary)]">Sign Up</Link>
          </div>
          <p className="text-sm text-[var(--text-muted)]">© 2026 StockPilot. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
