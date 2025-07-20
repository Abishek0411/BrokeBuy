from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.models.message import MessageCreate, MessageResponse
from app.database import db
from datetime import datetime
from typing import List

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/send", response_model=dict)
async def send_message(data: MessageCreate, user=Depends(get_current_user)):
    message = {
        "sender_id": user.id,
        "receiver_id": data.receiver_id,
        "listing_id": data.listing_id,
        "message": data.message,
        "timestamp": datetime.utcnow()
    }
    await db.messages.insert_one(message)
    return {"message": "Message sent successfully"}

@router.get("/chat/{listing_id}/{receiver_id}", response_model=List[MessageResponse])
async def get_chat(listing_id: str, receiver_id: str, user=Depends(get_current_user)):
    messages_cursor = db.messages.find({
        "$or": [
            {"sender_id": user.id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": user.id}
        ],
        "listing_id": listing_id
    }).sort("timestamp", 1)

    messages = []
    async for message in messages_cursor:
        messages.append(MessageResponse(**message))
    return messages
