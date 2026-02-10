import asyncio
from typing import Dict, Set

from fastapi import WebSocket

from ..utils.logger import logger


class ConnectionManager:
    """Manages WebSocket connections for real-time price updates."""

    def __init__(self):
        # user_id -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        # symbol -> set of user_ids subscribed
        self._subscriptions: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: {user_id}")

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
                    # Clean up subscriptions
                    for symbol in list(self._subscriptions.keys()):
                        self._subscriptions[symbol].discard(user_id)
                        if not self._subscriptions[symbol]:
                            del self._subscriptions[symbol]
        logger.info(f"WebSocket disconnected: {user_id}")

    async def subscribe(self, user_id: str, symbols: list[str]) -> None:
        """Subscribe user to price updates for symbols."""
        async with self._lock:
            for symbol in symbols:
                if symbol not in self._subscriptions:
                    self._subscriptions[symbol] = set()
                self._subscriptions[symbol].add(user_id)

    async def unsubscribe(self, user_id: str, symbols: list[str]) -> None:
        """Unsubscribe user from price updates."""
        async with self._lock:
            for symbol in symbols:
                if symbol in self._subscriptions:
                    self._subscriptions[symbol].discard(user_id)
                    if not self._subscriptions[symbol]:
                        del self._subscriptions[symbol]

    async def broadcast_price(self, symbol: str, data: dict) -> None:
        """Broadcast price update to all subscribed users."""
        async with self._lock:
            user_ids = self._subscriptions.get(symbol, set()).copy()

        for user_id in user_ids:
            await self._send_to_user(user_id, {"type": "price", "symbol": symbol, "data": data})

    async def _send_to_user(self, user_id: str, message: dict) -> None:
        """Send message to all connections of a user."""
        async with self._lock:
            websockets = self._connections.get(user_id, set()).copy()

        for ws in websockets:
            try:
                await ws.send_json(message)
            except Exception:
                # Connection likely closed, will be cleaned up
                pass

    def get_subscribed_symbols(self) -> list[str]:
        """Get all symbols with active subscriptions."""
        return list(self._subscriptions.keys())

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(ws) for ws in self._connections.values())


# Global instance
ws_manager = ConnectionManager()
