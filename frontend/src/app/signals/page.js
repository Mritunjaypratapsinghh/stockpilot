'use client';
import { useState, useEffect } from 'react';
import { Zap, TrendingUp, TrendingDown, RefreshCw, Target, ChevronDown, ChevronUp, AlertTriangle, Shield, Activity } from 'lucide-react';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

const ConfidenceBadge = ({ level }) => {
  const styles = {
    HIGH: 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30',
    MEDIUM: 'bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30',
    LOW: 'bg-[var(--border)] text-[var(--text-muted)] border-[var(--border)]',
  };
  return <span className={`px-2 py-0.5 rounded text-xs font-medium border ${styles[level] || styles.LOW}`}>{level}</span>;
};

const MarketBanner = ({ regime, change }) => {
  if (!regime || regime === 'NEUTRAL') return null;
  const styles = {
    CRASH: { bg: 'bg-[#ef4444]/10', border: 'border-[#ef4444]/30', text: 'text-[#ef4444]', icon: AlertTriangle, msg: 'Market Crash' },
    BEAR: { bg: 'bg-[#f59e0b]/10', border: 'border-[#f59e0b]/30', text: 'text-[#f59e0b]', icon: TrendingDown, msg: 'Bearish Market' },
    BULL: { bg: 'bg-[#10b981]/10', border: 'border-[#10b981]/30', text: 'text-[#10b981]', icon: TrendingUp, msg: 'Bullish Market' },
  };
  const s = styles[regime];
  if (!s) return null;
  const Icon = s.icon;
  return (
    <div className={`${s.bg} ${s.border} border rounded-lg p-3 mb-4 flex items-center gap-3`}>
      <Icon className={`w-5 h-5 ${s.text}`} />
      <div><span className={`font-medium ${s.text}`}>{s.msg}</span><span className="text-[var(--text-muted)] ml-2">Nifty {change >= 0 ? '+' : ''}{change?.toFixed(2)}% today</span></div>
    </div>
  );
};

