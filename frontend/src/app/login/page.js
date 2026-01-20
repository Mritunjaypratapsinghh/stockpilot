'use client';
import { useState } from 'react';
import { TrendingUp, Eye, EyeOff, ArrowRight, Shield, BarChart3, Bell } from 'lucide-react';
import { api } from '../../lib/api';

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try { const res = await api(isLogin ? '/api/auth/login' : '/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }); localStorage.setItem('token', res.access_token); window.location.href = '/'; }
    catch (err) { setError(err.message); } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex">
      {/* Left */}
      <div className="hidden lg:flex lg:w-1/2 bg-[var(--bg-secondary)] flex-col justify-between p-12">
        <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-[#6366f1] flex items-center justify-center"><TrendingUp className="w-5 h-5 text-white" /></div><span className="text-xl font-semibold">StockPilot</span></div>
        <div className="max-w-md">
          <h1 className="text-4xl font-bold leading-tight mb-4">Smart portfolio tracking for serious investors</h1>
          <p className="text-[var(--text-secondary)] text-lg mb-10">Real-time analytics, intelligent alerts, and AI-powered insights.</p>
          <div className="space-y-4">
            {[{ icon: BarChart3, text: 'Real-time portfolio analytics' }, { icon: Bell, text: 'Smart price & volume alerts' }, { icon: Shield, text: 'Bank-grade security' }].map((item, i) => (
              <div key={i} className="flex items-center gap-3 text-[var(--text-secondary)]"><div className="w-10 h-10 rounded-lg bg-[var(--border)] flex items-center justify-center"><item.icon className="w-5 h-5 text-[#6366f1]" /></div><span>{item.text}</span></div>
            ))}
          </div>
        </div>
        <p className="text-[var(--text-muted)] text-sm">© 2026 StockPilot</p>
      </div>

      {/* Right */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-3 mb-8"><div className="w-10 h-10 rounded-lg bg-[#6366f1] flex items-center justify-center"><TrendingUp className="w-5 h-5 text-white" /></div><span className="text-xl font-semibold">StockPilot</span></div>
          <h2 className="text-2xl font-bold mb-1">{isLogin ? 'Welcome back' : 'Create account'}</h2>
          <p className="text-[var(--text-muted)] mb-8">{isLogin ? 'Enter your credentials' : 'Start your journey'}</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && <div className="p-3 rounded-lg bg-[#ef4444]/10 border border-[#ef4444]/20 text-[#ef4444] text-sm">{error}</div>}
            <div><label className="block text-sm text-[var(--text-secondary)] mb-2">Email</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full px-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-white focus:border-[#6366f1]" placeholder="name@company.com" required /></div>
            <div><label className="block text-sm text-[var(--text-secondary)] mb-2">Password</label><div className="relative"><input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} className="w-full px-4 py-3 pr-12 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-white focus:border-[#6366f1]" placeholder="••••••••" required /><button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white">{showPw ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}</button></div></div>
            <button type="submit" disabled={loading} className="w-full py-3 bg-[#6366f1] text-white rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-[#5558e3] disabled:opacity-50">{loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <>{isLogin ? 'Sign in' : 'Create account'}<ArrowRight className="w-4 h-4" /></>}</button>
          </form>
          <p className="text-center text-sm text-[var(--text-muted)] mt-8">{isLogin ? "Don't have an account? " : 'Have an account? '}<button onClick={() => { setIsLogin(!isLogin); setError(''); }} className="text-[#6366f1] hover:text-[#5558e3] font-medium">{isLogin ? 'Sign up' : 'Sign in'}</button></p>
        </div>
      </div>
    </div>
  );
}
