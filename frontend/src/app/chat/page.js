'use client';
import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Bot, User, Loader2, TrendingUp, TrendingDown, PieChart, Wallet, Trash2, Copy, Check, Download, Mic, MicOff, Globe, History, Plus } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const LANGUAGES = { en: 'English', hi: 'हिंदी', hinglish: 'Hinglish', ta: 'தமிழ்', te: 'తెలుగు', bn: 'বাংলা', mr: 'मराठी' };
const SUGGESTIONS = [
  "Am I over-exposed to any sector?",
  "Compare my returns with Nifty 50",
  "Do my mutual funds overlap?",
  "Any tax harvesting opportunities?",
  "Which stocks should I sell?",
  "What's my portfolio health score?",
  "Show me my top gainers",
  "What should I buy next?",
];

const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || '0';

const FOLLOW_UP_MAP = {
  perform: ["Which stocks are dragging me down?", "How are my MFs doing?", "What's my XIRR?"],
  tax: ["How can I save tax?", "Show STCG vs LTCG breakdown", "Which losses should I harvest?"],
  sell: ["What should I buy instead?", "Am I well diversified?", "Show my sector allocation"],
  divers: ["Show my sector allocation", "Do my MFs overlap?", "Should I add more sectors?"],
  loss: ["Should I sell or hold?", "Can I harvest these losses?", "What's my tax liability?"],
  gain: ["Should I book profits?", "What's my tax on these gains?", "Am I overweight in any stock?"],
  mf: ["Do my MFs overlap?", "Check MF health", "Compare stocks vs MF returns"],
  buy: ["Am I well diversified?", "What sectors am I missing?", "What's my risk level?"],
  overlap: ["Which funds should I consolidate?", "Am I over-diversified?", "Show sector allocation"],
  harvest: ["Which stocks to sell for tax saving?", "What's the wash sale rule?", "STCG vs LTCG breakdown"],
  health: ["How can I improve my score?", "Am I too concentrated?", "What sectors am I missing?"],
  nifty: ["Am I beating Nifty this year?", "Which stocks outperformed?", "Should I switch to index funds?"],
  sector: ["Am I over-exposed to banking?", "Which sectors am I missing?", "Show sector-wise P&L"],
};

function getFollowUps(messages) {
  const last = messages.filter(m => m.role === 'user').pop()?.content?.toLowerCase() || '';
  for (const [key, suggestions] of Object.entries(FOLLOW_UP_MAP)) {
    if (last.includes(key)) return suggestions;
  }
  return SUGGESTIONS.slice(0, 4);
}

