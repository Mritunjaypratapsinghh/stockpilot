# from beanie import Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional
from .base import BaseDocumentNoUser

class IPO(BaseDocumentNoUser):
    symbol: str
    name: str
    
    class Settings:
        name = "ipos"
