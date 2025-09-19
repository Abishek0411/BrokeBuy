from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional
from app.database import db
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.utils.cloudinary import get_optimized_image_url


router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationCreate(BaseModel):
    type: str  # "message" or "buy_request"
    sender_id: str
    receiver_id: str
    listing_id: Optional[str] = None
    message: Optional[str] = None

class NotificationResponse(BaseModel):
    id: str
    type: str
    sender_id: str
    receiver_id: str
    listing_id: Optional[str]
    message: Optional[str]
    is_read: bool
    timestamp: datetime

@router.post("/", response_model=dict)
async def create_notification(data: NotificationCreate, user: TokenUser = Depends(get_current_user)):
    """Create a notification (e.g., when buyer sends message or buying request)."""
    if user.id == data.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot create a notification for yourself.")
    
    notif = {
        "type": data.type,
        "sender_id": ObjectId(data.sender_id),
        "receiver_id": ObjectId(data.receiver_id),
        "listing_id": ObjectId(data.listing_id) if data.listing_id else None,
        "message": data.message,
        "is_read": False,
        "timestamp": datetime.now(timezone.utc)
    }
    result = await db.notifications.insert_one(notif)
    return {"message": "Notification created", "id": str(result.inserted_id)}

@router.get("/")
async def get_notifications(user: TokenUser = Depends(get_current_user)):
    """Fetch all notifications for the logged-in user, enriched with listing, buyer, and message details."""
    cursor = db.notifications.find({"user_id": ObjectId(user.id)}).sort("created_at", -1)
    notifications = await cursor.to_list(length=None)

    # Collect related IDs
    listing_ids, buyer_ids, sender_ids = set(), set(), set()
    for n in notifications:
        meta = n.get("metadata", {})
        ntype = n.get("type")

        if ntype == "buy_request":
            if meta.get("listing_id"):
                listing_ids.add(ObjectId(meta["listing_id"]))
            if meta.get("buyer_id"):
                buyer_ids.add(ObjectId(meta["buyer_id"]))

        elif ntype == "message":
            if meta.get("sender_id"):
                sender_ids.add(ObjectId(meta["sender_id"]))
            if meta.get("listing_id"):
                listing_ids.add(ObjectId(meta["listing_id"]))

    # Fetch related docs
    listings = await db.listings.find(
        {"_id": {"$in": list(listing_ids)}},
        {"title": 1, "images": 1}
    ).to_list(None)
    buyers = await db.users.find(
        {"_id": {"$in": list(buyer_ids)}},
        {"name": 1, "reg_no": 1}
    ).to_list(None)
    senders = await db.users.find(
        {"_id": {"$in": list(sender_ids)}},
        {"name": 1, "avatar": 1}
    ).to_list(None)

    # Create quick lookup maps
    listing_map = {str(l["_id"]): l for l in listings}
    buyer_map = {str(b["_id"]): b for b in buyers}
    sender_map = {str(s["_id"]): s for s in senders}

    enriched = []
    for n in notifications:
        # Normalize base fields
        n["id"] = str(n.pop("_id"))
        n["user_id"] = str(n["user_id"])
        n["created_at"] = n.get("created_at", datetime.now(timezone.utc)).isoformat()
        meta = n.get("metadata", {})
        ntype = n.get("type")

        # Enrich based on type
        if ntype == "buy_request":
            listing = listing_map.get(meta.get("listing_id"))
            buyer = buyer_map.get(meta.get("buyer_id"))
            if listing:
                meta["listing_title"] = listing.get("title", "Unknown Item")
                meta["listing_image"] = get_optimized_image_url(
                    (listing.get("images") or [None])[0]
                )
            if buyer:
                meta["buyer_name"] = buyer.get("name", "Unknown Buyer")
                meta["buyer_reg_no"] = buyer.get("reg_no", "")

        elif ntype == "message":
            sender = sender_map.get(meta.get("sender_id"))
            listing = listing_map.get(meta.get("listing_id"))
            if sender:
                meta["sender_name"] = sender.get("name", "Unknown User")
                meta["sender_avatar"] = sender.get("avatar")
            if listing:
                meta["listing_title"] = listing.get("title", "Unknown Listing")
                meta["listing_image"] = get_optimized_image_url(
                    (listing.get("images") or [None])[0]
                )

        n["metadata"] = meta
        enriched.append(n)

    return {"notifications": enriched}

@router.patch("/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(notification_id: str, user: TokenUser = Depends(get_current_user)):
    """Mark a notification as read."""
    result = await db.notifications.update_one(
        {"_id": ObjectId(notification_id), "receiver_id": ObjectId(user.id)},
        {"$set": {"is_read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found or already read")
    return {"message": "Notification marked as read"}

@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(notification_id: str, user: TokenUser = Depends(get_current_user)):
    """Delete a notification."""
    result = await db.notifications.delete_one(
        {"_id": ObjectId(notification_id), "receiver_id": ObjectId(user.id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}

@router.post("/buy-request", response_model=dict)
async def send_buy_request(
    data: dict,
    user: TokenUser = Depends(get_current_user)
):
    """
    Send a buying request to the seller for a specific listing.
    """
    receiver_id = data.get("receiver_id")
    listing_id = data.get("listing_id")
    message = data.get("message", "I am interested in buying your product.")

    if not receiver_id or not listing_id:
        raise HTTPException(status_code=400, detail="receiver_id and listing_id are required")

    # Validate receiver and listing
    seller = await db.users.find_one({"_id": ObjectId(receiver_id)})
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if str(listing["posted_by"]) != receiver_id:
        raise HTTPException(status_code=400, detail="Receiver is not the owner of this listing")
    if str(user.id) == receiver_id:
        raise HTTPException(status_code=400, detail="You cannot send a buying request to yourself")

    # Create the notification
    notification = {
        "type": "buy_request",
        "sender_id": ObjectId(user.id),         # Buyer
        "receiver_id": ObjectId(receiver_id),   # Seller
        "listing_id": ObjectId(listing_id),
        "message": message,
        "is_read": False,
        "timestamp": datetime.now(timezone.utc)
    }

    await db.notifications.insert_one(notification)

    return {"message": "Buying request sent successfully"}

@router.post("/{notification_id}/respond", response_model=dict)
async def respond_buying_request(notification_id: str, action: str, user: TokenUser = Depends(get_current_user)):
    """
    Accept or decline a buying request.
    action = "accept" or "decline"
    """
    if action not in ["accept", "decline"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    notif = await db.notifications.find_one({"_id": ObjectId(notification_id), "receiver_id": ObjectId(user.id)})
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Notify buyer about seller's decision
    buyer_id = notif["sender_id"]
    decision_message = (
        f"Your buying request for listing {notif.get('listing_id')} was {action}ed."
    )

    await db.notifications.insert_one({
        "type": "buy_request_response",
        "sender_id": ObjectId(user.id),
        "receiver_id": buyer_id,
        "listing_id": notif.get("listing_id"),
        "message": decision_message,
        "is_read": False,
        "timestamp": datetime.now(timezone.utc)
    })

    # Optionally, mark the original buying request notification as read
    await db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"is_read": True}}
    )

    return {"message": f"Buying request {action}ed successfully"}
