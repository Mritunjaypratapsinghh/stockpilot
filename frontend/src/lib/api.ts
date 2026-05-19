const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Request deduplication — prevents duplicate in-flight requests to the same endpoint
const _inflight = new Map();

export async function api(endpoint: string, options: any = {}) {
  const method = options.method || 'GET';

  // Only deduplicate GET requests
  const dedupeKey = method === 'GET' ? endpoint : null;
  if (dedupeKey && _inflight.has(dedupeKey)) {
    return _inflight.get(dedupeKey);
  }

  // Read CSRF token from cookie for state-changing requests
  const csrfToken = typeof document !== 'undefined'
    ? document.cookie.split('; ').find(c => c.startsWith('csrf_token='))?.split('=')[1] || ''
    : '';

  const promise = (async () => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      credentials: 'include', // Send httpOnly cookies automatically
      headers: {
        'Content-Type': 'application/json',
        ...(method !== 'GET' && csrfToken ? { 'x-csrf-token': csrfToken } : {}),
        ...options.headers,
      },
    });

    if (!res.ok) {
      if (res.status === 401 && typeof window !== 'undefined' && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/calculators')) {
        window.location.href = '/login';
        return;
      }
      const error = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }

    const json = await res.json();
    return json.data !== undefined ? json.data : json;
  })();

  if (dedupeKey) {
    _inflight.set(dedupeKey, promise);
    promise.finally(() => _inflight.delete(dedupeKey));
  }

  return promise;
}

export async function uploadFile(endpoint, file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Upload failed');
  }
  return res.json();
}

export const getPortfolio = () => api('/api/portfolio');
export const getSnapshots = (range = '3M') => api('/api/portfolio/snapshots?range=' + range);
export const getHoldings = () => api('/api/portfolio/holdings');
export const getPerformance = () => api('/api/portfolio/performance');
export const getSectors = () => api('/api/portfolio/sectors');
export const getXirr = () => api('/api/portfolio/xirr');
export const getDashboard = () => api('/api/portfolio/dashboard');
export const getTransactions = () => api('/api/portfolio/transactions');
export const addTransaction = (data) => api('/api/portfolio/transactions', { method: 'POST', body: JSON.stringify(data) });
export const deleteTransaction = (holdingId, index) => api(`/api/portfolio/transactions/${holdingId}/${index}`, { method: 'DELETE' });
export const importHoldings = (file) => uploadFile('/api/portfolio/import', file);
export const getAlerts = () => api('/api/alerts');
export const getWatchlist = () => api('/api/watchlist');
export const getIndices = () => api('/api/market/indices');
export const getMarketSummary = () => api('/api/market/summary');
export const getAnalysis = (symbol, exchange = 'NSE') => api(`/api/market/research/${symbol}?exchange=${exchange}`);
export const getNews = (symbol) => api(`/api/market/research/${symbol}/news`);
export const getNotifications = () => api('/api/alerts/notifications');
export const getDividends = () => api('/api/finance/dividends');
export const addDividend = (data) => api('/api/finance/dividends', { method: 'POST', body: JSON.stringify(data) });
export const deleteDividend = (id) => api(`/api/finance/dividends/${id}`, { method: 'DELETE' });

export const downloadExport = async (type) => {
  const res = await fetch(`${API_BASE}/api/export/${type}/csv`, { credentials: 'include' });
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
  return api(`/api/ledger${query ? `?${query}` : ''}`);
};
export const getLedgerSummary = () => api('/api/ledger/summary');
export const addLedgerEntry = (data) => api('/api/ledger', { method: 'POST', body: JSON.stringify(data) });
export const updateLedgerEntry = (id, data) => api(`/api/ledger/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const settleLedgerEntry = (id, data) => api(`/api/ledger/${id}/settle`, { method: 'POST', body: JSON.stringify(data) });
export const deleteLedgerEntry = (id) => api(`/api/ledger/${id}`, { method: 'DELETE' });

// Vault
export const getVaultEntries = (category) => api(`/api/vault/entries${category ? `?category=${category}` : ''}`);
export const createVaultEntry = (data) => api('/api/vault/entries', { method: 'POST', body: JSON.stringify(data) });
export const updateVaultEntry = (id, data) => api(`/api/vault/entries/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteVaultEntry = (id) => api(`/api/vault/entries/${id}`, { method: 'DELETE' });
export const getVaultNominees = () => api('/api/vault/nominees');
export const addVaultNominee = (data) => api('/api/vault/nominees', { method: 'POST', body: JSON.stringify(data) });
export const removeVaultNominee = (id) => api(`/api/vault/nominees/${id}`, { method: 'DELETE' });
export const getSharedVaults = () => api('/api/vault/shared');
export const viewSharedVault = (email) => api(`/api/vault/shared/${encodeURIComponent(email)}`);
export const acceptVaultInvite = (token) => api(`/api/vault/accept-invite?token=${token}`, { method: 'POST' });
export const uploadVaultFile = (entryId, file) => uploadFile(`/api/vault/entries/${entryId}/upload`, file);
export const deleteVaultFile = (entryId, filename) => api(`/api/vault/entries/${entryId}/files/${filename}`, { method: 'DELETE' });
export const getVaultFileUrl = (filename) => `${API_BASE}/api/vault/files/${filename}`;

// Auth
export const logout = () => api('/api/auth/logout', { method: 'POST' });
