import asyncio
import json
from typing import Dict, Set

from fastapi import WebSocket

from ..utils.logger import logger


class ConnectionManager:
    """Manages WebSocket connections with Redis Pub/Sub for multi-instance scaling."""

    CHANNEL = "ws:prices"

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._subscriptions: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._pubsub_task = None

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)
        # Start Redis subscriber on first connection
        if self._pubsub_task is None:
            self._pubsub_task = asyncio.create_task(self._redis_subscriber())
        logger.info(f"WebSocket connected: {user_id}")

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
                    for symbol in list(self._subscriptions.keys()):
                        self._subscriptions[symbol].discard(user_id)
                        if not self._subscriptions[symbol]:
                            del self._subscriptions[symbol]
        logger.info(f"WebSocket disconnected: {user_id}")

    async def subscribe(self, user_id: str, symbols: list[str]) -> None:
        async with self._lock:
            for symbol in symbols:
                if symbol not in self._subscriptions:
                    self._subscriptions[symbol] = set()
                self._subscriptions[symbol].add(user_id)

    async def unsubscribe(self, user_id: str, symbols: list[str]) -> None:
        async with self._lock:
            for symbol in symbols:
                if symbol in self._subscriptions:
                    self._subscriptions[symbol].discard(user_id)
                    if not self._subscriptions[symbol]:
                        del self._subscriptions[symbol]

    async def broadcast_price(self, symbol: str, data: dict) -> None:
        """Publish price update to Redis — all instances will receive it."""
        try:
            from .cache import get_redis

            r = await get_redis()
            await r.publish(self.CHANNEL, json.dumps({"symbol": symbol, "data": data}))
        except Exception:
            # Fallback: broadcast locally if Redis unavailable
            await self._local_broadcast(symbol, data)

    async def _local_broadcast(self, symbol: str, data: dict) -> None:
        """Broadcast to local connections only."""
        async with self._lock:
            user_ids = self._subscriptions.get(symbol, set()).copy()
        for user_id in user_ids:
            await self._send_to_user(user_id, {"type": "price", "symbol": symbol, "data": data})

    async def _redis_subscriber(self) -> None:
        """Listen for price updates from Redis and broadcast to local connections."""
        try:
            from .cache import get_redis

            r = await get_redis()
            pubsub = r.pubsub()
            await pubsub.subscribe(self.CHANNEL)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    await self._local_broadcast(payload["symbol"], payload["data"])
        except Exception as e:
            logger.warning(f"Redis PubSub subscriber error: {e}")
            self._pubsub_task = None

    async def _send_to_user(self, user_id: str, message: dict) -> None:
        async with self._lock:
            websockets = self._connections.get(user_id, set()).copy()
        for ws in websockets:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    def get_subscribed_symbols(self) -> list[str]:
        return list(self._subscriptions.keys())

    def get_connection_count(self) -> int:
        return sum(len(ws) for ws in self._connections.values())


ws_manager = ConnectionManager()
