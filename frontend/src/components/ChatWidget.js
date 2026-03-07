'use client';
import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Bot, User, Loader2, X, Maximize2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function Markdown({ text }) {
  return <>{text.split('**').map((part, j) => j % 2 === 1 ? <strong key={j}>{part}</strong> : part)}</>;
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const router = useRouter();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
        body: JSON.stringify({ message: msg, history: history.slice(-10) }),
      });

      if (!res.ok || !res.body) {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Something went wrong.' }]);
        setLoading(false);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsg = '';
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        assistantMsg += decoder.decode(value, { stream: true });
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: assistantMsg };
          return updated;
        });
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error.' }]);
    }
    setLoading(false);
  };

  const [pos, setPos] = useState({ x: 24, y: 24 }); // distance from bottom-right
  const dragRef = useRef(null);
  const dragging = useRef(false);
  const didDrag = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return;
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      setPos({
        x: Math.max(8, window.innerWidth - clientX - dragStart.current.x),
        y: Math.max(8, window.innerHeight - clientY - dragStart.current.y),
      });
      didDrag.current = true;
    };
    const onUp = () => { dragging.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchmove', onMove);
    window.addEventListener('touchend', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onUp);
    };
  }, []);

  const startDrag = (e) => {
    dragging.current = true;
    didDrag.current = false;
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const rect = dragRef.current.getBoundingClientRect();
    dragStart.current = { x: rect.right - clientX, y: rect.bottom - clientY };
  };

  return (
    <>
      {/* Floating Button */}
      {!open && (
        <button
          ref={dragRef}
          onMouseDown={startDrag}
          onTouchStart={startDrag}
          onClick={() => { if (!didDrag.current) setOpen(true); }}
          style={{ right: pos.x, bottom: pos.y }}
          className="fixed w-14 h-14 bg-[var(--accent)] text-white rounded-full shadow-lg hover:opacity-90 flex items-center justify-center z-50 cursor-grab active:cursor-grabbing"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}

      {/* Chat Panel */}
      {open && (
        <div style={{ right: Math.max(16, pos.x - 160), bottom: pos.y }} className="fixed w-[380px] h-[520px] bg-[var(--bg-primary)] border border-[var(--border)] rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-secondary)]">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-[var(--accent)] flex items-center justify-center">
                <Bot className="w-3.5 h-3.5 text-white" />
              </div>
              <div>
                <p className="text-sm font-semibold">StockPilot AI</p>
                <p className="text-[10px] text-green-400">Online</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => { setOpen(false); router.push('/chat'); }} className="p-1.5 hover:bg-[var(--bg-primary)] rounded-lg" title="Open full chat">
                <Maximize2 className="w-4 h-4 text-[var(--text-muted)]" />
              </button>
              <button onClick={() => setOpen(false)} className="p-1.5 hover:bg-[var(--bg-primary)] rounded-lg">
                <X className="w-4 h-4 text-[var(--text-muted)]" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.length === 0 && (
              <div className="text-center py-8">
                <Bot className="w-10 h-10 text-[var(--accent)] mx-auto mb-3 opacity-50" />
                <p className="text-xs text-[var(--text-muted)] mb-3">Ask about your portfolio</p>
                <div className="space-y-1.5">
                  {["How is my portfolio?", "Top gainers?", "Tax liability?"].map((s, i) => (
                    <button key={i} onClick={() => handleSend(s)} className="block w-full px-3 py-1.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] text-left">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-full bg-[var(--accent)] flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-3 h-3 text-white" />
                  </div>
                )}
                <div className={`max-w-[80%] px-3 py-2 rounded-lg text-xs leading-relaxed ${msg.role === 'user' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)]'}`}>
                  <span className="whitespace-pre-wrap"><Markdown text={msg.content} /></span>
                </div>
              </div>
            ))}
            {loading && messages[messages.length - 1]?.role !== 'assistant' && (
              <div className="flex gap-2">
                <div className="w-6 h-6 rounded-full bg-[var(--accent)] flex items-center justify-center">
                  <Bot className="w-3 h-3 text-white" />
                </div>
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] px-3 py-2 rounded-lg">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--text-muted)]" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="px-3 py-2 border-t border-[var(--border)]">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask anything..."
                disabled={loading}
                className="flex-1 px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs focus:outline-none focus:border-[var(--accent)] disabled:opacity-50"
              />
              <button onClick={() => handleSend()} disabled={loading || !input.trim()} className="px-3 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50">
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
