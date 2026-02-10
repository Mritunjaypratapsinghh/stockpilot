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
    if (res.status === 401 && typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      localStorage.removeItem('token');
      window.location.href = '/login';
      return;
    }
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }

  const json = await res.json();
  // Auto-extract data from StandardResponse format
  return json.data !== undefined ? json.data : json;
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
export const getTransactions = () => api('/api/portfolio/transactions');
export const addTransaction = (data) => api('/api/portfolio/transactions', { method: 'POST', body: JSON.stringify(data) });
export const deleteTransaction = (holdingId, index) => api(`/api/portfolio/transactions/${holdingId}/${index}`, { method: 'DELETE' });
export const getTransactionsList = () => api('/api/portfolio/transactions');
export const importHoldings = (file) => uploadFile('/api/portfolio/import', file);
export const getAlerts = () => api('/api/alerts');
export const getWatchlist = () => api('/api/watchlist');
export const getIndices = () => api('/api/market/indices');
export const getMarketSummary = () => api('/api/market/summary');
export const getAnalysis = (symbol, exchange = 'NSE') => api(`/api/market/research/${symbol}?exchange=${exchange}`);
export const getEnhancedAnalysis = (symbol, exchange = 'NSE') => api(`/api/market/research/${symbol}?exchange=${exchange}`);
export const getNews = (symbol) => api(`/api/market/research/${symbol}/news`);
export const getNotifications = () => api('/api/alerts/notifications');
export const getDividends = () => api('/api/finance/dividends');
export const addDividend = (data) => api('/api/finance/dividends', { method: 'POST', body: JSON.stringify(data) });
export const deleteDividend = (id) => api(`/api/finance/dividends/${id}`, { method: 'DELETE' });

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


// Ledger
export const getLedger = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return api(`/api/v1/ledger${query ? `?${query}` : ''}`);
};
export const getLedgerSummary = () => api('/api/v1/ledger/summary');
export const addLedgerEntry = (data) => api('/api/v1/ledger', { method: 'POST', body: JSON.stringify(data) });
export const updateLedgerEntry = (id, data) => api(`/api/v1/ledger/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const settleLedgerEntry = (id, data) => api(`/api/v1/ledger/${id}/settle`, { method: 'POST', body: JSON.stringify(data) });
export const deleteLedgerEntry = (id) => api(`/api/v1/ledger/${id}`, { method: 'DELETE' });
