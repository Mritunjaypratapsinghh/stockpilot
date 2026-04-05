from .advisor_history import AdvisorHistory

# ITR Models
from .ais_line_item import AISCategory, AISLineItem, AISMatchSource, AISStatus
from .alert import Alert
from .asset import Asset
from .base import BaseDocument
from .chat import ChatMessage, ChatSession
from .daily_digest import DailyDigest
from .dividend import Dividend
from .goal import Goal
from .holding import Holding
from .ipo import IPO
from .ledger import Ledger, LedgerStatus, LedgerType, Settlement
from .networth_history import NetworthHistory
from .notification import Notification
from .portfolio_snapshot import PortfolioSnapshot
from .price_cache import PriceCache
from .signal_history import SignalHistory
from .sip import SIP
from .tax_audit_trail import TaxAuditTrail
from .tax_profile import (
    AgeCategory,
    Deductions,
    DocumentsUploaded,
    ExemptIncome,
    FilingStatus,
    HouseProperty,
    HRADetails,
    LossCarryForward,
    OtherIncome,
    RegimeChoice,
    ReinvestmentExemptions,
    SalaryDetails,
    TaxPayment,
    TaxProfile,
)
from .tds_entry import ReconciliationStatus, TDSEntry, TDSSource
from .transaction import Transaction
from .user import User
from .vault import VaultCategory, VaultEntry, VaultNominee
from .watchlist import WatchlistItem

ALL_DOCUMENTS = [
    User,
    Holding,
    Transaction,
    Alert,
    Asset,
    WatchlistItem,
    Goal,
    SIP,
    Dividend,
    NetworthHistory,
    PortfolioSnapshot,
    Notification,
    IPO,
    SignalHistory,
    AdvisorHistory,
    DailyDigest,
    PriceCache,
    Ledger,
    VaultEntry,
    VaultNominee,
    ChatSession,
    ChatMessage,
    TaxProfile,
    AISLineItem,
    TDSEntry,
    TaxAuditTrail,
]
