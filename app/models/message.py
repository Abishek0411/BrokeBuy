from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    receiver_id: str
    listing_id: str
    message: str

class MessageResponse(BaseModel):
    sender_id: str
    receiver_id: str
    listing_id: str
    message: str
    timestamp: datetime
