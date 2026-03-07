'use client';
import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Bot, User, Sparkles, TrendingUp, PieChart, AlertTriangle } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

const SUGGESTIONS = [
  "How is my portfolio performing?",
  "Which stocks should I sell?",
  "Am I well diversified?",
  "What's my tax liability?",
  "Show me my top gainers",
  "Any stocks in loss?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! I'm your portfolio assistant. Ask me anything about your investments - performance, diversification, tax, or get buy/sell recommendations." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [portfolioData, setPortfolioData] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Pre-fetch portfolio data
    Promise.all([
      api('/api/portfolio/dashboard'),
      api('/api/analytics'),
      api('/api/finance/tax'),
      api('/api/analytics/signals').catch(() => null),
    ]).then(([dashboard, analytics, tax, signals]) => {
      setPortfolioData({ dashboard, analytics, tax, signals });
    });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const analyzeQuery = async (query) => {
    if (!portfolioData) return "Still loading your portfolio data. Please wait a moment.";

    const q = query.toLowerCase();
    const { dashboard, analytics, tax, signals } = portfolioData;
    const holdings = dashboard?.holdings || [];
    const summary = dashboard?.summary || {};

    // Performance queries
    if (q.includes('perform') || q.includes('how') && q.includes('portfolio')) {
      const pnl = summary.pnl || 0;
      const pnlPct = summary.pnl_pct || 0;
      const dayPnl = summary.day_pnl || 0;
      return `📊 **Portfolio Performance**\n\n` +
        `• Current Value: ₹${fmt(summary.current)}\n` +
        `• Invested: ₹${fmt(summary.invested)}\n` +
        `• Total P&L: ${pnl >= 0 ? '+' : ''}₹${fmt(pnl)} (${pnlPct >= 0 ? '+' : ''}${pnlPct?.toFixed(1)}%)\n` +
        `• Today: ${dayPnl >= 0 ? '+' : ''}₹${fmt(dayPnl)}\n\n` +
        (pnlPct > 15 ? "🎉 Excellent! Your portfolio is outperforming." : 
         pnlPct > 0 ? "👍 Your portfolio is in profit." : 
         "📉 Your portfolio is currently in loss. Consider reviewing underperformers.");
    }

    // Top gainers
    if (q.includes('gainer') || q.includes('best') || q.includes('top')) {
      const gainers = [...holdings].filter(h => h.pnl > 0).sort((a, b) => b.pnl_pct - a.pnl_pct).slice(0, 5);
      if (!gainers.length) return "No stocks in profit currently.";
      return `🏆 **Top Gainers**\n\n` + gainers.map((h, i) => 
        `${i + 1}. **${h.symbol}**: +${h.pnl_pct?.toFixed(1)}% (+₹${fmt(h.pnl)})`
      ).join('\n');
    }

    // Losers
    if (q.includes('loss') || q.includes('loser') || q.includes('worst') || q.includes('down')) {
      const losers = [...holdings].filter(h => h.pnl < 0).sort((a, b) => a.pnl_pct - b.pnl_pct).slice(0, 5);
      if (!losers.length) return "🎉 Great news! No stocks in loss.";
      return `📉 **Stocks in Loss**\n\n` + losers.map((h, i) => 
        `${i + 1}. **${h.symbol}**: ${h.pnl_pct?.toFixed(1)}% (₹${fmt(h.pnl)})`
      ).join('\n') + `\n\n💡 Consider tax-loss harvesting before March 31.`;
    }

    // Sell recommendations
    if (q.includes('sell') || q.includes('exit')) {
      const sellSignals = signals?.portfolio?.filter(s => s.action === 'SELL' || s.action === 'REDUCE') || [];
      if (!sellSignals.length) return "No strong sell signals currently. Your holdings look stable.";
      return `🔴 **Sell/Reduce Recommendations**\n\n` + sellSignals.slice(0, 5).map(s => 
        `• **${s.symbol}** (${s.action}): ${s.reasons?.[0] || 'Consider reducing'}`
      ).join('\n');
    }

    // Buy recommendations
    if (q.includes('buy') || q.includes('add')) {
      const buySignals = signals?.portfolio?.filter(s => s.action === 'BUY' || s.action === 'ADD') || [];
      if (!buySignals.length) return "No strong buy signals currently. Market conditions suggest caution.";
      return `🟢 **Buy/Add Recommendations**\n\n` + buySignals.slice(0, 5).map(s => 
        `• **${s.symbol}** (${s.action}): ${s.reasons?.[0] || 'Good opportunity'}`
      ).join('\n');
    }

    // Diversification
    if (q.includes('diversif') || q.includes('sector') || q.includes('allocat')) {
      const sectors = analytics?.sectors || [];
      if (!sectors.length) return "Add more holdings to see sector allocation.";
      const topSector = sectors[0];
      const isConcentrated = topSector?.percentage > 40;
      return `🥧 **Sector Allocation**\n\n` + sectors.slice(0, 5).map(s => 
        `• ${s.sector}: ${s.percentage}%`
      ).join('\n') + `\n\n` + 
        (isConcentrated ? `⚠️ High concentration in ${topSector.sector}. Consider diversifying.` : 
         "✅ Good diversification across sectors.");
    }

    // Tax
    if (q.includes('tax')) {
      const taxData = tax?.tax_liability || {};
      return `💰 **Tax Summary (FY ${tax?.financial_year})**\n\n` +
        `• STCG Tax: ₹${fmt(taxData.stcg_tax)}\n` +
        `• LTCG Tax: ₹${fmt(taxData.ltcg_tax)}\n` +
        `• **Total Tax: ₹${fmt(taxData.total_tax)}**\n\n` +
        `💡 Visit Tax Center for harvesting opportunities.`;
    }

    // Holdings count
    if (q.includes('how many') || q.includes('count') || q.includes('holding')) {
      const stocks = holdings.filter(h => h.holding_type !== 'MF').length;
      const mfs = holdings.filter(h => h.holding_type === 'MF').length;
      return `📋 **Portfolio Composition**\n\n• Stocks: ${stocks}\n• Mutual Funds: ${mfs}\n• Total Holdings: ${holdings.length}`;
    }

    // Default
    return `I can help you with:\n\n` +
      `• Portfolio performance & P&L\n` +
      `• Top gainers and losers\n` +
      `• Buy/sell recommendations\n` +
      `• Sector diversification\n` +
      `• Tax liability\n\n` +
      `Try asking: "${SUGGESTIONS[Math.floor(Math.random() * SUGGESTIONS.length)]}"`;
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    const response = await analyzeQuery(userMsg);
    setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col">
      <Navbar />
      <main className="flex-1 flex flex-col p-4 md:p-6 max-w-4xl mx-auto w-full">
        <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2 mb-4">
          <MessageSquare className="w-5 h-5 md:w-6 md:h-6" /> Portfolio Assistant
          <span className="text-xs bg-[var(--accent)]/20 text-[var(--accent)] px-2 py-0.5 rounded-full ml-2">AI</span>
        </h1>

        {/* Chat Messages */}
        <div className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-4 overflow-y-auto min-h-[400px] max-h-[60vh]">
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-[var(--accent)] flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={`max-w-[80%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-primary)]'}`}>
                  <div className="text-sm whitespace-pre-wrap">{msg.content.split('**').map((part, j) => 
                    j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                  )}</div>
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-[var(--accent)] flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-[var(--bg-primary)] p-3 rounded-lg">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Suggestions */}
        <div className="flex gap-2 mb-3 overflow-x-auto pb-2">
          {SUGGESTIONS.slice(0, 4).map((s, i) => (
            <button key={i} onClick={() => setInput(s)} className="px-3 py-1.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-full text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] whitespace-nowrap">
              {s}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your portfolio..."
            className="flex-1 px-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-sm focus:outline-none focus:border-[var(--accent)]"
          />
          <button onClick={handleSend} disabled={loading || !input.trim()} className="px-4 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </main>
    </div>
  );
}
