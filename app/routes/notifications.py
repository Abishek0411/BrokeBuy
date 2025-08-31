from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional
from app.database import db
from auth import get_current_user, TokenUser  # your auth dependency

router = APIRouter()

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

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(user: TokenUser = Depends(get_current_user)):
    """Get all notifications for the logged-in user."""
    notifs = await db.notifications.find({"receiver_id": ObjectId(user.id)}).sort("timestamp", -1).to_list(length=50)
    for n in notifs:
        n["id"] = str(n["_id"])
        n["sender_id"] = str(n["sender_id"])
        n["receiver_id"] = str(n["receiver_id"])
        if n.get("listing_id"):
            n["listing_id"] = str(n["listing_id"])
    return notifs

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
