from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.database import db
from app.models.credit_transaction import CreditTransactionType
from typing import Tuple

class WalletAutoRefill:
    """Handles automatic wallet refilling when balance goes below threshold"""
    
    REFILL_THRESHOLD = 20000.0  # Refill when balance goes below 20k
    REFILL_AMOUNT = 50000.0     # Refill to 50k
    MAX_DAILY_REFILLS = 3       # Maximum auto-refills per day
    
    @staticmethod
    async def check_and_refill_wallet(user_id: str) -> Tuple[bool, str, float]:
        """
        Check if wallet needs refilling and refill if necessary
        Returns (was_refilled, message, new_balance)
        """
        
        # Get current user balance
        user = await db.users.find_one({"_id": ObjectId(user_id)}, {"wallet_balance": 1})
        if not user:
            return False, "User not found", 0.0
        
        current_balance = user.get("wallet_balance", 0.0)
        
        # Check if refill is needed
        if current_balance >= WalletAutoRefill.REFILL_THRESHOLD:
            return False, "No refill needed", current_balance
        
        # Check daily refill limit
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        refills_today = await db.credit_transactions.count_documents({
            "user_id": ObjectId(user_id),
            "transaction_type": CreditTransactionType.AUTO_REFILL.value,
            "is_auto_refill": True,
            "created_at": {"$gte": today}
        })
        
        if refills_today >= WalletAutoRefill.MAX_DAILY_REFILLS:
            return False, f"Daily auto-refill limit reached ({WalletAutoRefill.MAX_DAILY_REFILLS})", current_balance
        
        # Calculate refill amount
        refill_amount = WalletAutoRefill.REFILL_AMOUNT - current_balance
        
        # Perform refill
        new_balance = await WalletAutoRefill._perform_refill(user_id, refill_amount)
        
        return True, f"Wallet auto-refilled with ₹{refill_amount:,.0f}", new_balance
    
    @staticmethod
    async def _perform_refill(user_id: str, amount: float) -> float:
        """Perform the actual wallet refill"""
        
        # Update user balance
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"wallet_balance": WalletAutoRefill.REFILL_AMOUNT}}
        )
        
        # Record in wallet history
        await db.wallet_history.insert_one({
            "user_id": ObjectId(user_id),
            "type": "credit",
            "amount": amount,
            "ref_note": f"Auto-refill: Balance below ₹{WalletAutoRefill.REFILL_THRESHOLD:,.0f}",
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Record in credit transactions
        await db.credit_transactions.insert_one({
            "user_id": ObjectId(user_id),
            "amount": amount,
            "transaction_type": CreditTransactionType.AUTO_REFILL.value,
            "description": f"Auto-refill: Balance below ₹{WalletAutoRefill.REFILL_THRESHOLD:,.0f}",
            "is_auto_refill": True,
            "created_at": datetime.now(timezone.utc),
            "previous_balance": WalletAutoRefill.REFILL_AMOUNT - amount,
            "new_balance": WalletAutoRefill.REFILL_AMOUNT
        })
        
        return WalletAutoRefill.REFILL_AMOUNT
    
    @staticmethod
    async def record_credit_transaction(
        user_id: str,
        amount: float,
        transaction_type: CreditTransactionType,
        reference_id: str = None,
        description: str = None,
        is_auto_refill: bool = False
    ) -> str:
        """Record a credit transaction in the credit_transactions table"""
        
        # Get current balance for logging
        user = await db.users.find_one({"_id": ObjectId(user_id)}, {"wallet_balance": 1})
        previous_balance = user.get("wallet_balance", 0.0) if user else 0.0
        new_balance = previous_balance + amount
        
        # Insert credit transaction record
        result = await db.credit_transactions.insert_one({
            "user_id": ObjectId(user_id),
            "amount": amount,
            "transaction_type": transaction_type.value,
            "reference_id": reference_id,
            "description": description,
            "is_auto_refill": is_auto_refill,
            "created_at": datetime.now(timezone.utc),
            "previous_balance": previous_balance,
            "new_balance": new_balance
        })
        
        return str(result.inserted_id)
    
    @staticmethod
    async def get_credit_transaction_summary(
        user_id: str = None,
        days: int = 30
    ) -> dict:
        """Get summary of credit transactions"""
        
        cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - \
                     timedelta(days=days)
        
        match_query = {
            "created_at": {"$gte": cutoff_date},
            "transaction_type": {"$ne": "auto_refill"}  # Exclude auto-refill transactions
        }
        if user_id:
            match_query["user_id"] = ObjectId(user_id)
        
        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": None,
                    "total_credits": {"$sum": "$amount"},
                    "manual_topups": {
                        "$sum": {"$cond": [
                            {"$eq": ["$transaction_type", CreditTransactionType.MANUAL_TOPUP.value]}, 1, 0]}
                    },
                    "sale_proceeds": {
                        "$sum": {"$cond": [
                            {"$eq": ["$transaction_type", CreditTransactionType.SALE_PROCEEDS.value]}, 
                            "$amount", 0]}
                    },
                    "total_transactions": {"$sum": 1}
                }
            }
        ]
        
        result = await db.credit_transactions.aggregate(pipeline).to_list(1)
        
        if result:
            summary = result[0]
            return {
                "total_credits": summary.get("total_credits", 0.0),
                "manual_topups": summary.get("manual_topups", 0),
                "sale_proceeds": summary.get("sale_proceeds", 0.0),
                "total_transactions": summary.get("total_transactions", 0),
                "period_start": cutoff_date,
                "period_end": datetime.now(timezone.utc)
            }
        
        return {
            "total_credits": 0.0,
            "manual_topups": 0,
            "sale_proceeds": 0.0,
            "total_transactions": 0,
            "period_start": cutoff_date,
            "period_end": datetime.now(timezone.utc)
        }
