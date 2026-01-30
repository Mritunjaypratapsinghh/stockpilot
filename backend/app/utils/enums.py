from enum import Enum


class HoldingType(str, Enum):
    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class AlertType(str, Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    ALERT = "alert"
    SIGNAL = "signal"
    DIVIDEND = "dividend"
    PORTFOLIO = "portfolio"


class SIPFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
