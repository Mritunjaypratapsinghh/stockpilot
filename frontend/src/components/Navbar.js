'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Bell, Search, TrendingUp, LogOut, Briefcase, Eye, EyeOff, Calendar, Zap, Sun, Moon, Settings, Target, Receipt, BarChart3, Filter, RefreshCw, Scissors, ArrowRightLeft, ChevronDown, Wallet, CalendarDays, Activity, HandCoins, Calculator, Shield, Menu, X, MessageSquare } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

const mainNav = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { href: '/networth', label: 'Net Worth', icon: Wallet },
  { href: '/market', label: 'Market', icon: TrendingUp },
  { href: '/chat', label: 'AI Chat', icon: MessageSquare },
  { href: '/calculators', label: 'Calculators', icon: Calculator },
];

const toolsMenu = [
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/simulator', label: 'Simulator', icon: ArrowRightLeft },
  { href: '/screener', label: 'Screener', icon: Filter },
  { href: '/compare', label: 'Compare', icon: ArrowRightLeft },
  { href: '/mf-health', label: 'MF Health', icon: Activity },
  { href: '/mf-overlap', label: 'MF Overlap', icon: Activity },
  { href: '/signals', label: 'Signals', icon: Zap },
  { href: '/research', label: 'Research', icon: Search },
];

const planningMenu = [
  { href: '/goals', label: 'Goals', icon: Target },
  { href: '/tax', label: 'Tax Center', icon: Receipt },
  { href: '/itr', label: 'ITR Filing', icon: Shield },
  { href: '/sip', label: 'SIP Tracker', icon: RefreshCw },
  { href: '/rebalance', label: 'Rebalance', icon: BarChart3 },
  { href: '/pnl', label: 'P&L Calendar', icon: CalendarDays },
];

const trackingMenu = [
  { href: '/watchlist', label: 'Watchlist', icon: Eye },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/ledger', label: 'Ledger', icon: HandCoins },
  { href: '/vault', label: 'Vault', icon: Shield },
  { href: '/corporate-actions', label: 'Corp Actions', icon: Scissors },
  { href: '/ipo', label: 'IPO', icon: Calendar },
];

