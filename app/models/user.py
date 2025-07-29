from pydantic import BaseModel, EmailStr
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
