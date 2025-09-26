from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.credit_transaction import CreditTransactionResponse, CreditTransactionSummary
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.utils.wallet_auto_refill import WalletAutoRefill
from app.database import db
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from typing import List, Optional

router = APIRouter(prefix="/credit-transactions", tags=["Credit Transactions"])

@router.get("/my-transactions", response_model=List[CreditTransactionResponse])
async def get_my_credit_transactions(
    user: TokenUser = Depends(get_current_user),
    page: int = 1,
    limit: int = 50,
    transaction_type: Optional[str] = None
):
    """Get credit transactions for the current user"""
    
    # Build query
    query = {"user_id": ObjectId(user.id)}
    if transaction_type:
        query["transaction_type"] = transaction_type
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get transactions
    transactions_cursor = db.credit_transactions.find(query).sort("created_at", -1).skip(skip).limit(limit)
    transactions = await transactions_cursor.to_list(length=limit)
    
    result = []
    for transaction in transactions:
        result.append(CreditTransactionResponse(
            id=str(transaction["_id"]),
            user_id=str(transaction["user_id"]),
            amount=transaction["amount"],
            transaction_type=transaction["transaction_type"],
            reference_id=transaction.get("reference_id"),
            description=transaction.get("description"),
            is_auto_refill=transaction.get("is_auto_refill", False),
            created_at=transaction["created_at"],
            previous_balance=transaction.get("previous_balance", 0.0),
            new_balance=transaction.get("new_balance", 0.0)
        ))
    
    return result

@router.get("/summary", response_model=CreditTransactionSummary)
async def get_credit_transaction_summary(
    user: TokenUser = Depends(get_current_user),
    days: int = 30
):
    """Get credit transaction summary for the current user"""
    
    summary = await WalletAutoRefill.get_credit_transaction_summary(user.id, days)
    
    return CreditTransactionSummary(**summary)

@router.get("/admin/all-transactions", response_model=List[CreditTransactionResponse])
async def get_all_credit_transactions(
    user: TokenUser = Depends(get_current_user),
    page: int = 1,
    limit: int = 100,
    user_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    days: int = 30
):
    """Get all credit transactions (admin only)"""
    
    # Check if user is admin
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Build query
    query = {}
    if user_id:
        query["user_id"] = ObjectId(user_id)
    if transaction_type:
        query["transaction_type"] = transaction_type
    
    # Add date filter
    cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - \
                 timedelta(days=days)
    query["created_at"] = {"$gte": cutoff_date}
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get transactions
    transactions_cursor = db.credit_transactions.find(query).sort("created_at", -1).skip(skip).limit(limit)
    transactions = await transactions_cursor.to_list(length=limit)
    
    result = []
    for transaction in transactions:
        result.append(CreditTransactionResponse(
            id=str(transaction["_id"]),
            user_id=str(transaction["user_id"]),
            amount=transaction["amount"],
            transaction_type=transaction["transaction_type"],
            reference_id=transaction.get("reference_id"),
            description=transaction.get("description"),
            is_auto_refill=transaction.get("is_auto_refill", False),
            created_at=transaction["created_at"],
            previous_balance=transaction.get("previous_balance", 0.0),
            new_balance=transaction.get("new_balance", 0.0)
        ))
    
    return result

@router.get("/admin/summary", response_model=CreditTransactionSummary)
async def get_admin_credit_summary(
    user: TokenUser = Depends(get_current_user),
    days: int = 30
):
    """Get credit transaction summary for all users (admin only)"""
    
    # Check if user is admin
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    summary = await WalletAutoRefill.get_credit_transaction_summary(None, days)
    
    return CreditTransactionSummary(**summary)

@router.post("/check-auto-refill")
async def check_auto_refill(user: TokenUser = Depends(get_current_user)):
    """Check if wallet needs auto-refill and perform it if necessary"""
    
    was_refilled, message, new_balance = await WalletAutoRefill.check_and_refill_wallet(user.id)
    
    return {
        "was_refilled": was_refilled,
        "message": message,
        "new_balance": new_balance
    }

@router.get("/money-flow-stats")
async def get_money_flow_stats(
    user: TokenUser = Depends(get_current_user),
    days: int = 30
):
    """Get detailed money flow statistics (admin only)"""
    
    # Check if user is admin
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - \
                 timedelta(days=days)
    
    # Get detailed statistics
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {
            "$group": {
                "_id": "$transaction_type",
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$amount"},
                "avg_amount": {"$avg": "$amount"}
            }
        },
        {"$sort": {"total_amount": -1}}
    ]
    
    stats = await db.credit_transactions.aggregate(pipeline).to_list(None)
    
    # Get daily breakdown
    daily_pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$amount"}
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]
    
    daily_stats = await db.credit_transactions.aggregate(daily_pipeline).to_list(None)
    
    return {
        "transaction_types": stats,
        "daily_breakdown": daily_stats,
        "period_days": days,
        "period_start": cutoff_date,
        "period_end": datetime.now(timezone.utc)
    }
