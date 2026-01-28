'use client';
import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';
import Link from 'next/link';
import Navbar from '../../components/Navbar';
import { api } from '../../lib/api';

function StockContent() {
  const searchParams = useSearchParams();
  const symbol = searchParams.get('s') || '';
  const [data, setData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [enhanced, setEnhanced] = useState(null);
  const [news, setNews] = useState([]);
  const [range, setRange] = useState('6mo');
  const [loading, setLoading] = useState(true);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (symbol) loadData();
  }, [symbol, range]);

  const loadData = async () => {
    setLoading(true);
    try {
      const exchange = searchParams.get('exchange') || 'NSE';
      const [chartData, analysisData, enhancedData, newsData] = await Promise.all([
        api(`/api/research/chart/${symbol}?range=${range}`),
        api(`/api/research/analysis/${symbol}?exchange=${exchange}`),
        api(`/api/research/enhanced/${symbol}?exchange=${exchange}`).catch(() => null),
        api(`/api/research/news/${symbol}`)
      ]);
      setData(chartData);
      setAnalysis(analysisData);
      setEnhanced(enhancedData);
      setNews(newsData.news || []);
      
      if (chartData.candles?.length > 0) {
        renderChart(chartData.candles);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const renderChart = async (candles) => {
    if (!chartRef.current || typeof window === 'undefined') return;
    
    const { createChart } = await import('lightweight-charts');
    
    if (chartInstance.current) {
      chartInstance.current.remove();
    }

    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: 'transparent' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#2a2a2a' },
      timeScale: { borderColor: '#2a2a2a', timeVisible: true },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    candleSeries.setData(candles);
    chart.timeScale().fitContent();
    chartInstance.current = chart;

    const handleResize = () => {
      if (chartRef.current) {
        chart.applyOptions({ width: chartRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  };

  const fmt = (n) => n?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '-';

  if (!symbol) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Navbar />
        <main className="p-6 text-center py-20">
          <p className="text-[var(--text-muted)]">No symbol specified</p>
          <Link href="/portfolio" className="text-[var(--accent)] hover:underline">Go to Portfolio</Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Link href="/portfolio" className="p-2 hover:bg-[var(--bg-secondary)] rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{symbol}</h1>
            {data?.name && <p className="text-[var(--text-muted)]">{data.name}</p>}
          </div>
          {analysis && (
            <div className="ml-auto text-right">
              <div className="text-3xl font-bold tabular">₹{fmt(analysis.current_price)}</div>
              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm font-medium ${analysis.trend === 'BULLISH' ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>
                {analysis.trend === 'BULLISH' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {analysis.trend}
              </span>
            </div>
          )}
        </div>

        {/* Chart */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6">
          <div className="flex gap-2 mb-4">
            {['1mo', '3mo', '6mo', '1y', '2y'].map(r => (
              <button key={r} onClick={() => setRange(r)} className={`px-3 py-1 rounded text-sm ${range === r ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'}`}>
                {r.toUpperCase()}
              </button>
            ))}
          </div>
          <div ref={chartRef} className="w-full" style={{ height: 400 }}>
            {loading && <div className="h-full flex items-center justify-center text-[var(--text-muted)]">Loading chart...</div>}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Technical Indicators */}
          <div className="lg:col-span-2 space-y-4">
            {/* Enhanced Analysis Card */}
            {enhanced && (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold">Enhanced Analysis</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    enhanced.recommendation === 'STRONG_BUY' ? 'bg-[#10b981]/20 text-[#10b981]' :
                    enhanced.recommendation === 'BUY' ? 'bg-[#10b981]/10 text-[#10b981]' :
                    enhanced.recommendation === 'HOLD' ? 'bg-[#f59e0b]/10 text-[#f59e0b]' :
                    'bg-[#ef4444]/10 text-[#ef4444]'
                  }`}>
                    {enhanced.recommendation?.replace('_', ' ')}
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {enhanced.pe_ratio && (
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">P/E Ratio</div>
                      <div className="text-xl font-bold">{enhanced.pe_ratio}</div>
                    </div>
                  )}
                  {enhanced.roe && (
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">ROE</div>
                      <div className="text-xl font-bold">{enhanced.roe}%</div>
                    </div>
                  )}
                  {enhanced.roce && (
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">ROCE</div>
                      <div className="text-xl font-bold">{enhanced.roce}%</div>
                    </div>
                  )}
                  {enhanced.market_cap && (
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">Market Cap</div>
                      <div className="text-lg font-bold">₹{enhanced.market_cap} Cr</div>
                    </div>
                  )}
                </div>
                {enhanced.sources?.nse && (
                  <div className="mt-4 pt-4 border-t border-[var(--border)]">
                    <div className="text-sm text-[var(--text-muted)] mb-2">NSE Data</div>
                    <div className="grid grid-cols-3 gap-4">
                      {enhanced.sources.nse.vwap && (
                        <div>
                          <div className="text-xs text-[var(--text-muted)]">VWAP</div>
                          <div className="font-medium">₹{fmt(enhanced.sources.nse.vwap)}</div>
                        </div>
                      )}
                      {enhanced.sources.nse.delivery_pct && (
                        <div>
                          <div className="text-xs text-[var(--text-muted)]">Delivery %</div>
                          <div className={`font-medium ${enhanced.sources.nse.delivery_pct > 60 ? 'text-[#10b981]' : ''}`}>
                            {fmt(enhanced.sources.nse.delivery_pct)}%
                          </div>
                        </div>
                      )}
                      {enhanced.sources.nse.volume && (
                        <div>
                          <div className="text-xs text-[var(--text-muted)]">Volume</div>
                          <div className="font-medium">{(enhanced.sources.nse.volume / 1000).toFixed(0)}K</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                <div className="mt-3 text-xs text-[var(--text-muted)]">
                  Data Quality: {enhanced.data_quality}
                </div>
              </div>
            )}

            {analysis && !analysis.error && (
              <>
                <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
                  <h3 className="font-semibold mb-4">Technical Indicators</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">RSI (14)</div>
                      <div className={`text-xl font-bold ${analysis.rsi < 30 ? 'text-[#10b981]' : analysis.rsi > 70 ? 'text-[#ef4444]' : ''}`}>{analysis.rsi}</div>
                      <div className="text-xs text-[var(--text-muted)]">{analysis.rsi_signal}</div>
                    </div>
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">SMA 20</div>
                      <div className="text-xl font-bold">₹{fmt(analysis.sma_20)}</div>
                      <div className={`text-xs ${analysis.current_price > analysis.sma_20 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                        {analysis.current_price > analysis.sma_20 ? 'Above' : 'Below'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">Support</div>
                      <div className="text-xl font-bold text-[#10b981]">₹{fmt(analysis.support)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-[var(--text-muted)]">Resistance</div>
                      <div className="text-xl font-bold text-[#ef4444]">₹{fmt(analysis.resistance)}</div>
                    </div>
                  </div>
                </div>

                {analysis.sma_50 && (
                  <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5">
                    <h3 className="font-semibold mb-4">Moving Averages</h3>
                    <div className="space-y-3">
                      {[['SMA 20', analysis.sma_20], ['SMA 50', analysis.sma_50], ['SMA 200', analysis.sma_200]].map(([label, value]) => value && (
                        <div key={label} className="flex items-center justify-between">
                          <span className="text-[var(--text-muted)]">{label}</span>
                          <div className="flex items-center gap-3">
                            <span className="font-medium tabular">₹{fmt(value)}</span>
                            <span className={`px-2 py-0.5 rounded text-xs ${analysis.current_price > value ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#ef4444]/10 text-[#ef4444]'}`}>
                              {analysis.current_price > value ? 'Above' : 'Below'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* News */}
          <div>
            {news.length > 0 && (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg overflow-hidden">
                <div className="px-5 py-4 border-b border-[var(--border)] font-semibold">Latest News</div>
                <div className="divide-y divide-[var(--border)]">
                  {news.slice(0, 5).map((n, i) => (
                    <a key={i} href={n.link} target="_blank" rel="noopener" className="block px-5 py-3 hover:bg-[var(--bg-tertiary)]">
                      <div className="font-medium text-sm line-clamp-2 mb-1">{n.title}</div>
                      <div className="text-xs text-[var(--text-muted)]">{n.publisher}</div>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function StockPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><main className="p-6 text-center py-20"><p className="text-[var(--text-muted)]">Loading...</p></main></div>}>
      <StockContent />
    </Suspense>
  );
}
