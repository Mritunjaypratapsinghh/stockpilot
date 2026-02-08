"""Compatibility shim - re-exports from core.database"""
from .core.database import init_db as connect_db, close_db, get_database as get_db

__all__ = ["connect_db", "close_db", "get_db"]
