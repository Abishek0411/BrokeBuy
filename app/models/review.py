from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewCreate(BaseModel):
    listing_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    comment: str = Field(..., max_length=500, description="Comment must be 500 characters or less")

class ReviewResponse(BaseModel):
    id: str
    listing_id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_reg_no: str
    rating: int
    comment: str
    created_at: datetime
    is_verified: bool = False  # True if reviewer actually purchased the item

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = Field(None, max_length=500, description="Comment must be 500 characters or less")
