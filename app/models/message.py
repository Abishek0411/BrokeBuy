from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class MessageCreate(BaseModel):
    receiver_id: str
    listing_id: str
    message: str = Field(..., max_length=500, description="Message must be 500 characters or less")

class MessageResponse(BaseModel):
    sender_id: str
    receiver_id: str
    listing_id: str
    message: str
    timestamp: datetime

class OtherUser(BaseModel):
    id: str
    name: str | None
    avatar: str | None
    reg_no: str | None

class ListingPreview(BaseModel):
    id: str
    title: str
    price: float
    image: Optional[str] = None


class ChatResponse(BaseModel):
    messages: List[MessageResponse]
    other_user: OtherUser
    listing: ListingPreview  # ✅ Added tagged listing