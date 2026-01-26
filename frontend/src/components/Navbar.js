'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Bell, Search, TrendingUp, LogOut, Briefcase, Eye, Calendar, Zap, Sun, Moon, Settings, Target, Receipt, BarChart3, Filter, RefreshCw, Scissors, ArrowRightLeft, ChevronDown } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

const mainNav = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { href: '/market', label: 'Market', icon: TrendingUp },
];

const toolsMenu = [
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/screener', label: 'Screener', icon: Filter },
  { href: '/compare', label: 'Compare', icon: ArrowRightLeft },
  { href: '/signals', label: 'Signals', icon: Zap },
  { href: '/research', label: 'Research', icon: Search },
];

const planningMenu = [
  { href: '/goals', label: 'Goals', icon: Target },
  { href: '/tax', label: 'Tax Center', icon: Receipt },
  { href: '/sip', label: 'SIP Tracker', icon: RefreshCw },
  { href: '/rebalance', label: 'Rebalance', icon: BarChart3 },
];

const trackingMenu = [
  { href: '/watchlist', label: 'Watchlist', icon: Eye },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/corporate-actions', label: 'Corp Actions', icon: Scissors },
  { href: '/ipo', label: 'IPO', icon: Calendar },
];

function Dropdown({ label, items, pathname }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const isActive = items.some(i => pathname === i.href);

  useEffect(() => {
    const handleClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-[#6366f1] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
        {label}<ChevronDown className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 py-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg shadow-lg min-w-[160px] z-50">
          {items.map(item => (
            <Link key={item.href} href={item.href} onClick={() => setOpen(false)} className={`flex items-center gap-2 px-3 py-2 text-sm ${pathname === item.href ? 'bg-[var(--bg-tertiary)] text-[#6366f1]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'}`}>
              <item.icon className="w-4 h-4" />{item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Navbar() {
  const pathname = usePathname();
  const [dark, setDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    const isDark = saved ? saved === 'dark' : true;
    setDark(isDark);
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  }, []);

  const toggleTheme = () => {
    const newTheme = !dark;
    setDark(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', newTheme ? 'dark' : 'light');
  };

  return (
    <nav className="sticky top-0 z-50 bg-[var(--bg-primary)] border-b border-[var(--border)]">
      <div className="h-14 px-6 flex items-center">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-[#6366f1] flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-[var(--text-primary)]">StockPilot</span>
        </Link>

        {/* Divider */}
        <div className="w-px h-5 bg-[var(--border-light)] ml-6 shrink-0"></div>

        {/* Nav Items */}
        <div className="flex items-center ml-6 gap-1">
          {mainNav.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-[#6366f1] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
                <item.icon className="w-4 h-4" />{item.label}
              </Link>
            );
          })}
          <Dropdown label="Tools" items={toolsMenu} pathname={pathname} />
          <Dropdown label="Planning" items={planningMenu} pathname={pathname} />
          <Dropdown label="Tracking" items={trackingMenu} pathname={pathname} />
          <Link href="/settings" className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${pathname === '/settings' ? 'bg-[#6366f1] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
            <Settings className="w-4 h-4" />Settings
          </Link>
        </div>

        {/* Spacer */}
        <div className="flex-1"></div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="flex items-center gap-1.5 px-3 py-1.5 ml-2 rounded-md text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors shrink-0 whitespace-nowrap"
        >
          {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          {dark ? 'Light' : 'Dark'}
        </button>

        {/* Logout */}
        <button
          onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }}
          className="flex items-center gap-1.5 px-3 py-1.5 ml-2 rounded-md text-sm font-medium text-[var(--text-secondary)] hover:text-[#ef4444] hover:bg-[#ef4444]/10 transition-colors shrink-0 whitespace-nowrap"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </nav>
  );
}
