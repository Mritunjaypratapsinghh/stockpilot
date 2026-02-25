'use client';
import { useState } from 'react';
import Navbar from '../../components/Navbar';
import { PieChart, TrendingUp, Target, Wallet, CreditCard, Receipt, DollarSign, Calculator } from 'lucide-react';
import AssetAllocation from './AssetAllocation';
import SIPStepup from './SIPStepup';
import PortfolioScore from './PortfolioScore';
import RetirementPlanner from './RetirementPlanner';
import SWPCalculator from './SWPCalculator';
import LoanAnalyzer from './LoanAnalyzer';
import SalaryTax from './SalaryTax';
import CashflowPlanner from './CashflowPlanner';

const calculators = [
  { id: 'asset-allocation', label: 'Asset Allocation', icon: PieChart, component: AssetAllocation },
  { id: 'sip-stepup', label: 'SIP Step-up', icon: TrendingUp, component: SIPStepup },
  { id: 'portfolio-score', label: 'Portfolio Score', icon: Target, component: PortfolioScore },
  { id: 'cashflow', label: 'Cashflow Planner', icon: DollarSign, component: CashflowPlanner },
  { id: 'retirement', label: 'Retirement Planner', icon: Wallet, component: RetirementPlanner },
  { id: 'swp', label: 'SWP Generator', icon: Calculator, component: SWPCalculator },
  { id: 'loan', label: 'Smart Loan Analyzer', icon: CreditCard, component: LoanAnalyzer },
  { id: 'salary-tax', label: 'Salary & Tax', icon: Receipt, component: SalaryTax },
];

const styles = {
  container: { minHeight: '100vh', background: 'var(--bg-primary)', margin: 0, padding: 0 },
  wrapper: { display: 'flex', margin: 0, padding: 0 },
  sidebar: { width: 220, minHeight: 'calc(100vh - 60px)', background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)', padding: '20px 12px', margin: 0 },
  sidebarTitle: { fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 16px 8px', padding: 0 },
  nav: { display: 'flex', flexDirection: 'column', gap: 2, margin: 0, padding: 0 },
  navBtn: { display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', margin: 0, border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 13, textAlign: 'left', width: '100%', transition: 'all 0.15s' },
  navBtnActive: { background: 'var(--accent)', color: '#fff', fontWeight: 500 },
  navBtnInactive: { background: 'transparent', color: 'var(--text-secondary)', fontWeight: 400 },
  icon: { width: 16, height: 16, flexShrink: 0, margin: 0, padding: 0 },
  main: { flex: 1, padding: 24, margin: 0, overflow: 'auto' },
};

export default function CalculatorsPage() {
  const [active, setActive] = useState('asset-allocation');
  const ActiveComponent = calculators.find(c => c.id === active)?.component || AssetAllocation;

  return (
    <div style={styles.container}>
      <Navbar />
      <div style={styles.wrapper}>
        <aside style={styles.sidebar}>
          <div style={styles.sidebarTitle}>Calculators</div>
          <nav style={styles.nav}>
            {calculators.map(calc => (
              <button
                key={calc.id}
                onClick={() => setActive(calc.id)}
                style={{ ...styles.navBtn, ...(active === calc.id ? styles.navBtnActive : styles.navBtnInactive) }}
                onMouseEnter={e => { if (active !== calc.id) e.target.style.background = 'var(--bg-tertiary)'; }}
                onMouseLeave={e => { if (active !== calc.id) e.target.style.background = 'transparent'; }}
              >
                <calc.icon style={styles.icon} />
                {calc.label}
              </button>
            ))}
          </nav>
        </aside>
        <main style={styles.main}>
          <ActiveComponent />
        </main>
      </div>
    </div>
  );
}
