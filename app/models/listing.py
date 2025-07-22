from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ListingCreate(BaseModel):
    title: str
    description: str
    price: float
    category: str
    images: List[str] = Field(default_factory=list)
    
class ListingResponse(ListingCreate):
    id: str
    posted_by: str
    is_sold: bool = False
    created_at: datetime
    updated_at: datetime

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    images: Optional[List[str]] = None

class ListingOut(BaseModel):
    id: str
    title: str
    description: str
    price: float
    category: str
    images: List[str]
    posted_by: str
    buyer_id: Optional[str] = None
    is_sold: bool
    created_at: datetime
    updated_at: datetime