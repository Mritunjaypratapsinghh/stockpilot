from .base import BaseDocument
from .user import User
from .holding import Holding
from .transaction import Transaction
from .alert import Alert
from .asset import Asset
from .watchlist import WatchlistItem
from .goal import Goal
from .sip import SIP
from .dividend import Dividend
from .networth_history import NetworthHistory
from .portfolio_snapshot import PortfolioSnapshot
from .notification import Notification
from .ipo import IPO
from .signal_history import SignalHistory
from .advisor_history import AdvisorHistory
from .daily_digest import DailyDigest
from .price_cache import PriceCache
from .ledger import Ledger, LedgerType, LedgerStatus, Settlement

ALL_DOCUMENTS = [
    User, Holding, Transaction, Alert, Asset, WatchlistItem, Goal, SIP,
    Dividend, NetworthHistory, PortfolioSnapshot, Notification, IPO,
    SignalHistory, AdvisorHistory, DailyDigest, PriceCache, Ledger
]
