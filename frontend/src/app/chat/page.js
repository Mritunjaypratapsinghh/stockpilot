'use client';
import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Bot, User, Loader2, TrendingUp, TrendingDown, PieChart, Wallet } from 'lucide-react';
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

const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [portfolioData, setPortfolioData] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    Promise.all([
      api('/api/portfolio/dashboard').catch(() => null),
      api('/api/analytics').catch(() => null),
      api('/api/finance/tax').catch(() => null),
      api('/api/analytics/signals').catch(() => null),
    ]).then(([dashboard, analytics, tax, signals]) => {
      setPortfolioData({ dashboard, analytics, tax, signals });
      setDataLoading(false);
    });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const analyzeQuery = (query) => {
    if (!portfolioData) return "Portfolio data unavailable. Please refresh.";
    const q = query.toLowerCase();
    const { dashboard, analytics, tax, signals } = portfolioData;
    const holdings = dashboard?.holdings || [];
    const summary = dashboard?.summary || {};

    if (q.includes('perform') || (q.includes('how') && q.includes('portfolio'))) {
      const pnl = summary.pnl || 0;
      const pnlPct = summary.pnl_pct || 0;
      return `📊 **Portfolio Performance**\n\n• Current Value: ₹${fmt(summary.current)}\n• Invested: ₹${fmt(summary.invested)}\n• Total P&L: ${pnl >= 0 ? '+' : ''}₹${fmt(pnl)} (${pnlPct >= 0 ? '+' : ''}${pnlPct?.toFixed(1)}%)\n• Today: ${(summary.day_pnl || 0) >= 0 ? '+' : ''}₹${fmt(summary.day_pnl)}\n\n${pnlPct > 15 ? '🎉 Excellent returns!' : pnlPct > 0 ? '👍 Portfolio is in profit.' : '📉 Portfolio is in loss. Review underperformers.'}`;
    }

    if (q.includes('gainer') || q.includes('best') || q.includes('top')) {
      const gainers = [...holdings].filter(h => h.pnl > 0).sort((a, b) => b.pnl_pct - a.pnl_pct).slice(0, 5);
      if (!gainers.length) return "No stocks in profit currently.";
      return `🏆 **Top Gainers**\n\n${gainers.map((h, i) => `${i + 1}. **${h.symbol}**: +${h.pnl_pct?.toFixed(1)}% (+₹${fmt(h.pnl)})`).join('\n')}`;
    }

    if (q.includes('loss') || q.includes('loser') || q.includes('worst') || q.includes('down')) {
      const losers = [...holdings].filter(h => h.pnl < 0).sort((a, b) => a.pnl_pct - b.pnl_pct).slice(0, 5);
      if (!losers.length) return "🎉 No stocks in loss!";
      return `📉 **Stocks in Loss**\n\n${losers.map((h, i) => `${i + 1}. **${h.symbol}**: ${h.pnl_pct?.toFixed(1)}% (₹${fmt(h.pnl)})`).join('\n')}\n\n💡 Consider tax-loss harvesting before March 31.`;
    }

    if (q.includes('sell') || q.includes('exit')) {
      const sells = signals?.portfolio?.filter(s => s.action === 'SELL' || s.action === 'REDUCE') || [];
      if (!sells.length) return "No strong sell signals currently. Your holdings look stable.";
      return `🔴 **Sell/Reduce Recommendations**\n\n${sells.slice(0, 5).map(s => `• **${s.symbol}** (${s.action}): ${s.reasons?.[0] || 'Consider reducing'}`).join('\n')}`;
    }

    if (q.includes('buy') || q.includes('add')) {
      const buys = signals?.portfolio?.filter(s => s.action === 'BUY' || s.action === 'ADD') || [];
      if (!buys.length) return "No strong buy signals right now.";
      return `🟢 **Buy/Add Recommendations**\n\n${buys.slice(0, 5).map(s => `• **${s.symbol}** (${s.action}): ${s.reasons?.[0] || 'Good opportunity'}`).join('\n')}`;
    }

    if (q.includes('diversif') || q.includes('sector') || q.includes('allocat')) {
      const sectors = (analytics?.sectors || []).filter(s => s.sector !== 'Others' && s.sector !== 'Unknown');
      const othersTotal = (analytics?.sectors || []).filter(s => s.sector === 'Others' || s.sector === 'Unknown').reduce((sum, s) => sum + (s.percentage || 0), 0);
      if (!sectors.length && othersTotal > 0) return "Sector data isn't available for most of your holdings. This usually means sector info hasn't been fetched yet — try refreshing your portfolio.";
      if (!sectors.length) return "Add more holdings to see sector allocation.";
      const topSector = sectors[0];
      return `🥧 **Sector Allocation**\n\n${sectors.slice(0, 6).map(s => `• ${s.sector}: ${s.percentage?.toFixed(1)}%`).join('\n')}${othersTotal > 10 ? `\n• Unclassified: ${othersTotal.toFixed(1)}%` : ''}\n\n${topSector?.percentage > 40 ? `⚠️ Heavy in ${topSector.sector}. Consider diversifying.` : '✅ Reasonably diversified across sectors.'}`;
    }

    if (q.includes('tax')) {
      const t = tax?.tax_liability || {};
      return `💰 **Tax Summary (FY ${tax?.financial_year || '2025-26'})**\n\n• STCG Tax: ₹${fmt(t.stcg_tax)}\n• LTCG Tax: ₹${fmt(t.ltcg_tax)}\n• **Total: ₹${fmt(t.total_tax)}**\n\n💡 Visit Tax Center for harvesting opportunities.`;
    }

    if (q.includes('how many') || q.includes('count') || q.includes('holding')) {
      const stocks = holdings.filter(h => h.holding_type !== 'MF').length;
      const mfs = holdings.filter(h => h.holding_type === 'MF').length;
      return `📋 **Holdings**\n\n• Stocks: ${stocks}\n• Mutual Funds: ${mfs}\n• Total: ${holdings.length}`;
    }

    return `I can help with:\n• Portfolio performance & P&L\n• Top gainers and losers\n• Buy/sell recommendations\n• Sector diversification\n• Tax liability\n\nTry: "${SUGGESTIONS[Math.floor(Math.random() * SUGGESTIONS.length)]}"`;
  };

  const handleSend = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading || dataLoading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);
    await new Promise(r => setTimeout(r, 400));
    setMessages(prev => [...prev, { role: 'assistant', content: analyzeQuery(msg) }]);
    setLoading(false);
  };

  // Sidebar stats
  const summary = portfolioData?.dashboard?.summary || {};
  const holdings = portfolioData?.dashboard?.holdings || [];
  const topGainers = [...holdings].filter(h => h.pnl > 0).sort((a, b) => b.pnl_pct - a.pnl_pct).slice(0, 3);
  const topLosers = [...holdings].filter(h => h.pnl < 0).sort((a, b) => a.pnl_pct - b.pnl_pct).slice(0, 3);

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-primary)]">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          <div className="px-4 md:px-6 pt-4 pb-2">
            <h1 className="text-lg font-bold flex items-center gap-2">
              <MessageSquare className="w-5 h-5" /> Portfolio Assistant
              <span className="text-[10px] bg-[var(--accent)]/20 text-[var(--accent)] px-2 py-0.5 rounded-full">AI</span>
            </h1>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 pb-2">
            {dataLoading ? (
              <div className="flex items-center gap-3 p-4 bg-[var(--bg-secondary)] rounded-lg mt-2">
                <Loader2 className="w-5 h-5 animate-spin text-[var(--accent)]" />
                <span className="text-sm text-[var(--text-muted)]">Loading your portfolio data...</span>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="w-12 h-12 text-[var(--accent)] mb-4 opacity-50" />
                <p className="text-sm text-[var(--text-muted)] mb-6">Ask me anything about your portfolio</p>
                <div className="grid grid-cols-2 gap-2 max-w-md">
                  {SUGGESTIONS.map((s, i) => (
                    <button key={i} onClick={() => handleSend(s)} className="px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--accent)]/50 text-left transition-colors">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4 py-2">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                    {msg.role === 'assistant' && (
                      <div className="w-7 h-7 rounded-full bg-[var(--accent)] flex items-center justify-center shrink-0 mt-1">
                        <Bot className="w-3.5 h-3.5 text-white" />
                      </div>
                    )}
                    <div className={`max-w-[70%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)]'}`}>
                      <div className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content.split('**').map((part, j) =>
                        j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                      )}</div>
                    </div>
                    {msg.role === 'user' && (
                      <div className="w-7 h-7 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center shrink-0 mt-1">
                        <User className="w-3.5 h-3.5" />
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-3">
                    <div className="w-7 h-7 rounded-full bg-[var(--accent)] flex items-center justify-center">
                      <Bot className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] p-3 rounded-lg">
                      <Loader2 className="w-4 h-4 animate-spin text-[var(--text-muted)]" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input */}
          <div className="px-4 md:px-6 py-3 border-t border-[var(--border)]">
            {messages.length > 0 && (
              <div className="flex gap-2 mb-2 overflow-x-auto pb-1">
                {SUGGESTIONS.slice(0, 4).map((s, i) => (
                  <button key={i} onClick={() => handleSend(s)} disabled={dataLoading} className="px-3 py-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-full text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] whitespace-nowrap disabled:opacity-50">
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={dataLoading ? "Loading portfolio..." : "Ask about your portfolio..."}
                disabled={dataLoading}
                className="flex-1 px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-sm focus:outline-none focus:border-[var(--accent)] disabled:opacity-50"
              />
              <button onClick={() => handleSend()} disabled={loading || !input.trim() || dataLoading} className="px-4 py-2.5 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="hidden lg:block w-80 border-l border-[var(--border)] overflow-y-auto p-4 space-y-4">
          {dataLoading ? (
            <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-20 bg-[var(--bg-secondary)] rounded-lg animate-pulse" />)}</div>
          ) : (
            <>
              {/* Portfolio Summary */}
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1"><Wallet className="w-3 h-3" /> Portfolio</p>
                <p className="text-xl font-bold">₹{fmt(summary.current)}</p>
                <p className={`text-xs mt-1 ${(summary.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(summary.pnl || 0) >= 0 ? '+' : ''}₹{fmt(summary.pnl)} ({(summary.pnl_pct || 0) >= 0 ? '+' : ''}{summary.pnl_pct?.toFixed(1)}%)
                </p>
              </div>

              {/* Quick Stats */}
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1"><PieChart className="w-3 h-3" /> Holdings</p>
                <div className="flex justify-between text-sm">
                  <span>{holdings.filter(h => h.holding_type !== 'MF').length} Stocks</span>
                  <span>{holdings.filter(h => h.holding_type === 'MF').length} MFs</span>
                </div>
              </div>

              {/* Top Gainers */}
              {topGainers.length > 0 && (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1"><TrendingUp className="w-3 h-3 text-green-400" /> Top Gainers</p>
                  <div className="space-y-2">
                    {topGainers.map(h => (
                      <div key={h.symbol} className="flex justify-between text-xs">
                        <span>{h.symbol}</span>
                        <span className="text-green-400">+{h.pnl_pct?.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Top Losers */}
              {topLosers.length > 0 && (
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1"><TrendingDown className="w-3 h-3 text-red-400" /> Top Losers</p>
                  <div className="space-y-2">
                    {topLosers.map(h => (
                      <div key={h.symbol} className="flex justify-between text-xs">
                        <span>{h.symbol}</span>
                        <span className="text-red-400">{h.pnl_pct?.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
