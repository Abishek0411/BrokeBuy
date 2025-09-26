from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Union

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    srm_id: Optional[str]
    name: Optional[str]
    reg_no: Optional[str]
    phone: Optional[str]
    avatar: Optional[str]
    wallet_balance: float = 0.0
    role: str

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50, description="Name must be 50 characters or less")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL must be 500 characters or less")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            # Basic validation for name
            if len(v.strip()) < 2:
                raise ValueError('Name must be at least 2 characters long')
            if len(v.strip()) > 50:
                raise ValueError('Name must be 50 characters or less')
        return v

class TokenUser(BaseModel):
    _id: Union[str, None] = None  # MongoDB ID as string
    id: Optional[str] = None  # Optional, fallback
    name: str
    email: EmailStr
    role: str
    avatar_url: Optional[str] = None
    wallet_balance: Optional[float] = 0.0
