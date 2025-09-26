from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.utils.cloudinary import get_optimized_image_url
from app.models.message import MessageCreate, ChatResponse
from app.database import db
from app.utils.rate_limiter import RateLimiter
from datetime import datetime, timezone
from typing import List
from app.routes.listings import _notify


router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/send", response_model=dict)
async def send_message(data: MessageCreate, user: TokenUser = Depends(get_current_user)):
    # 1. Rate limiting: Check message rate limit (3 per 10s)
    can_send, rate_limit_msg = await RateLimiter.check_message_rate_limit(user.id, window_seconds=10, max_requests=3)
    if not can_send:
        raise HTTPException(status_code=429, detail=rate_limit_msg)

    # 2. Validation: Prevent sending messages to oneself
    if user.id == data.receiver_id:
        raise HTTPException(status_code=400, detail="You cannot send a message to yourself.")

    # 3. Verify receiver and listing
    receiver_exists = await db.users.find_one({"_id": ObjectId(data.receiver_id)}, {"name": 1})
    listing_exists = await db.listings.find_one({"_id": ObjectId(data.listing_id)}, {"title": 1, "images": 1})
    if not receiver_exists or not listing_exists:
        raise HTTPException(status_code=404, detail="Receiver or listing not found.")

    # 4. Insert the message
    message_doc = {
        "sender_id": ObjectId(user.id),
        "receiver_id": ObjectId(data.receiver_id),
        "listing_id": ObjectId(data.listing_id),
        "message": data.message,
        "timestamp": datetime.now(timezone.utc)
    }
    await db.messages.insert_one(message_doc)

    # 5. Create a notification for the receiver
    sender = await db.users.find_one({"_id": ObjectId(user.id)}, {"name": 1})
    await _notify(
        ObjectId(data.receiver_id),
        "message",
        "New Message",
        f"{sender.get('name', 'Someone')} sent you a new message about {listing_exists.get('title', 'a listing')}",
        meta={
            "sender_id": str(user.id),
            "listing_id": str(data.listing_id),
            "listing_title": listing_exists.get("title"),
            "listing_image": (listing_exists.get("images") or [None])[0]
        }
    )

    return {"message": "Message sent successfully and notification created."}

@router.get("/chat/{listing_id}/{receiver_id}", response_model=ChatResponse)
async def get_chat(
    listing_id: str, 
    receiver_id: str, 
    user: TokenUser = Depends(get_current_user),
    # Add pagination parameters
    skip: int = 0,
    limit: int = Query(default=50, lte=100)
):
    sender_obj_id = ObjectId(user.id)
    receiver_obj_id = ObjectId(receiver_id)
    listing_obj_id = ObjectId(listing_id)

    # Step 1: Fetch a 'page' of messages
    messages_cursor = db.messages.find({
        "$or": [
            {"sender_id": sender_obj_id, "receiver_id": receiver_obj_id},
            {"sender_id": receiver_obj_id, "receiver_id": sender_obj_id}
        ],
        "listing_id": listing_obj_id
    }).sort("timestamp", -1).skip(skip).limit(limit) # Sort descending and paginate

    # Use the limit parameter here
    messages = await messages_cursor.to_list(length=limit)
    messages.reverse() # Reverse to show oldest first in the chunk

    # Step 2: Mark unread messages as read (this is fine as is)
    # This operation is quick and should run on all unread messages in the chat, not just the page.
    await db.messages.update_many(
        {
            "sender_id": receiver_obj_id, "receiver_id": sender_obj_id,
            "listing_id": listing_obj_id, "is_read": {"$ne": True}
        },
        {"$set": {"is_read": True}}
    )

    # Step 3 & 4 remain the same...
    for msg in messages:
        msg['id'] = str(msg['_id'])
        msg['sender_id'] = str(msg['sender_id'])
        msg['receiver_id'] = str(msg['receiver_id'])
        msg['listing_id'] = str(msg['listing_id'])

    other_user_doc = await db.users.find_one({"_id": receiver_obj_id})
    if not other_user_doc:
        raise HTTPException(status_code=404, detail="Chat partner not found")

    other_user_data = {
        "id": str(other_user_doc["_id"]),
        "name": other_user_doc.get("name"),
        "avatar": other_user_doc.get("avatar"),
        "reg_no": other_user_doc.get("reg_no")
    }

    # Step 5: Get listing details (for tagged listing in chat)
    listing_doc = await db.listings.find_one({"_id": listing_obj_id})
    if not listing_doc:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing_data = {
        "id": str(listing_doc["_id"]),
        "title": listing_doc.get("title"),
        "price": listing_doc.get("price"),
        "image": get_optimized_image_url(listing_doc["images"][0]) if listing_doc.get("images") else None
    }

    return {
        "messages": messages,
        "other_user": other_user_data,
        "listing": listing_data
    }

@router.get("/conversations", response_model=List[dict])
async def get_conversations(user: TokenUser = Depends(get_current_user)):
    user_obj_id = ObjectId(user.id)

    pipeline = [
        {
            "$match": {
                "$or": [
                    {"sender_id": user_obj_id},
                    {"receiver_id": user_obj_id}
                ]
            }
        },
        {"$sort": {"timestamp": -1}},
        {
            "$group": {
                "_id": {
                    "listing_id": "$listing_id",
                    "other_user_id": {
                        "$cond": {
                            "if": {"$eq": ["$sender_id", user_obj_id]},
                            "then": "$receiver_id",
                            "else": "$sender_id"
                        }
                    }
                },
                "last_message": {"$first": "$message"},
                "last_message_time": {"$first": "$timestamp"},
                "messages_for_unread": {
                    "$push": {
                        "sender_id": "$sender_id",
                        "is_read": "$is_read"
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "listings",
                "localField": "_id.listing_id",
                "foreignField": "_id",
                "as": "listing_details"
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "_id.other_user_id",
                "foreignField": "_id",
                "as": "other_user_details"
            }
        },
        {"$unwind": "$listing_details"},
        {"$unwind": "$other_user_details"},
        {
            "$project": {
                "_id": 0,
                "listing_id": {"$toString": "$_id.listing_id"},
                "listing_title": "$listing_details.title",
                "listing_image": {"$arrayElemAt": ["$listing_details.images", 0]},
                "other_user": {
                    "id": {"$toString": "$_id.other_user_id"},
                    "name": "$other_user_details.name",
                    "avatar": "$other_user_details.avatar",
                    "reg_no": "$other_user_details.reg_no"
                },
                "last_message": "$last_message",
                "last_message_time": "$last_message_time",
                "unread_count": {
                    "$size": {
                        "$filter": {
                            "input": "$messages_for_unread",
                            "as": "msg",
                            "cond": {
                                "$and": [
                                    {"$eq": ["$$msg.sender_id", "$_id.other_user_id"]},
                                    {"$ne": ["$$msg.is_read", True]}
                                ]
                            }
                        }
                    }
                }
            }
        }
    ]

    conversations_cursor = db.messages.aggregate(pipeline)
    conversations = await conversations_cursor.to_list(length=None)

    # ✅ Optimize images before returning
    for convo in conversations:
        if convo.get("listing_image"):
            convo["listing_image"] = get_optimized_image_url(convo["listing_image"])

    return conversations