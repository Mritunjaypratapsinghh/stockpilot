'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Bell, Search, TrendingUp, LogOut, Briefcase, Eye, Calendar, Zap, Sun, Moon, Settings, Target, Receipt, BarChart3, Filter, RefreshCw, Scissors, ArrowRightLeft, ChevronDown, Wallet, CalendarDays, Activity } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

const mainNav = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { href: '/networth', label: 'Net Worth', icon: Wallet },
  { href: '/market', label: 'Market', icon: TrendingUp },
];

const toolsMenu = [
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/screener', label: 'Screener', icon: Filter },
  { href: '/compare', label: 'Compare', icon: ArrowRightLeft },
  { href: '/mf-health', label: 'MF Health', icon: Activity },
  { href: '/signals', label: 'Signals', icon: Zap },
  { href: '/research', label: 'Research', icon: Search },
];

const planningMenu = [
  { href: '/goals', label: 'Goals', icon: Target },
  { href: '/tax', label: 'Tax Center', icon: Receipt },
  { href: '/sip', label: 'SIP Tracker', icon: RefreshCw },
  { href: '/rebalance', label: 'Rebalance', icon: BarChart3 },
  { href: '/pnl', label: 'P&L Calendar', icon: CalendarDays },
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
      <button onClick={() => setOpen(!open)} className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
        {label}<ChevronDown className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 py-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg shadow-lg min-w-[160px] z-50">
          {items.map(item => (
            <Link key={item.href} href={item.href} onClick={() => setOpen(false)} className={`flex items-center gap-2 px-3 py-2 text-sm ${pathname === item.href ? 'bg-[var(--bg-tertiary)] text-[var(--accent)]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'}`}>
              <item.icon className="w-4 h-4" />{item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

const THEMES = ['dark', 'oled', 'light'];
const ACCENTS = [
  { name: 'indigo', color: '#6366f1' },
  { name: 'blue', color: '#3b82f6' },
  { name: 'green', color: '#10b981' },
  { name: 'purple', color: '#8b5cf6' },
  { name: 'pink', color: '#ec4899' },
  { name: 'orange', color: '#f97316' },
];

export default function Navbar() {
  const pathname = usePathname();
  const [theme, setTheme] = useState('dark');
  const [accent, setAccent] = useState('indigo');
  const [showThemeMenu, setShowThemeMenu] = useState(false);
  const themeRef = useRef(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const savedAccent = localStorage.getItem('accent') || 'indigo';
    setTheme(savedTheme);
    setAccent(savedAccent);
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.setAttribute('data-accent', savedAccent);
  }, []);

  useEffect(() => {
    const handleClick = (e) => { if (themeRef.current && !themeRef.current.contains(e.target)) setShowThemeMenu(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const cycleTheme = () => {
    const idx = THEMES.indexOf(theme);
    const newTheme = THEMES[(idx + 1) % THEMES.length];
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const setAccentColor = (a) => {
    setAccent(a);
    localStorage.setItem('accent', a);
    document.documentElement.setAttribute('data-accent', a);
  };

  return (
    <nav className="sticky top-0 z-50 bg-[var(--bg-primary)] border-b border-[var(--border)]">
      <div className="h-14 px-6 flex items-center">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center">
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
              <Link key={item.href} href={item.href} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
                <item.icon className="w-4 h-4" />{item.label}
              </Link>
            );
          })}
          <Dropdown label="Tools" items={toolsMenu} pathname={pathname} />
          <Dropdown label="Planning" items={planningMenu} pathname={pathname} />
          <Dropdown label="Tracking" items={trackingMenu} pathname={pathname} />
          <Link href="/settings" className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${pathname === '/settings' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
            <Settings className="w-4 h-4" />Settings
          </Link>
        </div>

        {/* Spacer */}
        <div className="flex-1"></div>

        {/* Theme Toggle */}
        <div ref={themeRef} className="relative">
          <button
            onClick={() => setShowThemeMenu(!showThemeMenu)}
            className="flex items-center gap-1.5 px-3 py-1.5 ml-2 rounded-md text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors shrink-0 whitespace-nowrap"
          >
            {theme === 'light' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {theme === 'oled' ? 'OLED' : theme === 'light' ? 'Light' : 'Dark'}
          </button>
          {showThemeMenu && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg shadow-lg p-2 z-50">
              <div className="text-xs text-[var(--text-muted)] px-2 mb-1">Theme</div>
              <div className="flex gap-1 mb-3">
                {THEMES.map(t => (
                  <button key={t} onClick={() => { setTheme(t); localStorage.setItem('theme', t); document.documentElement.setAttribute('data-theme', t); }} className={`flex-1 py-1.5 rounded text-xs font-medium ${theme === t ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'}`}>
                    {t === 'oled' ? 'OLED' : t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
              <div className="text-xs text-[var(--text-muted)] px-2 mb-1">Accent Color</div>
              <div className="flex gap-1.5 px-1">
                {ACCENTS.map(a => (
                  <button key={a.name} onClick={() => setAccentColor(a.name)} className={`w-6 h-6 rounded-full ${accent === a.name ? 'ring-2 ring-offset-2 ring-offset-[var(--bg-secondary)]' : ''}`} style={{ backgroundColor: a.color, ringColor: a.color }} />
                ))}
              </div>
            </div>
          )}
        </div>

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