function Markdown({ text }) {
  if (!text) return null;
  return (
    <div className="space-y-1.5">
      {text.split('\n').map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={i} className="h-1" />;
        if (trimmed.startsWith('### ')) return <div key={i} className="font-semibold text-[var(--text-primary)] mt-2">{trimmed.slice(4)}</div>;
        if (trimmed.startsWith('## ')) return <div key={i} className="font-bold text-[var(--text-primary)] mt-2">{trimmed.slice(3)}</div>;
        const isBullet = /^[-•*]\s/.test(trimmed);
        const isNumbered = /^\d+[.)]\s/.test(trimmed);
        const content = isBullet ? trimmed.slice(2) : isNumbered ? trimmed.replace(/^\d+[.)]\s/, '') : trimmed;
        const rendered = content.split(/(\*\*[^*]+\*\*|`[^`]+`)/).map((part, j) => {
          if (part.startsWith('**') && part.endsWith('**')) return <strong key={j}>{part.slice(2, -2)}</strong>;
          if (part.startsWith('`') && part.endsWith('`')) return <code key={j} className="px-1 py-0.5 bg-[var(--bg-tertiary)] rounded text-xs">{part.slice(1, -1)}</code>;
          return part;
        });
        if (isBullet) return <div key={i} className="flex gap-2 ml-1"><span className="text-[var(--accent)] mt-0.5">•</span><span>{rendered}</span></div>;
        if (isNumbered) return <div key={i} className="flex gap-2 ml-1"><span className="text-[var(--text-muted)] min-w-[1.2em]">{trimmed.match(/^\d+/)[0]}.</span><span>{rendered}</span></div>;
        return <div key={i}>{rendered}</div>;
      })}
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarData, setSidebarData] = useState(null);
  const [sidebarLoading, setSidebarLoading] = useState(true);
  const [copied, setCopied] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showSessions, setShowSessions] = useState(false);
  const [language, setLanguage] = useState('en');
  const [listening, setListening] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    api('/api/portfolio/dashboard').then(setSidebarData).catch(() => {}).finally(() => setSidebarLoading(false));
    api('/api/chat/sessions').then(d => setSessions(d || [])).catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const copyText = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopied(idx);
    setTimeout(() => setCopied(null), 1500);
  };

  const loadSession = async (sid) => {
    const msgs = await api(`/api/chat/sessions/${sid}`);
    setMessages(msgs || []);
    setSessionId(sid);
    setShowSessions(false);
  };

  const newChat = () => {
    setMessages([]);
    setSessionId(null);
    setShowSessions(false);
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    await api(`/api/chat/sessions/${sid}`, { method: 'DELETE' });
    setSessions(prev => prev.filter(s => s.id !== sid));
    if (sessionId === sid) newChat();
  };

  const exportChat = () => {
    if (sessionId) window.open(`${API_BASE}/api/chat/export/${sessionId}`, '_blank');
  };

  // Voice input
  const toggleVoice = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser');
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = language === 'hi' ? 'hi-IN' : language === 'ta' ? 'ta-IN' : language === 'te' ? 'te-IN' : language === 'bn' ? 'bn-IN' : language === 'mr' ? 'mr-IN' : 'en-IN';
    recognition.interimResults = false;
    recognition.onresult = (e) => { setInput(e.results[0][0].transcript); setListening(false); };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  };

  const handleSend = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput('');
    const userMsg = { role: 'user', content: msg };
    const history = [...messages, userMsg];
    setMessages(history);
    setLoading(true);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const res = await fetch(`${API_BASE}/api/chat/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ message: msg, history: history.slice(-10), session_id: sessionId, language }),
      });

      if (!res.ok || !res.body) {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Something went wrong. Please try again.' }]);
        setLoading(false);
        return;
      }

      // Stream response
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsg = '';
      setMessages(prev => [...prev, { role: 'assistant', content: '', suggestions: [] }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        assistantMsg += decoder.decode(value, { stream: true });
        
        // Parse metadata from response
        let displayMsg = assistantMsg;
        let suggestions = [];
        const metaMatch = assistantMsg.match(/<!--META:(.+?)-->/);
        if (metaMatch) {
          try {
            const meta = JSON.parse(metaMatch[1]);
            suggestions = meta.suggestions || [];
            if (meta.session_id && !sessionId) setSessionId(meta.session_id);
            if (meta.sparkline) {
              // Store sparkline data on the message
              displayMsg = assistantMsg.replace(/<!--META:.+?-->/, '').trim();
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: displayMsg, suggestions, sparkline: meta.sparkline, alert: meta.alert };
                return updated;
              });
              continue;
            }
          } catch {}
          displayMsg = assistantMsg.replace(/<!--META:.+?-->/, '').trim();
        }
        // Also handle old SUGGESTIONS format
        const sugMatch = displayMsg.match(/<!--SUGGESTIONS:(.+?)-->/);
        if (sugMatch) {
          suggestions = sugMatch[1].split(',').filter(Boolean);
          displayMsg = displayMsg.replace(/<!--SUGGESTIONS:.+?-->/, '').trim();
        }
        
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: displayMsg, suggestions };
          return updated;
        });
      }

      // Refresh sessions list
      api('/api/chat/sessions').then(d => setSessions(d || [])).catch(() => {});

      if (!assistantMsg) {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: 'No response received. Please try again.' };
          return updated;
        });
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Please try again.' }]);
    }
    setLoading(false);
  };

  const summary = sidebarData?.summary || {};
  const holdings = sidebarData?.holdings || [];
  const topGainers = [...holdings].filter(h => h.pnl > 0).sort((a, b) => b.pnl_pct - a.pnl_pct).slice(0, 3);
  const topLosers = [...holdings].filter(h => h.pnl < 0).sort((a, b) => a.pnl_pct - b.pnl_pct).slice(0, 3);
  
  // Get suggestions from last assistant message or use defaults
  const lastAssistantMsg = messages.filter(m => m.role === 'assistant').pop();
  const dynamicSuggestions = lastAssistantMsg?.suggestions?.length > 0 ? lastAssistantMsg.suggestions : getFollowUps(messages);

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-primary)]">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          <div className="px-4 md:px-6 pt-4 pb-2 flex items-center justify-between">
            <h1 className="text-lg font-bold flex items-center gap-2">
              <MessageSquare className="w-5 h-5" /> Portfolio Assistant
              <span className="text-[10px] bg-[var(--accent)]/20 text-[var(--accent)] px-2 py-0.5 rounded-full">StockPilot AI</span>
            </h1>
            <div className="flex items-center gap-2">
              <select value={language} onChange={e => setLanguage(e.target.value)} className="text-xs bg-[var(--bg-secondary)] border border-[var(--border)] rounded px-2 py-1 text-[var(--text-muted)]">
                {Object.entries(LANGUAGES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <button onClick={() => setShowSessions(!showSessions)} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1" title="Chat History">
                <History className="w-3.5 h-3.5" />
              </button>
              {sessionId && (
                <button onClick={exportChat} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1" title="Export Chat">
                  <Download className="w-3.5 h-3.5" />
                </button>
              )}
              <button onClick={newChat} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1" title="New Chat">
                <Plus className="w-3.5 h-3.5" />
              </button>
              {messages.length > 0 && (
                <button onClick={() => { setMessages([]); setSessionId(null); }} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1">
                  <Trash2 className="w-3.5 h-3.5" /> Clear
                </button>
              )}
            </div>
          </div>

          {/* Session History Dropdown */}
          {showSessions && (
            <div className="mx-4 mb-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg max-h-48 overflow-y-auto">
              {sessions.length === 0 ? (
                <div className="p-3 text-xs text-[var(--text-muted)] text-center">No previous chats</div>
              ) : sessions.map(s => (
                <div key={s.id} onClick={() => loadSession(s.id)} className={`flex items-center justify-between px-3 py-2 hover:bg-[var(--bg-tertiary)] cursor-pointer text-xs ${sessionId === s.id ? 'bg-[var(--accent)]/10' : ''}`}>
                  <div className="truncate flex-1">
                    <div className="font-medium text-[var(--text-primary)]">{s.title}</div>
                    <div className="text-[var(--text-muted)] truncate">{s.last_message}</div>
                  </div>
                  <button onClick={(e) => deleteSession(s.id, e)} className="ml-2 p-1 text-[var(--text-muted)] hover:text-[#ef4444]"><Trash2 className="w-3 h-3" /></button>
                </div>
              ))}
            </div>
          )}

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
                    <div className={`group relative max-w-[70%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)]'}`}>
                      <div className="text-sm whitespace-pre-wrap leading-relaxed"><Markdown text={msg.content} /></div>
                      {/* Sparkline Chart */}
                      {msg.sparkline?.length > 0 && (
                        <div className="mt-2 flex items-end gap-[2px] h-10 border-t border-[var(--border)] pt-2">
                          {msg.sparkline.map((d, j) => {
                            const prices = msg.sparkline.map(p => p.price);
                            const min = Math.min(...prices);
                            const max = Math.max(...prices);
                            const range = max - min || 1;
                            const height = ((d.price - min) / range) * 100;
                            const isUp = msg.sparkline[msg.sparkline.length - 1].price >= msg.sparkline[0].price;
                            return <div key={j} title={`${d.date}: ₹${d.price}`} className={`w-1 rounded-sm ${isUp ? 'bg-[#10b981]' : 'bg-[#ef4444]'}`} style={{ height: `${Math.max(height, 5)}%` }} />;
                          })}
                        </div>
                      )}
                      {msg.alert && <div className="mt-2 text-xs text-[#10b981] font-medium">{msg.alert}</div>}
                      {msg.role === 'assistant' && msg.content && (
                        <button onClick={() => copyText(msg.content, i)} className="absolute -bottom-5 right-0 text-[10px] text-[var(--text-muted)] hover:text-[var(--text-primary)] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5">
                          {copied === i ? <><Check className="w-3 h-3" /> Copied</> : <><Copy className="w-3 h-3" /> Copy</>}
                        </button>
                      )}
                    </div>
                    {msg.role === 'user' && (
                      <div className="w-7 h-7 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center shrink-0 mt-1">
                        <User className="w-3.5 h-3.5" />
                      </div>
                    )}
                  </div>
                ))}
                {loading && messages[messages.length - 1]?.role !== 'assistant' && (
                  <div className="flex gap-3">
                    <div className="w-7 h-7 rounded-full bg-[var(--accent)] flex items-center justify-center">
                      <Bot className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] p-3 rounded-lg">
                      <div className="flex gap-1 items-center h-4">
                        <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                        <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                        <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
                      </div>
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
              <div className="flex gap-2 mb-2 overflow-x-auto pb-1 scrollbar-hide">
                {dynamicSuggestions.map((s, i) => (
                  <button key={i} onClick={() => handleSend(s)} className="px-3 py-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-full text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--accent)]/50 whitespace-nowrap transition-colors">
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <button onClick={toggleVoice} className={`px-3 py-2.5 rounded-lg border ${listening ? 'bg-[#ef4444] text-white border-[#ef4444] animate-pulse' : 'bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'}`}>
                {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
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
