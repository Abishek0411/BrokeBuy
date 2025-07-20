from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.database import db
from bson import ObjectId
from app.models.wallet import WalletAdd, WalletResponse
from datetime import datetime

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

    await db.users.update_one(
        {"_id": ObjectId(user.id)},
        {"$inc": {"wallet_balance": data.amount}}
    )

    await db.transactions.insert_one({
        "user_id": ObjectId(user.id),
        "type": "credit",
        "amount": data.amount,
        "ref_note": data.ref_note,
        "timestamp": datetime.utcnow()
    })

    return {"message": f"₹{data.amount} added to your wallet"}

# ✅ View transaction history
@router.get("/history")
async def get_transaction_history(user=Depends(get_current_user)):
    txns = await db.transactions.find(
        {"user_id": ObjectId(user.id)}
    ).sort("timestamp", -1).to_list(100)

    for t in txns:
        t["_id"] = str(t["_id"])
        t["user_id"] = str(t["user_id"])
        t["timestamp"] = t["timestamp"].isoformat()

    return txns
