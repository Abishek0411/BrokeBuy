from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.models.message import MessageCreate, MessageResponse, OtherUser, ChatResponse
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

@router.get("/chat/{listing_id}/{receiver_id}", response_model=ChatResponse) # Use new model
async def get_chat(listing_id: str, receiver_id: str, user: TokenUser = Depends(get_current_user)):
    sender_obj_id = ObjectId(user.id)
    receiver_obj_id = ObjectId(receiver_id)
    listing_obj_id = ObjectId(listing_id)

    # 1. Fetch the messages (your existing logic is perfect)
    messages_cursor = db.messages.find({
        "$or": [
            {"sender_id": sender_obj_id, "receiver_id": receiver_obj_id},
            {"sender_id": receiver_obj_id, "receiver_id": sender_obj_id}
        ],
        "listing_id": listing_obj_id
    }).sort("timestamp", 1)
    
    messages = await messages_cursor.to_list(length=None)
    for msg in messages:
        msg['id'] = str(msg['_id'])
        msg['sender_id'] = str(msg['sender_id'])
        msg['receiver_id'] = str(msg['receiver_id'])
        msg['listing_id'] = str(msg['listing_id'])

    # 2. Fetch the other user's details
    other_user_doc = await db.users.find_one({"_id": receiver_obj_id})
    if not other_user_doc:
        raise HTTPException(status_code=404, detail="Chat partner not found")

    other_user_data = {
        "id": str(other_user_doc["_id"]),
        "name": other_user_doc.get("name"),
        "avatar": other_user_doc.get("avatar"),
        "reg_no": other_user_doc.get("reg_no")
    }

    # 3. Return both in the new response structure
    return {
        "messages": messages,
        "other_user": other_user_data
    }

@router.get("/conversations", response_model=List[dict])
async def get_conversations(user: TokenUser = Depends(get_current_user)):
    user_obj_id = ObjectId(user.id)

    pipeline = [
        # Stage 1: Match all messages involving the current user
        {
            "$match": {
                "$or": [
                    {"sender_id": user_obj_id},
                    {"receiver_id": user_obj_id}
                ]
            }
        },
        # Stage 2: Sort by latest message first to easily find the last message
        {
            "$sort": {"timestamp": -1}
        },
        # Stage 3: Group messages into unique conversations
        {
            "$group": {
                "_id": {
                    "listing_id": "$listing_id",
                    # Define the other user in the conversation
                    "other_user_id": {
                        "$cond": {
                            "if": {"$eq": ["$sender_id", user_obj_id]},
                            "then": "$receiver_id",
                            "else": "$sender_id"
                        }
                    }
                },
                # Get the content of the most recent message
                "last_message": {"$first": "$message"},
                "last_message_time": {"$first": "$timestamp"},
                # Collect all sender IDs and read statuses for unread count
                "messages_for_unread": {
                    "$push": {
                        "sender_id": "$sender_id",
                        "is_read": "$is_read"
                    }
                }
            }
        },
        # Stage 4: Join with the 'listings' collection
        {
            "$lookup": {
                "from": "listings",
                "localField": "_id.listing_id",
                "foreignField": "_id",
                "as": "listing_details"
            }
        },
        # Stage 5: Join with the 'users' collection to get other user's info
        {
            "$lookup": {
                "from": "users",
                "localField": "_id.other_user_id",
                "foreignField": "_id",
                "as": "other_user_details"
            }
        },
        # Stage 6: Deconstruct the arrays created by $lookup
        {"$unwind": "$listing_details"},
        {"$unwind": "$other_user_details"},
        # Stage 7: Reshape the final output to match the frontend's expectation
        {
            "$project": {
                "_id": 0, # Exclude the default _id field
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
                # Calculate unread count on the server
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
    return await conversations_cursor.to_list(length=None)

