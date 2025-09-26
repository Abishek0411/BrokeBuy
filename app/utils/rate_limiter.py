from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple
from app.database import db
from bson import ObjectId
import asyncio

class RateLimiter:
    """Rate limiter for various operations"""
    
    @staticmethod
    async def check_message_rate_limit(user_id: str, window_seconds: int = 10, max_requests: int = 3) -> Tuple[bool, str]:
        """Check if user can send a message based on rate limit"""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)
        
        # Count messages sent in the time window
        count = await db.messages.count_documents({
            "sender_id": ObjectId(user_id),
            "timestamp": {"$gte": window_start}
        })
        
        if count >= max_requests:
            return False, f"Rate limit exceeded. You can send {max_requests} messages per {window_seconds} seconds."
        
        return True, ""
    
    @staticmethod
    async def check_listing_rate_limit(user_id: str, window_hours: int = 24, max_requests: int = 3) -> Tuple[bool, str]:
        """Check if user can create a listing based on daily rate limit"""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=window_hours)
        
        # Count listings created in the time window
        count = await db.listings.count_documents({
            "posted_by": user_id,
            "created_at": {"$gte": window_start}
        })
        
        if count >= max_requests:
            return False, f"Rate limit exceeded. You can create {max_requests} listings per day."
        
        return True, ""
    
    @staticmethod
    async def check_daily_credit_limit(user_id: str, max_amount: float = 10000.0) -> Tuple[bool, str]:
        """Check if user has exceeded daily credit transaction limit"""
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Sum all credit transactions today
        pipeline = [
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "type": "credit",
                    "timestamp": {"$gte": start_of_day}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_amount": {"$sum": "$amount"}
                }
            }
        ]
        
        result = await db.wallet_history.aggregate(pipeline).to_list(1)
        total_credits = result[0]["total_amount"] if result else 0.0
        
        if total_credits >= max_amount:
            return False, f"Daily credit limit exceeded. Maximum ₹{max_amount:,.0f} per day."
        
        return True, ""
