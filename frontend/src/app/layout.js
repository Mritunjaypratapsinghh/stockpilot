import './globals.css';

export const metadata = {
  title: 'StockPilot',
  description: 'Portfolio Intelligence Platform',
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
            document.documentElement.setAttribute('data-theme', theme);
          })();
        `}} />
      </head>
      <body>{children}</body>
    </html>
  );
}
