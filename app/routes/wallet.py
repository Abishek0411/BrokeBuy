from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.database import db
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

    # Start a client session for the transaction
    async with await db.start_session() as s:
        # Start a transaction
        async with s.start_transaction():
            try:
                # Perform both operations within the transaction
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
                # The transaction will be automatically aborted on an error
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
