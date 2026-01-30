from pydantic import Field
from .base import BaseDocument

class Notification(BaseDocument):
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    read: bool = False
    
    class Settings:
        name = "notifications"
