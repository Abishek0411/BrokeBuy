from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.models.user import UserResponse, UserUpdate, TokenUser
from app.database import db
from bson import ObjectId

users_collection = db.users

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_my_profile(user: TokenUser = Depends(get_current_user)):
    user_doc = await users_collection.find_one({"_id": ObjectId(user.id)})

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    user_doc["id"] = str(user_doc["_id"])
    user_doc.setdefault("avatar_url", None)
    user_doc.setdefault("wallet_balance", 0.0)

    return UserResponse(**user_doc)

@router.put("/update", response_model=dict)
async def update_my_profile(data: UserUpdate, user=Depends(get_current_user)):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": updates})
    return {"message": "Profile updated"}
