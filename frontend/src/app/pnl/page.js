'use client';
import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';
import { api } from '../../lib/api';
import Navbar from '../../components/Navbar';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function PnLCalendarPage() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [data, setData] = useState(null);
  const [monthly, setMonthly] = useState(null);
  const [view, setView] = useState('calendar');
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [daily, monthlyData] = await Promise.all([
        api(`/api/pnl/daily?year=${year}&month=${month}`),
        api(`/api/pnl/monthly?year=${year}`)
      ]);
      setData(daily);
      setMonthly(monthlyData);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [year, month]);

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else setMonth(month - 1);
  };

  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else setMonth(month + 1);
  };

  const getDaysInMonth = (y, m) => new Date(y, m, 0).getDate();
  const getFirstDayOfMonth = (y, m) => new Date(y, m - 1, 1).getDay();

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const days = [];

    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-20"></div>);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayData = data?.calendar?.[dateStr];
      const pnl = dayData?.pnl || 0;
      const isPositive = pnl > 0;
      const isNegative = pnl < 0;

      days.push(
        <div key={day} className={`h-20 p-2 border border-[var(--border)] rounded-lg ${isPositive ? 'bg-[#22c55e]/10' : isNegative ? 'bg-[#ef4444]/10' : 'bg-[var(--bg-secondary)]'}`}>
          <div className="text-sm text-[var(--text-secondary)]">{day}</div>
          {dayData && (
            <div className={`text-sm font-medium mt-1 ${isPositive ? 'text-[#22c55e]' : isNegative ? 'text-[#ef4444]' : 'text-[var(--text-secondary)]'}`}>
              {isPositive ? '+' : ''}{pnl.toLocaleString('en-IN')}
            </div>
          )}
          {dayData?.transactions?.length > 0 && (
            <div className="text-xs text-[#6366f1] mt-1">{dayData.transactions.length} txn</div>
          )}
        </div>
      );
    }

    return days;
  };

  if (loading) return <div className="min-h-screen bg-[var(--bg-primary)]"><Navbar /><div className="p-6">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <main className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">P&L Calendar</h1>
            <p className="text-[var(--text-secondary)]">Track your daily and monthly profit & loss</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setView('calendar')} className={`px-4 py-2 rounded-lg text-sm ${view === 'calendar' ? 'bg-[#6366f1] text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}`}>Calendar</button>
            <button onClick={() => setView('monthly')} className={`px-4 py-2 rounded-lg text-sm ${view === 'monthly' ? 'bg-[#6366f1] text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}`}>Monthly</button>
          </div>
        </div>

        {/* Monthly Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
            <div className="text-sm text-[var(--text-secondary)]">Monthly P&L</div>
            <div className={`text-xl font-bold ${(data?.monthly_pnl || 0) >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
              {(data?.monthly_pnl || 0) >= 0 ? '+' : ''}₹{(data?.monthly_pnl || 0).toLocaleString('en-IN')}
            </div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
            <div className="text-sm text-[var(--text-secondary)]">Trading Days</div>
            <div className="text-xl font-bold text-[var(--text-primary)]">{data?.trading_days || 0}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
            <div className="text-sm text-[var(--text-secondary)]">Yearly P&L</div>
            <div className={`text-xl font-bold ${(monthly?.yearly_pnl || 0) >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
              {(monthly?.yearly_pnl || 0) >= 0 ? '+' : ''}₹{(monthly?.yearly_pnl || 0).toLocaleString('en-IN')}
            </div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-xl p-4 border border-[var(--border)]">
            <div className="text-sm text-[var(--text-secondary)]">Best Month</div>
            <div className="text-xl font-bold text-[#22c55e]">
              {monthly?.monthly?.reduce((best, m) => m.pnl > best.pnl ? m : best, { pnl: -Infinity, month_name: '-' })?.month_name || '-'}
            </div>
          </div>
        </div>

        {view === 'calendar' ? (
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-6">
              <button onClick={prevMonth} className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg">
                <ChevronLeft className="w-5 h-5 text-[var(--text-secondary)]" />
              </button>
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">{MONTHS[month - 1]} {year}</h2>
              <button onClick={nextMonth} className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg">
                <ChevronRight className="w-5 h-5 text-[var(--text-secondary)]" />
              </button>
            </div>

            {/* Day Headers */}
            <div className="grid grid-cols-7 gap-2 mb-2">
              {DAYS.map(day => (
                <div key={day} className="text-center text-sm font-medium text-[var(--text-secondary)]">{day}</div>
              ))}
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 gap-2">
              {renderCalendar()}
            </div>

            <div className="flex items-center gap-6 mt-4 text-sm text-[var(--text-secondary)]">
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-[#22c55e]/30"></div>Profit</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-[#ef4444]/30"></div>Loss</div>
            </div>
          </div>
        ) : (
          <div className="bg-[var(--bg-secondary)] rounded-xl p-6 border border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Monthly P&L - {year}</h2>
            <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {monthly?.monthly?.map((m) => (
                <div key={m.month} className={`p-4 rounded-lg border ${m.pnl >= 0 ? 'border-[#22c55e]/30 bg-[#22c55e]/5' : 'border-[#ef4444]/30 bg-[#ef4444]/5'}`}>
                  <div className="text-sm text-[var(--text-secondary)]">{m.month_name}</div>
                  <div className={`text-lg font-bold ${m.pnl >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                    {m.pnl >= 0 ? '+' : ''}₹{m.pnl.toLocaleString('en-IN')}
                  </div>
                  <div className={`text-xs ${m.pnl_pct >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                    {m.pnl_pct >= 0 ? '+' : ''}{m.pnl_pct}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
