from typing import List, Dict, Set
from bson import ObjectId
from app.database import db
from datetime import datetime, timezone, timedelta

class CircularTradeDetector:
    """Detects circular trading patterns to prevent abuse"""
    
    @staticmethod
    async def detect_circular_trade(user_id: str, target_user_id: str) -> tuple[bool, str]:
        """
        Detect if a trade would create a circular pattern
        Returns (is_circular, reason)
        """
        
        # Get recent transactions for both users
        recent_days = 7
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=recent_days)
        
        # Get user's recent sales
        user_sales = await db.listings.find({
            "posted_by": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        }).to_list(length=None)
        
        # Get user's recent purchases
        user_purchases = await db.listings.find({
            "buyer_id": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        }).to_list(length=None)
        
        # Get target user's recent sales
        target_sales = await db.listings.find({
            "posted_by": target_user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        }).to_list(length=None)
        
        # Get target user's recent purchases
        target_purchases = await db.listings.find({
            "buyer_id": target_user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        }).to_list(length=None)
        
        # Check for direct circular trades (A sells to B, B sells to A)
        user_sold_to_target = any(
            sale.get("buyer_id") == target_user_id for sale in user_sales
        )
        target_sold_to_user = any(
            sale.get("buyer_id") == user_id for sale in target_sales
        )
        
        if user_sold_to_target and target_sold_to_user:
            return True, "Direct circular trade detected: both users have sold items to each other recently"
        
        # Check for complex circular patterns (A->B->C->A)
        if await CircularTradeDetector._detect_complex_circular_pattern(user_id, target_user_id, cutoff_date):
            return True, "Complex circular trade pattern detected"
        
        # Check for rapid back-and-forth trading
        if await CircularTradeDetector._detect_rapid_trading(user_id, target_user_id, cutoff_date):
            return True, "Rapid back-and-forth trading detected"
        
        return False, ""
    
    @staticmethod
    async def _detect_complex_circular_pattern(user_id: str, target_user_id: str, cutoff_date: datetime) -> bool:
        """Detect complex circular trading patterns"""
        
        # Get all users involved in trades with the given users
        involved_users = set()
        
        # Users who bought from user_id
        user_buyers = await db.listings.find({
            "posted_by": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        }, {"buyer_id": 1}).to_list(length=None)
        
        for buyer in user_buyers:
            involved_users.add(str(buyer["buyer_id"]))
        
        # Users who sold to user_id
        user_sellers = await db.listings.find({
            "buyer_id": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        }, {"posted_by": 1}).to_list(length=None)
        
        for seller in user_sellers:
            involved_users.add(str(seller["posted_by"]))
        
        # Check if target_user_id is in the trading network
        if target_user_id in involved_users:
            # Check for circular path: user_id -> ... -> target_user_id -> ... -> user_id
            return await CircularTradeDetector._find_circular_path(user_id, target_user_id, involved_users, cutoff_date)
        
        return False
    
    @staticmethod
    async def _detect_rapid_trading(user_id: str, target_user_id: str, cutoff_date: datetime) -> bool:
        """Detect rapid back-and-forth trading between users"""
        
        # Count trades between users in the last 24 hours
        recent_hours = 24
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=recent_hours)
        
        # Count user -> target trades
        user_to_target = await db.listings.count_documents({
            "posted_by": user_id,
            "buyer_id": target_user_id,
            "is_sold": True,
            "sold_at": {"$gte": recent_cutoff}
        })
        
        # Count target -> user trades
        target_to_user = await db.listings.count_documents({
            "posted_by": target_user_id,
            "buyer_id": user_id,
            "is_sold": True,
            "sold_at": {"$gte": recent_cutoff}
        })
        
        # If more than 3 trades in 24 hours, flag as rapid trading
        total_trades = user_to_target + target_to_user
        return total_trades > 3
    
    @staticmethod
    async def _find_circular_path(start_user: str, target_user: str, involved_users: Set[str], cutoff_date: datetime) -> bool:
        """Find if there's a circular trading path"""
        
        # Simple BFS to find circular path
        visited = set()
        queue = [(start_user, [start_user])]
        
        while queue:
            current_user, path = queue.pop(0)
            
            if current_user in visited:
                continue
            
            visited.add(current_user)
            
            # Get users this user sold to
            sales = await db.listings.find({
                "posted_by": current_user,
                "is_sold": True,
                "sold_at": {"$gte": cutoff_date}
            }, {"buyer_id": 1}).to_list(length=None)
            
            for sale in sales:
                buyer_id = str(sale["buyer_id"])
                
                if buyer_id == start_user and len(path) > 2:
                    # Found circular path
                    return True
                
                if buyer_id in involved_users and buyer_id not in visited:
                    queue.append((buyer_id, path + [buyer_id]))
        
        return False
    
    @staticmethod
    async def get_trading_stats(user_id: str, days: int = 30) -> Dict:
        """Get trading statistics for a user"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Count sales
        sales_count = await db.listings.count_documents({
            "posted_by": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        })
        
        # Count purchases
        purchases_count = await db.listings.count_documents({
            "buyer_id": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        })
        
        # Get unique trading partners
        sales_partners = await db.listings.distinct("buyer_id", {
            "posted_by": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        })
        
        purchase_partners = await db.listings.distinct("posted_by", {
            "buyer_id": user_id,
            "is_sold": True,
            "sold_at": {"$gte": cutoff_date}
        })
        
        unique_partners = len(set(sales_partners + purchase_partners))
        
        return {
            "sales_count": sales_count,
            "purchases_count": purchases_count,
            "unique_partners": unique_partners,
            "total_trades": sales_count + purchases_count
        }
