"""Chat session model for persisting conversation history."""

from pymongo import DESCENDING, IndexModel

from .base import BaseDocument


class ChatMessage(BaseDocument):
    """Individual chat message within a session."""

    session_id: str
    role: str  # "user" or "assistant"
    content: str
    suggestions: list[str] = []

    class Settings:
        name = "chat_messages"
        indexes = [
            IndexModel([("user_id", 1), ("session_id", 1), ("created_at", 1)]),
        ]


class ChatSession(BaseDocument):
    """Chat session grouping messages."""

    title: str = "New Chat"
    last_message: str = ""
    message_count: int = 0

    class Settings:
        name = "chat_sessions"
        indexes = [
            IndexModel([("user_id", 1), ("updated_at", DESCENDING)]),
        ]
