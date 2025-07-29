from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ListingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    condition: Optional[str] = None
    location: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    
class ListingResponse(ListingCreate):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    category: str
    condition : Optional[str] = None
    location: Optional[str] = None
    posted_by: str
    buyer_id: Optional[str] = None
    is_sold: bool
    created_at: datetime
    updated_at: datetime
    is_available: bool
    seller_name: Optional[str] = None
    seller_reg_no: Optional[str] = None
    images: List[str] = Field(default_factory=list)


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    images: Optional[List[str]] = None

class ListingOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    condition: Optional[str] = None
    images: List[str]
    posted_by: str
    buyer_id: Optional[str] = None
    is_sold: bool
    created_at: datetime
    updated_at: datetime