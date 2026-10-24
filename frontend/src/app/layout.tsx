// @ts-nocheck
import './globals.css';
import ChatWidgetWrapper from '../components/ChatWidgetWrapper';
import { ErrorBoundary } from '../components/ErrorBoundary';
import Providers from '../components/Providers';

// viewport-fit=cover + interactive-widget=resizes-content are the two mobile baseline configs:
// cover: lets page paint under notch/Dynamic Island so we can use env(safe-area-inset-*)
// interactive-widget: keyboard shrinks layout on Android Chrome (matches iOS behavior)
export const viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  interactiveWidget: 'resizes-content',
};

export const metadata = {
  title: 'StockPilot — AI-Powered Portfolio Intelligence for Indian Investors',
  description: 'Track stocks & mutual funds, get AI trading signals, tax harvesting alerts, and smart portfolio analytics. Free for Indian investors.',
  keywords: 'portfolio tracker india, stock portfolio, mutual fund tracker, AI trading signals, tax harvesting, XIRR calculator, nifty 50',
  openGraph: {
    title: 'StockPilot — AI-Powered Portfolio Intelligence',
    description: 'Track, analyze, and optimize your stock & mutual fund investments with AI signals, tax insights, and smart alerts.',
    type: 'website',
    locale: 'en_IN',
    siteName: 'StockPilot',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'StockPilot — AI Portfolio Intelligence',
    description: 'AI trading signals, tax harvesting alerts, portfolio analytics for Indian investors.',
  },
  icons: {
    icon: '/favicon.svg',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
        <link rel="manifest" href="/manifest.json" />
        {/* Per-scheme theme-color — matches the top of the page for each mode */}
        <meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0c0b09" />
        <meta name="theme-color" media="(prefers-color-scheme: light)" content="#f5f0e8" />
        <meta name="color-scheme" content="dark light" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            var theme = localStorage.getItem('theme') || 'dark';
            var accent = localStorage.getItem('accent') || 'indigo';
            document.documentElement.setAttribute('data-theme', theme);
            document.documentElement.setAttribute('data-accent', accent);
            if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
          })();
        `}} />
      </head>
      <body><Providers><ErrorBoundary>{children}</ErrorBoundary></Providers><ChatWidgetWrapper /></body>
    </html>
  );
}
