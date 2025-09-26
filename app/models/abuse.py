from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class AbuseType(str, Enum):
    SPAM = "spam"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    FRAUD = "fraud"
    HARASSMENT = "harassment"
    FAKE_LISTING = "fake_listing"
    OTHER = "other"

class AbuseReportCreate(BaseModel):
    target_type: str = Field(..., description="Type of content being reported (listing, message, user)")
    target_id: str = Field(..., description="ID of the content being reported")
    abuse_type: AbuseType = Field(..., description="Type of abuse")
    description: str = Field(..., max_length=500, description="Description of the abuse")
    evidence_urls: Optional[List[str]] = Field(None, description="URLs to evidence (screenshots, etc.)")

class AbuseReportResponse(BaseModel):
    id: str
    reporter_id: str
    target_type: str
    target_id: str
    abuse_type: AbuseType
    description: str
    evidence_urls: Optional[List[str]]
    status: str = "pending"
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    admin_notes: Optional[str] = None

class AbuseReportUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Status: pending, reviewed, dismissed, action_taken")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Admin notes about the report")
