const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function api(endpoint, options = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
      return;
    }
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }

  return res.json();
}

export async function uploadFile(endpoint, file) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { ...(token && { Authorization: `Bearer ${token}` }) },
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Upload failed');
  }
  return res.json();
}

export const getPortfolio = () => api('/api/portfolio');
export const getHoldings = () => api('/api/portfolio/holdings');
export const getPerformance = () => api('/api/portfolio/performance');
export const getSectors = () => api('/api/portfolio/sectors');
export const getXirr = () => api('/api/portfolio/xirr');
export const getDashboard = () => api('/api/portfolio/dashboard');
export const getTransactions = () => api('/api/transactions');
export const addTransaction = (data) => api('/api/transactions/', { method: 'POST', body: JSON.stringify(data) });
export const importHoldings = (file) => uploadFile('/api/portfolio/import', file);
export const getAlerts = () => api('/api/alerts');
export const getWatchlist = () => api('/api/watchlist');
export const getIndices = () => api('/api/market/indices');
export const getMarketSummary = () => api('/api/research/market-summary');
export const getAnalysis = (symbol, exchange = 'NSE') => api(`/api/research/analysis/${symbol}?exchange=${exchange}`);
export const getEnhancedAnalysis = (symbol, exchange = 'NSE') => api(`/api/research/enhanced/${symbol}?exchange=${exchange}`);
export const getNews = (symbol) => api(`/api/research/news/${symbol}`);
export const getNotifications = () => api('/api/notifications');
export const getDividends = () => api('/api/dividends');
export const getDividendSummary = () => api('/api/dividends/summary');
export const addDividend = (data) => api('/api/dividends', { method: 'POST', body: JSON.stringify(data) });
export const deleteDividend = (id) => api(`/api/dividends/${id}`, { method: 'DELETE' });

export const downloadExport = async (type) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const res = await fetch(`${API_BASE}/api/export/${type}/csv`, {
    headers: { ...(token && { Authorization: `Bearer ${token}` }) },
  });
  if (!res.ok) throw new Error('Export failed');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${type}_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
};
