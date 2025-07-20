from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ListingCreate(BaseModel):
    title: str
    description: str
    price: float
    category: str
    images: List[str] = []

class ListingResponse(ListingCreate):
    id: str
    posted_by: str
    is_sold: bool = False
    created_at: datetime
    updated_at: datetime
