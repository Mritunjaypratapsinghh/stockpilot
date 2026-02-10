from typing import Any, Dict, Optional

from .base import BaseDocumentNoUser


class IPO(BaseDocumentNoUser):
    name: str
    symbol: Optional[str] = None
    ipo_type: str = "MAINBOARD"
    status: str = "UPCOMING"
    price_band: Dict[str, float] = {}
    lot_size: int = 0
    gmp: float = 0
    dates: Dict[str, Any] = {}
    date_range: Optional[str] = None

    class Settings:
        name = "ipos"
