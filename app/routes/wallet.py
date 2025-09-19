from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.database import db, client
from bson import ObjectId
from app.models.wallet import WalletAdd, WalletResponse
from datetime import datetime, timezone
from pymongo.errors import PyMongoError

router = APIRouter(prefix="/wallet", tags=["Wallet"])

# ✅ Get wallet balance
@router.get("/balance", response_model=WalletResponse)
async def wallet_balance(user=Depends(get_current_user)):
    return WalletResponse(balance=user.wallet_balance or 0.0)

# ✅ Add money (Top-Up) to wallet
@router.post("/topup")
async def top_up_wallet(data: WalletAdd, user=Depends(get_current_user)):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid top-up amount")

    # 1. Check top-up limit
    if (user.wallet_balance or 0) + data.amount > 50000:
        raise HTTPException(status_code=400, detail="Wallet balance cannot exceed ₹50,000")

    # 2. Check top-up count today
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    topups_today = await db.wallet_history.count_documents({
        "user_id": ObjectId(user.id),
        "type": "credit",
        "timestamp": {"$gte": start_of_day}
    })

    if topups_today >= 2:
        raise HTTPException(status_code=400, detail="You can only top-up twice per day")

    # 3. Transaction
    async with await client.start_session() as s:
        async with s.start_transaction():
            try:
                await db.users.update_one(
                    {"_id": ObjectId(user.id)},
                    {"$inc": {"wallet_balance": data.amount}},
                    session=s
                )
                await db.wallet_history.insert_one({
                    "user_id": ObjectId(user.id),
                    "type": "credit",
                    "amount": data.amount,
                    "ref_note": data.ref_note,
                    "timestamp": datetime.now(timezone.utc)
                }, session=s)
            except PyMongoError as e:
                print(f"Transaction failed: {e}")
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
