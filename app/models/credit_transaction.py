from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class CreditTransactionType(str, Enum):
    AUTO_REFILL = "auto_refill"
    MANUAL_TOPUP = "manual_topup"
    SALE_PROCEEDS = "sale_proceeds"
    REFUND = "refund"
    ADMIN_CREDIT = "admin_credit"

class CreditTransactionCreate(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0, description="Amount must be positive")
    transaction_type: CreditTransactionType
    reference_id: Optional[str] = None  # Reference to listing, purchase request, etc.
    description: Optional[str] = None
    is_auto_refill: bool = False

class CreditTransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    transaction_type: CreditTransactionType
    reference_id: Optional[str]
    description: Optional[str]
    is_auto_refill: bool
    created_at: datetime
    previous_balance: float
    new_balance: float

class CreditTransactionSummary(BaseModel):
    total_credits: float
    auto_refills: int
    manual_topups: int
    sale_proceeds: float
    total_transactions: int
    period_start: datetime
    period_end: datetime
