from pydantic import BaseModel, Field
from typing import Optional

class WalletAdd(BaseModel):
    amount: float = Field(..., gt=0)
    ref_note: Optional[str] = "Wallet top-up"

class WalletResponse(BaseModel):
    balance: float
