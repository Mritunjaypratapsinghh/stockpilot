'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Bell, Search, TrendingUp, LogOut, Briefcase, Eye, Calendar, Zap, Sun, Moon, Settings, Target, Receipt, BarChart3 } from 'lucide-react';
import { useState, useEffect } from 'react';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/goals', label: 'Goals', icon: Target },
  { href: '/tax', label: 'Tax', icon: Receipt },
  { href: '/signals', label: 'Signals', icon: Zap },
  { href: '/watchlist', label: 'Watchlist', icon: Eye },
  { href: '/market', label: 'Market', icon: TrendingUp },
  { href: '/ipo', label: 'IPO', icon: Calendar },
  { href: '/research', label: 'Research', icon: Search },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/settings', label: 'Settings', icon: Settings },
];

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
        <div className="flex items-center ml-6 overflow-x-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-1.5 px-3 py-1.5 mr-1 rounded-md text-sm font-medium transition-colors shrink-0 whitespace-nowrap ${
                isActive 
                  ? 'bg-[#6366f1] text-white' 
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
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
