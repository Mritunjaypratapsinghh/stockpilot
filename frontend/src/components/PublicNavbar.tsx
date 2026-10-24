// @ts-nocheck
'use client';
import Link from 'next/link';
import { Sun, Moon, LogIn, UserPlus } from 'lucide-react';
import { useState, useEffect } from 'react';

function CompassLogo() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="23" fill="#1e1b16"/>
      <circle cx="24" cy="24" r="18" fill="#0c0b09"/>
      <rect x="21.5" y="1.5" width="5" height="5" rx="2.5" fill="#b8892a"/>
      <rect x="21.5" y="41.5" width="5" height="5" rx="2.5" fill="#5a5448"/>
      <rect x="1.5" y="21.5" width="5" height="5" rx="2.5" fill="#5a5448"/>
      <rect x="41.5" y="21.5" width="5" height="5" rx="2.5" fill="#5a5448"/>
      <path d="M24 7 C26.5 12 27.8 17.5 27 21.5 C26.4 23.5 25.3 24 24 24 C22.7 24 21.6 23.5 21 21.5 C20.2 17.5 21.5 12 24 7 Z" fill="#b8892a"/>
      <path d="M24 41 C26.5 36 27.8 30.5 27 26.5 C26.4 24.5 25.3 24 24 24 C22.7 24 21.6 24.5 21 26.5 C20.2 30.5 21.5 36 24 41 Z" fill="#2a2620"/>
      <circle cx="24" cy="24" r="2.8" fill="#b8892a"/>
      <circle cx="24" cy="24" r="1.2" fill="#0c0b09"/>
    </svg>
  );
}

export default function PublicNavbar() {
  const [theme, setTheme] = useState('dark');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/auth/me', { credentials: 'include' })
      .then(r => setIsLoggedIn(r.ok)).catch(() => setIsLoggedIn(false));
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
          <CompassLogo />
          <span className="font-semibold text-[var(--text-primary)]">
            <span className="font-normal">Stock</span><span className="text-[var(--accent)]">Pilot</span>
          </span>
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