function Dropdown({ label, items, pathname, mobile, onNavigate }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const isActive = items.some(i => pathname === i.href);

  useEffect(() => {
    const handleClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  if (mobile) {
    return (
      <div className="border-b border-[var(--border)] pb-2 mb-2">
        <div className="text-xs text-[var(--text-muted)] px-3 py-1">{label}</div>
        {items.map(item => (
          <Link key={item.href} href={item.href} onClick={onNavigate} className={`flex items-center gap-3 px-3 py-2.5 text-sm ${pathname === item.href ? 'text-[var(--accent)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-secondary)]'}`}>
            <item.icon className="w-5 h-5" />{item.label}
          </Link>
        ))}
      </div>
    );
  }

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
  const [mobileOpen, setMobileOpen] = useState(false);
  const [privacyMode, setPrivacyMode] = useState(false);
  const themeRef = useRef(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const savedAccent = localStorage.getItem('accent') || 'indigo';
    const savedPrivacy = localStorage.getItem('privacyMode') === 'true';
    setTheme(savedTheme);
    setAccent(savedAccent);
    setPrivacyMode(savedPrivacy);
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.setAttribute('data-accent', savedAccent);
    if (savedPrivacy) document.documentElement.setAttribute('data-privacy', 'true');
  }, []);

  useEffect(() => {
    const handleClick = (e) => { if (themeRef.current && !themeRef.current.contains(e.target)) setShowThemeMenu(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  useEffect(() => { setMobileOpen(false); }, [pathname]);

  const setAccentColor = (a) => {
    setAccent(a);
    localStorage.setItem('accent', a);
    document.documentElement.setAttribute('data-accent', a);
  };

  const togglePrivacy = () => {
    const next = !privacyMode;
    setPrivacyMode(next);
    localStorage.setItem('privacyMode', next);
    if (next) document.documentElement.setAttribute('data-privacy', 'true');
    else document.documentElement.removeAttribute('data-privacy');
  };

  return (
    <>
      <nav className="sticky top-0 z-50 bg-[var(--bg-primary)] border-b border-[var(--border)]">
        <div className="h-14 px-4 md:px-6 flex items-center">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-[var(--text-primary)] hidden sm:block">StockPilot</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden lg:flex items-center ml-4 gap-0.5 min-w-0">
            <div className="w-px h-5 bg-[var(--border-light)] mr-3 shrink-0"></div>
            {mainNav.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href} className={`flex items-center gap-1.5 px-2 xl:px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${isActive ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
                  <item.icon className="w-4 h-4" /><span className="hidden xl:inline">{item.label}</span>
                </Link>
              );
            })}
            <Dropdown label="Tools" items={toolsMenu} pathname={pathname} />
            <Dropdown label="Planning" items={planningMenu} pathname={pathname} />
            <Dropdown label="Tracking" items={trackingMenu} pathname={pathname} />
            <Link href="/settings" className={`flex items-center gap-1.5 px-2 xl:px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${pathname === '/settings' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}>
              <Settings className="w-4 h-4" /><span className="hidden xl:inline">Settings</span>
            </Link>
          </div>

          <div className="flex-1"></div>

          {/* Privacy Toggle - Desktop */}
          <button onClick={togglePrivacy} className={`hidden lg:flex p-2 rounded-md transition-colors shrink-0 ${privacyMode ? 'text-[var(--accent)] bg-[var(--accent)]/10' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`} title={privacyMode ? 'Show values' : 'Hide values'}>
            {privacyMode ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>

          {/* Theme Toggle - Desktop */}
          <div ref={themeRef} className="relative hidden lg:block shrink-0">
            <button onClick={() => setShowThemeMenu(!showThemeMenu)} className="p-2 rounded-md text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors">
              {theme === 'light' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
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

          {/* Logout - Desktop */}
          <button onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }} className="hidden lg:flex items-center p-2 rounded-md text-[var(--text-secondary)] hover:text-[#ef4444] hover:bg-[#ef4444]/10 transition-colors shrink-0" title="Logout">
            <LogOut className="w-4 h-4" />
          </button>

          {/* Mobile Menu Button */}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="lg:hidden p-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]">
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 top-14 z-40 bg-[var(--bg-primary)] overflow-y-auto">
          <div className="p-2">
            {/* Main Nav */}
            <div className="border-b border-[var(--border)] pb-2 mb-2">
              {mainNav.map(item => (
                <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} className={`flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg ${pathname === item.href ? 'text-[var(--accent)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-secondary)]'}`}>
                  <item.icon className="w-5 h-5" />{item.label}
                </Link>
              ))}
            </div>

            <Dropdown label="Tools" items={toolsMenu} pathname={pathname} mobile onNavigate={() => setMobileOpen(false)} />
            <Dropdown label="Planning" items={planningMenu} pathname={pathname} mobile onNavigate={() => setMobileOpen(false)} />
            <Dropdown label="Tracking" items={trackingMenu} pathname={pathname} mobile onNavigate={() => setMobileOpen(false)} />

            {/* Settings */}
            <Link href="/settings" onClick={() => setMobileOpen(false)} className={`flex items-center gap-3 px-3 py-2.5 text-sm ${pathname === '/settings' ? 'text-[var(--accent)]' : 'text-[var(--text-secondary)]'}`}>
              <Settings className="w-5 h-5" />Settings
            </Link>

            {/* Theme */}
            <div className="border-t border-[var(--border)] mt-2 pt-3 px-3">
              <div className="text-xs text-[var(--text-muted)] mb-2">Theme</div>
              <div className="flex gap-2 mb-3">
                {THEMES.map(t => (
                  <button key={t} onClick={() => { setTheme(t); localStorage.setItem('theme', t); document.documentElement.setAttribute('data-theme', t); }} className={`flex-1 py-2 rounded-lg text-sm font-medium ${theme === t ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}`}>
                    {t === 'oled' ? 'OLED' : t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
              <div className="text-xs text-[var(--text-muted)] mb-2">Accent</div>
              <div className="flex gap-2">
                {ACCENTS.map(a => (
                  <button key={a.name} onClick={() => setAccentColor(a.name)} className={`w-8 h-8 rounded-full ${accent === a.name ? 'ring-2 ring-offset-2 ring-offset-[var(--bg-primary)]' : ''}`} style={{ backgroundColor: a.color }} />
                ))}
              </div>
            </div>

            {/* Logout */}
            <button onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }} className="flex items-center gap-3 px-3 py-3 mt-4 text-sm text-[#ef4444] border-t border-[var(--border)] w-full">
              <LogOut className="w-5 h-5" />Logout
            </button>
          </div>
        </div>
      )}
    </>
  );
}
