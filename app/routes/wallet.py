from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.utils.rate_limiter import RateLimiter
from app.utils.wallet_auto_refill import WalletAutoRefill
from app.models.credit_transaction import CreditTransactionType
from app.database import db, client
from bson import ObjectId
from app.models.wallet import WalletAdd, WalletResponse
from datetime import datetime, timezone
from pymongo.errors import PyMongoError

router = APIRouter(prefix="/wallet", tags=["Wallet"])

# ✅ Get wallet balance
@router.get("/balance", response_model=WalletResponse)
async def wallet_balance(user=Depends(get_current_user)):
    # Check if auto-refill is needed
    was_refilled, message, new_balance = await WalletAutoRefill.check_and_refill_wallet(user.id)
    
    return WalletResponse(balance=new_balance)

# ✅ Add money (Top-Up) to wallet
@router.post("/topup")
async def top_up_wallet(data: WalletAdd, user=Depends(get_current_user)):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid top-up amount")

    # 1. Check daily credit limit
    can_credit, credit_limit_msg = await RateLimiter.check_daily_credit_limit(user.id, max_amount=10000.0)
    if not can_credit:
        raise HTTPException(status_code=429, detail=credit_limit_msg)

    # 2. Check top-up limit
    if (user.wallet_balance or 0) + data.amount > 50000:
        raise HTTPException(status_code=400, detail="Wallet balance cannot exceed ₹50,000")

    # 3. Check top-up count today
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    topups_today = await db.wallet_history.count_documents({
        "user_id": ObjectId(user.id),
        "type": "credit",
        "timestamp": {"$gte": start_of_day}
    })

    if topups_today >= 2:
        raise HTTPException(status_code=400, detail="You can only top-up twice per day")

    # 4. Update wallet (without transaction for standalone MongoDB)
    try:
        await db.users.update_one(
            {"_id": ObjectId(user.id)},
            {"$inc": {"wallet_balance": data.amount}}
        )
        await db.wallet_history.insert_one({
            "user_id": ObjectId(user.id),
            "type": "credit",
            "amount": data.amount,
            "ref_note": data.ref_note,
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Record in credit transactions table
        await WalletAutoRefill.record_credit_transaction(
            user_id=user.id,
            amount=data.amount,
            transaction_type=CreditTransactionType.MANUAL_TOPUP,
            description=data.ref_note,
            is_auto_refill=False
        )
    except PyMongoError as e:
        print(f"Top-up failed: {e}")
        raise HTTPException(status_code=500, detail="Wallet top-up failed.")

    return {"message": f"₹{data.amount} added to your wallet"}


# ✅ View transaction history
@router.get("/history")
async def get_transaction_history(user=Depends(get_current_user)):
    user_id = ObjectId(user.id)

    txns = await db.wallet_history.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).to_list(100)

    for txn in txns:
        txn["_id"] = str(txn["_id"])
        txn["user_id"] = str(txn["user_id"])
        txn["timestamp"] = txn["timestamp"].isoformat()

    return txns

# ✅ Manual refill to ₹50,000
@router.post("/refill")
async def manual_refill_wallet(user=Depends(get_current_user)):
    """Manually refill wallet to ₹50,000"""
    
    # Get current user balance
    user_doc = await db.users.find_one({"_id": ObjectId(user.id)}, {"wallet_balance": 1})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_balance = user_doc.get("wallet_balance", 0.0)
    target_balance = 50000.0
    refill_amount = target_balance - current_balance
    
    # Check if refill is needed
    if refill_amount <= 0:
        return {"message": "Wallet is already at maximum balance (₹50,000)", "refilled": False}
    
    # Check daily refill limit (same as auto-refill)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    refills_today = await db.credit_transactions.count_documents({
        "user_id": ObjectId(user.id),
        "transaction_type": CreditTransactionType.AUTO_REFILL.value,
        "is_auto_refill": True,
        "created_at": {"$gte": today}
    })
    
    if refills_today >= 3:  # Same limit as auto-refill
        raise HTTPException(status_code=429, detail="Daily refill limit reached (3 refills per day)")
    
    # Perform refill (without transaction for standalone MongoDB)
    try:
        # Update user balance
        await db.users.update_one(
            {"_id": ObjectId(user.id)},
            {"$set": {"wallet_balance": target_balance}}
        )
        
        # Record in wallet history
        await db.wallet_history.insert_one({
            "user_id": ObjectId(user.id),
            "type": "credit",
            "amount": refill_amount,
            "ref_note": "Manual refill to ₹50,000",
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Record in credit transactions
        await WalletAutoRefill.record_credit_transaction(
            user_id=user.id,
            amount=refill_amount,
            transaction_type=CreditTransactionType.AUTO_REFILL,
            description="Manual refill to ₹50,000",
            is_auto_refill=True
        )
        
    except PyMongoError as e:
        print(f"Manual refill failed: {e}")
        raise HTTPException(status_code=500, detail="Manual refill failed")
    
    return {
        "message": f"Wallet refilled to ₹50,000 (added ₹{refill_amount:,.0f})",
        "refilled": True,
        "refill_amount": refill_amount,
        "new_balance": target_balance
    }
