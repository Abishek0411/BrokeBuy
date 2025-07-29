from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.models.message import MessageCreate, MessageResponse
from app.database import db
from datetime import datetime, timezone
from typing import List

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/send", response_model=dict)
async def send_message(data: MessageCreate, user: TokenUser = Depends(get_current_user)):
    # 1. Validation: Prevent sending messages to oneself
    if user.id == data.receiver_id:
        raise HTTPException(status_code=400, detail="You cannot send a message to yourself.")

    # (Optional but recommended) Check if receiver and listing exist
    receiver_exists = await db.users.find_one({"_id": ObjectId(data.receiver_id)})
    listing_exists = await db.listings.find_one({"_id": ObjectId(data.listing_id)})
    if not receiver_exists or not listing_exists:   
        raise HTTPException(status_code=404, detail="Receiver or listing not found.")
        
    message = {
        # 2. Data Integrity: Convert string IDs to ObjectId before saving
        "sender_id": ObjectId(user.id),
        "receiver_id": ObjectId(data.receiver_id),
        "listing_id": ObjectId(data.listing_id),
        "message": data.message,
        "timestamp": datetime.now(timezone.utc)
    }
    
    await db.messages.insert_one(message)
    return {"message": "Message sent successfully"}

@router.get("/chat/{listing_id}/{receiver_id}", response_model=List[MessageResponse])
async def get_chat(listing_id: str, receiver_id: str, user: TokenUser = Depends(get_current_user)):
    # Query using ObjectIds for consistency and correctness
    sender_obj_id = ObjectId(user.id)
    receiver_obj_id = ObjectId(receiver_id)
    listing_obj_id = ObjectId(listing_id)

    # This query will now be extremely fast because of the index you created
    messages_cursor = db.messages.find({
        "$or": [
            {"sender_id": sender_obj_id, "receiver_id": receiver_obj_id},
            {"sender_id": receiver_obj_id, "receiver_id": sender_obj_id}
        ],
        "listing_id": listing_obj_id
    }).sort("timestamp", 1)

    messages = []
    async for message in messages_cursor:
        # Ensure the response model can handle ObjectId by converting it back to str
        message['id'] = str(message['_id'])
        message['sender_id'] = str(message['sender_id'])
        message['receiver_id'] = str(message['receiver_id'])
        message['listing_id'] = str(message['listing_id'])
        messages.append(MessageResponse(**message))
        
    return messages
