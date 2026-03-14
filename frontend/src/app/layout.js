import './globals.css';
import ChatWidgetWrapper from '../components/ChatWidgetWrapper';

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
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            var theme = localStorage.getItem('theme') || 'dark';
            var accent = localStorage.getItem('accent') || 'indigo';
            document.documentElement.setAttribute('data-theme', theme);
            document.documentElement.setAttribute('data-accent', accent);
          })();
        `}} />
      </head>
      <body>{children}<ChatWidgetWrapper /></body>
    </html>
  );
}
