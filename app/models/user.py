from pydantic import BaseModel, EmailStr
from typing import Optional, Union

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatar_url: Optional[str]
    role: str
    wallet_balance: float

class UserUpdate(BaseModel):
    name: Optional[str]
    avatar_url: Optional[str]

class TokenUser(BaseModel):
    _id: Union[str, None] = None  # MongoDB ID as string
    id: Optional[str] = None  # Optional, fallback
    name: str
    email: EmailStr
    role: str
    avatar_url: Optional[str] = None
    wallet_balance: Optional[float] = 0.0
