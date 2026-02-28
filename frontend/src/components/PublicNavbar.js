'use client';
import Link from 'next/link';
import { TrendingUp, Sun, Moon, LogIn, UserPlus } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function PublicNavbar() {
  const [theme, setTheme] = useState('dark');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    setIsLoggedIn(!!localStorage.getItem('token'));
  }, []);

  const cycleTheme = () => {
    const themes = ['dark', 'oled', 'light'];
    const idx = themes.indexOf(theme);
    const newTheme = themes[(idx + 1) % themes.length];
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <nav className="sticky top-0 z-50 bg-[var(--bg-primary)] border-b border-[var(--border)]">
      <div className="h-14 px-6 flex items-center">
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-[var(--text-primary)]">StockPilot</span>
        </Link>

        <div className="w-px h-5 bg-[var(--border-light)] mx-6 shrink-0"></div>

        <span className="text-sm font-medium text-[var(--text-secondary)]">Free Financial Calculators</span>

        <div className="flex-1"></div>

        <button onClick={cycleTheme} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors">
          {theme === 'light' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          {theme === 'oled' ? 'OLED' : theme === 'light' ? 'Light' : 'Dark'}
        </button>

        {isLoggedIn ? (
          <Link href="/" className="flex items-center gap-1.5 px-4 py-1.5 ml-2 rounded-md text-sm font-medium bg-[var(--accent)] text-white hover:opacity-90 transition-opacity">
            Go to Dashboard
          </Link>
        ) : (
          <>
            <Link href="/login" className="flex items-center gap-1.5 px-3 py-1.5 ml-2 rounded-md text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors">
              <LogIn className="w-4 h-4" /> Login
            </Link>
            <Link href="/login?signup=true" className="flex items-center gap-1.5 px-4 py-1.5 ml-2 rounded-md text-sm font-medium bg-[var(--accent)] text-white hover:opacity-90 transition-opacity">
              <UserPlus className="w-4 h-4" /> Sign Up Free
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
