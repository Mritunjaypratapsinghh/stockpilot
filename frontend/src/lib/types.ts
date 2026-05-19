/**
 * API response types for StockPilot.
 * Used to type API responses and remove @ts-nocheck from pages.
 */

// ── Auth ──
export interface User {
  id: string;
  email: string;
  settings: Record<string, any>;
  telegram_chat_id: string;
  is_pro: boolean;
}

// ── Portfolio ──
export interface Holding {
  _id: string;
  symbol: string;
  name: string;
  holding_type: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  day_change_pct: number;
  current_value: number;
  total_investment: number;
  pnl: number;
  pnl_pct: number;
  sector?: string;
}

export interface PortfolioSummary {
  total_investment: number;
  current_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  day_pnl: number;
  day_pnl_pct: number;
  holdings_count: number;
}

export interface Transaction {
  symbol: string;
  holding_id: string;
  index: number;
  type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  date: string;
  notes?: string;
}

export interface SectorAllocation {
  sector: string;
  value: number;
  percentage: number;
}

// ── Analytics ──
export interface HealthScore {
  score: number;
  grade: string;
  factors: { name: string; score: number; weight: number }[];
}

export interface Insight {
  type: string;
  title: string;
  description: string;
  action?: string;
}

// ── Market ──
export interface MarketIndex {
  symbol: string;
  name: string;
  value: number;
  change: number;
  change_pct: number;
}

export interface StockQuote {
  symbol: string;
  name: string;
  current_price: number;
  previous_close: number;
  day_change: number;
  day_change_pct: number;
  day_high: number;
  day_low: number;
  volume: number;
}

// ── Finance ──
export interface Goal {
  _id: string;
  name: string;
  category: string;
  target_amount: number;
  current_value: number;
  target_date: string;
  progress: number;
  required_sip: number;
}

export interface SIP {
  _id: string;
  fund_name: string;
  amount: number;
  frequency: string;
  start_date: string;
  is_active: boolean;
}

export interface Alert {
  _id: string;
  symbol: string;
  alert_type: string;
  target_value: number;
  is_active: boolean;
  triggered: boolean;
}

// ── Dashboard ──
export interface DashboardData {
  holdings: Holding[];
  sectors: SectorAllocation[];
  xirr: number | null;
  transactions: Transaction[];
  summary: {
    invested: number;
    current: number;
    pnl: number;
    pnl_pct: number;
  };
}

// ── Notifications ──
export interface Notification {
  _id: string;
  title: string;
  message: string;
  type: string;
  read: boolean;
  created_at: string;
}
