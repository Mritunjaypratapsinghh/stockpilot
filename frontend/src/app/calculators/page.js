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
  { id: 'portfolio-score', label: 'StockPilot Score', icon: Target, component: PortfolioScore },
  { id: 'cashflow', label: 'Cashflow Planner', icon: DollarSign, component: CashflowPlanner },
  { id: 'retirement', label: 'Retirement Planner', icon: Wallet, component: RetirementPlanner },
  { id: 'swp', label: 'SWP Generator', icon: Calculator, component: SWPCalculator },
  { id: 'loan', label: 'Smart Loan Analyzer', icon: CreditCard, component: LoanAnalyzer },
  { id: 'salary-tax', label: 'Salary & Tax Calculator', icon: Receipt, component: SalaryTax },
];

export default function CalculatorsPage() {
  const [active, setActive] = useState('asset-allocation');
  const ActiveComponent = calculators.find(c => c.id === active)?.component || AssetAllocation;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', margin: 0, padding: 0 }}>
      <Navbar />
      <div style={{ display: 'flex', margin: 0, padding: 0 }}>
        <aside className="calc-sidebar" style={{ width: 230, minHeight: 'calc(100vh - 60px)', background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)', padding: '24px 14px', margin: 0, transition: 'width 0.2s' }}>
          <div className="calc-sidebar-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 18px 10px', padding: 0 }}>Calculators</div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 2, margin: 0, padding: 0 }}>
            {calculators.map(calc => {
              const isActive = active === calc.id;
              return (
                <button key={calc.id} onClick={() => setActive(calc.id)} title={calc.label} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '11px 14px', margin: 0,
                  border: 'none', borderRadius: 10, cursor: 'pointer', fontSize: 14, textAlign: 'left', width: '100%',
                  background: isActive ? 'rgba(124,58,237,0.12)' : 'transparent',
                  color: isActive ? '#7C3AED' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 400,
                  borderLeft: isActive ? '3px solid #7C3AED' : '3px solid transparent',
                  transition: 'all 0.15s', justifyContent: 'flex-start',
                }}
                  onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'var(--bg-tertiary)'; }}
                  onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}>
                  <calc.icon style={{ width: 17, height: 17, flexShrink: 0 }} />
                  <span className="calc-sidebar-label">{calc.label}</span>
                  {isActive && <span className="calc-sidebar-arrow" style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>›</span>}
                </button>
              );
            })}
          </nav>
        </aside>
        <main className="calc-main" style={{ flex: 1, padding: 32, margin: 0, overflow: 'auto' }}>
          <ActiveComponent />
        </main>
      </div>
    </div>
  );
}
