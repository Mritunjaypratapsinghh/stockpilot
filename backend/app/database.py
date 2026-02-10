"""Compatibility shim - re-exports from core.database"""

from .core.database import close_db
from .core.database import get_database as get_db
from .core.database import init_db as connect_db

__all__ = ["connect_db", "close_db", "get_db"]
