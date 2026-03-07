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
  const [sidebarData, setSidebarData] = useState(null);
  const [sidebarLoading, setSidebarLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    api('/api/portfolio/dashboard').then(setSidebarData).catch(() => {}).finally(() => setSidebarLoading(false));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput('');
    const userMsg = { role: 'user', content: msg };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api('/api/chat/ask', {
        method: 'POST',
        body: JSON.stringify({ message: msg, history: [...messages, userMsg].slice(-10) }),
      });
      setMessages(prev => [...prev, { role: 'assistant', content: res?.reply || 'Could not get a response. Please try again.' }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Something went wrong. Please try again.' }]);
    }
    setLoading(false);
  };

  const summary = sidebarData?.summary || {};
  const holdings = sidebarData?.holdings || [];
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
              <span className="text-[10px] bg-[var(--accent)]/20 text-[var(--accent)] px-2 py-0.5 rounded-full">Gemini AI</span>
            </h1>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 pb-2">
            {messages.length === 0 ? (
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
                  <button key={i} onClick={() => handleSend(s)} className="px-3 py-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-full text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] whitespace-nowrap">
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
                placeholder="Ask about your portfolio..."
                disabled={loading}
                className="flex-1 px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-sm focus:outline-none focus:border-[var(--accent)] disabled:opacity-50"
              />
              <button onClick={() => handleSend()} disabled={loading || !input.trim()} className="px-4 py-2.5 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="hidden lg:block w-80 border-l border-[var(--border)] overflow-y-auto p-4 space-y-4">
          {sidebarLoading ? (
            <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-20 bg-[var(--bg-secondary)] rounded-lg animate-pulse" />)}</div>
          ) : (
            <>
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1"><Wallet className="w-3 h-3" /> Portfolio</p>
                <p className="text-xl font-bold">₹{fmt(summary.current)}</p>
                <p className={`text-xs mt-1 ${(summary.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(summary.pnl || 0) >= 0 ? '+' : ''}₹{fmt(summary.pnl)} ({(summary.pnl_pct || 0) >= 0 ? '+' : ''}{summary.pnl_pct?.toFixed(1)}%)
                </p>
              </div>

              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1"><PieChart className="w-3 h-3" /> Holdings</p>
                <div className="flex justify-between text-sm">
                  <span>{holdings.filter(h => h.holding_type !== 'MF').length} Stocks</span>
                  <span>{holdings.filter(h => h.holding_type === 'MF').length} MFs</span>
                </div>
              </div>

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
