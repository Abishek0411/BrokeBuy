import asyncio
from datetime import datetime, timezone
from app.database import db
from app.utils.wallet_auto_refill import WalletAutoRefill
from bson import ObjectId

async def check_all_users_for_auto_refill():
    """Background task to check all users for auto-refill needs"""
    
    try:
        # Get all users with wallet balance below threshold
        users_cursor = db.users.find({
            "wallet_balance": {"$lt": WalletAutoRefill.REFILL_THRESHOLD}
        }, {"_id": 1, "wallet_balance": 1})
        
        users = await users_cursor.to_list(length=None)
        
        refill_count = 0
        for user in users:
            user_id = str(user["_id"])
            was_refilled, message, new_balance = await WalletAutoRefill.check_and_refill_wallet(user_id)
            
            if was_refilled:
                refill_count += 1
                print(f"Auto-refilled wallet for user {user_id}: {message}")
        
        if refill_count > 0:
            print(f"Auto-refill task completed: {refill_count} wallets refilled")
        else:
            print("Auto-refill task completed: No wallets needed refilling")
            
    except Exception as e:
        print(f"Error in auto-refill task: {e}")

async def get_money_flow_summary():
    """Get summary of money flow for logging purposes"""
    
    try:
        # Get summary for the last 24 hours
        summary = await WalletAutoRefill.get_credit_transaction_summary(None, days=1)
        
        print(f"Money Flow Summary (Last 24h):")
        print(f"  Total Credits: ₹{summary['total_credits']:,.2f}")
        print(f"  Auto Refills: {summary['auto_refills']}")
        print(f"  Manual Topups: {summary['manual_topups']}")
        print(f"  Sale Proceeds: ₹{summary['sale_proceeds']:,.2f}")
        print(f"  Total Transactions: {summary['total_transactions']}")
        
        return summary
        
    except Exception as e:
        print(f"Error getting money flow summary: {e}")
        return None