export default function SignalsPage() {
  const [data, setData] = useState({ portfolio: [], ipos: [], market_regime: 'NEUTRAL', summary: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({});

  const loadSignals = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api('/api/analytics/signals', { method: 'POST' });
      setData(result);
    } catch (e) {
      setError(e.message || 'Failed to load signals');
    }
    setLoading(false);
  };

  useEffect(() => { loadSignals(); }, []);

  const toggleExpand = (i) => setExpanded(prev => ({ ...prev, [i]: !prev[i] }));

  const getActionStyle = (action) => {
    if (action === 'STRONG BUY') return { bg: 'bg-[#10b981]/20', text: 'text-[#10b981]', icon: TrendingUp };
    if (action === 'BUY MORE' || action === 'ADD') return { bg: 'bg-[#10b981]/10', text: 'text-[#10b981]', icon: TrendingUp };
    if (action === 'PARTIAL SELL' || action === 'TRIM') return { bg: 'bg-[#f59e0b]/10', text: 'text-[#f59e0b]', icon: TrendingDown };
    if (action === 'EXIT') return { bg: 'bg-[#ef4444]/20', text: 'text-[#ef4444]', icon: TrendingDown };
    if (action === 'AVOID') return { bg: 'bg-[#ef4444]/10', text: 'text-[#ef4444]', icon: AlertTriangle };
    if (action === 'WAIT') return { bg: 'bg-[#8b5cf6]/10', text: 'text-[#8b5cf6]', icon: Target };
    return { bg: 'bg-[var(--border)]', text: 'text-[var(--text-muted)]', icon: Target };
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-4 md:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center"><Zap className="w-6 h-6 text-[var(--accent)]" /></div>
            <div><h1 className="text-xl md:text-2xl font-bold">Smart Signals</h1><p className="text-[var(--text-muted)]">Fundamentals + Technicals + Portfolio Context</p></div>
          </div>
          <button onClick={loadSignals} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium hover:bg-[#5558e3] disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Analyze
          </button>
        </div>

        {error && (
          <div className="bg-[#ef4444]/10 border border-[#ef4444]/30 rounded-lg p-4 mb-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-[#ef4444]" />
            <span className="text-[#ef4444]">{error}</span>
            <button onClick={loadSignals} className="ml-auto text-sm underline text-[#ef4444]">Retry</button>
          </div>
        )}

        {loading ? (
          <div className="py-20 text-center">
            <div className="flex justify-center gap-1 mb-4">{[0, 1, 2].map(i => <div key={i} className="w-3 h-3 bg-[var(--accent)] rounded-full animate-pulse" style={{ animationDelay: `${i * 150}ms` }} />)}</div>
            <p className="text-[var(--text-muted)]">Analyzing portfolio with fundamentals...</p>
          </div>
        ) : (
          <>
            <MarketBanner regime={data.market_regime} change={data.nifty_change} />

            {/* Summary Cards */}
            {data.summary && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-xl md:text-2xl font-bold">{data.summary.total_signals || 0}</div>
                  <div className="text-sm text-[var(--text-muted)]">Holdings Analyzed</div>
                </div>
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-xl md:text-2xl font-bold text-[var(--accent)]">{data.summary.actionable || 0}</div>
                  <div className="text-sm text-[var(--text-muted)]">Actionable Signals</div>
                </div>
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-xl md:text-2xl font-bold text-[#10b981]">{data.summary.high_confidence || 0}</div>
                  <div className="text-sm text-[var(--text-muted)]">High Confidence</div>
                </div>
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                  <div className="text-sm text-[var(--text-muted)]">{data.summary.market_note || 'Stock-specific approach'}</div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="col-span-2">
                <h2 className="text-sm font-medium text-[var(--text-muted)] uppercase mb-4">Portfolio Signals</h2>
                {data.portfolio?.length === 0 ? (
                  <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-12 text-center">
                    <Target className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
                    <div className="text-[var(--text-muted)]">No holdings to analyze</div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.portfolio?.map((r, i) => {
                      const style = getActionStyle(r.action);
                      const Icon = style.icon;
                      const isExpanded = expanded[i];

                      return (
                        <div key={i} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 cursor-pointer hover:bg-[var(--bg-hover)]" onClick={() => toggleExpand(i)}>
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${style.bg}`}>
                                <Icon className={`w-5 h-5 ${style.text}`} />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{r.symbol}</span>
                                  <ConfidenceBadge level={r.confidence} />
                                </div>
                                <div className="text-sm text-[var(--text-muted)]">
                                  ₹{r.current_price?.toFixed(2)} • <span className={r.pnl_pct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}>{r.pnl_pct >= 0 ? '+' : ''}{r.pnl_pct?.toFixed(1)}%</span>
                                  {r.sector && <span className="ml-2 text-[var(--text-muted)]">• {r.sector}</span>}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className={`px-3 py-1 rounded text-sm font-medium ${style.bg} ${style.text}`}>{r.action}</span>
                              {isExpanded ? <ChevronUp className="w-5 h-5 text-[var(--text-muted)]" /> : <ChevronDown className="w-5 h-5 text-[var(--text-muted)]" />}
                            </div>
                          </div>

                          {isExpanded && (
                            <div className="px-4 pb-4 border-t border-[var(--border)] pt-4 space-y-4">
                              {/* Warnings */}
                              {r.warnings?.length > 0 && (
                                <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/30 rounded-lg p-3">
                                  {r.warnings.map((w, j) => (
                                    <div key={j} className="text-sm text-[#f59e0b] flex items-start gap-2">
                                      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" /> {w}
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Key Metrics */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                <div className="bg-[var(--bg-primary)] rounded p-2">
                                  <div className="text-[var(--text-muted)]">Avg Price</div>
                                  <div className="font-medium">₹{r.avg_price?.toFixed(2)}</div>
                                </div>
                                <div className="bg-[var(--bg-primary)] rounded p-2">
                                  <div className="text-[var(--text-muted)]">RSI</div>
                                  <div className={`font-medium ${r.rsi < 30 ? 'text-[#10b981]' : r.rsi > 70 ? 'text-[#ef4444]' : ''}`}>{r.rsi}</div>
                                </div>
                                {r.target && (
                                  <div className="bg-[var(--bg-primary)] rounded p-2">
                                    <div className="text-[var(--text-muted)]">{r.target_label || 'Target'}</div>
                                    <div className="font-medium text-[#10b981]">₹{r.target}</div>
                                  </div>
                                )}
                                {r.stop_loss && (
                                  <div className="bg-[var(--bg-primary)] rounded p-2">
                                    <div className="text-[var(--text-muted)]">Stop Loss</div>
                                    <div className="font-medium text-[#ef4444]">₹{r.stop_loss}</div>
                                  </div>
                                )}
                              </div>

                              {/* Fundamentals */}
                              {r.fundamentals && (
                                <div className="bg-[var(--bg-primary)] rounded-lg p-3">
                                  <div className="text-sm font-medium mb-2 flex items-center gap-2">
                                    <Shield className="w-4 h-4 text-[var(--accent)]" /> Fundamentals
                                    {r.fundamentals.quality && <span className="text-xs bg-[#10b981]/10 text-[#10b981] px-2 py-0.5 rounded">Quality</span>}
                                    {r.fundamentals.risky && <span className="text-xs bg-[#ef4444]/10 text-[#ef4444] px-2 py-0.5 rounded">Risky</span>}
                                  </div>
                                  <div className="grid grid-cols-3 gap-2 text-sm">
                                    {r.fundamentals.pe && <div><span className="text-[var(--text-muted)]">PE:</span> {r.fundamentals.pe}</div>}
                                    {r.fundamentals.roe && <div><span className="text-[var(--text-muted)]">ROE:</span> {r.fundamentals.roe}%</div>}
                                    {r.fundamentals.debt_equity !== null && <div><span className="text-[var(--text-muted)]">D/E:</span> {r.fundamentals.debt_equity}</div>}
                                  </div>
                                </div>
                              )}

                              {/* Sector Concentration */}
                              {r.sector_concentration > 20 && (
                                <div className="flex items-center gap-2 text-sm">
                                  <Activity className="w-4 h-4 text-[var(--text-muted)]" />
                                  <span className="text-[var(--text-muted)]">{r.sector} allocation:</span>
                                  <span className={r.sector_concentration > 30 ? 'text-[#ef4444] font-medium' : 'text-[#f59e0b]'}>{r.sector_concentration}%</span>
                                </div>
                              )}

                              {/* Reasons */}
                              <div>
                                <div className="text-sm font-medium mb-2">Analysis</div>
                                <ul className="space-y-1">
                                  {r.reasons?.map((reason, j) => (
                                    <li key={j} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                                      <span className="text-[var(--accent)] mt-1">•</span> {reason}
                                    </li>
                                  ))}
                                </ul>
                              </div>

                              {/* Confidence Factors */}
                              {r.confidence_factors?.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                  {r.confidence_factors.map((f, j) => (
                                    <span key={j} className="text-xs bg-[var(--bg-primary)] border border-[var(--border)] px-2 py-1 rounded">{f}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* IPO Sidebar */}
              <div>
                <h2 className="text-sm font-medium text-[var(--text-muted)] uppercase mb-4">IPO Recommendations</h2>
                <div className="space-y-3">
                  {data.ipos?.filter(ipo => ipo.action).length === 0 ? (
                    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-8 text-center text-[var(--text-muted)]">No IPO recommendations</div>
                  ) : data.ipos?.filter(ipo => ipo.action).map((ipo, i) => (
                    <div key={i} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                        <div className="font-medium">{ipo.name}</div>
                        <span className={`text-xs font-medium px-2 py-1 rounded ${ipo.action === 'APPLY' ? 'bg-[#10b981]/10 text-[#10b981]' : ipo.action === 'AVOID' ? 'bg-[#ef4444]/10 text-[#ef4444]' : 'bg-[#eab308]/10 text-[#eab308]'}`}>{ipo.action}</span>
                      </div>
                      <div className="text-sm text-[var(--text-muted)] mb-2">{ipo.price_band} • GMP: ₹{ipo.gmp} ({ipo.gmp_pct?.toFixed(0)}%)</div>
                      <div className="text-sm text-[var(--text-secondary)]">{ipo.reasons?.[0]}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        <p className="mt-8 text-sm text-[var(--text-muted)] text-center">⚠️ Not financial advice. Signals combine technicals + fundamentals + portfolio context. Do your own research.</p>
      </main>
    </div>
  );
}
