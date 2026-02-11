'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function usePriceWebSocket(symbols = []) {
  const [prices, setPrices] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeout = useRef(null);

  const connect = useCallback(() => {
    const token = localStorage.getItem('token');
    const url = token ? `${WS_BASE}/ws/prices?token=${token}` : `${WS_BASE}/ws/prices`;
    
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      if (symbols.length > 0) {
        ws.send(JSON.stringify({ action: 'subscribe', symbols }));
      }
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'price') {
        setPrices(prev => ({ ...prev, [msg.symbol]: msg.data }));
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 3 seconds
      reconnectTimeout.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }, [symbols]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);

  // Subscribe to new symbols
  const subscribe = useCallback((newSymbols) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', symbols: newSymbols }));
    }
  }, []);

  // Unsubscribe from symbols
  const unsubscribe = useCallback((oldSymbols) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'unsubscribe', symbols: oldSymbols }));
    }
  }, []);

  return { prices, connected, subscribe, unsubscribe };
}
