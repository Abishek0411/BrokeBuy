from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.models.user import UserResponse, UserUpdate, TokenUser
from app.database import db
from bson import ObjectId

users_collection = db.users
listings_collection = db.listings

router = APIRouter(prefix="/users", tags=["Users"])

# GET /users/me - Get own profile
@router.get("/me", response_model=UserResponse)
async def get_my_profile(user: TokenUser = Depends(get_current_user)):
    user_doc = await users_collection.find_one({"_id": ObjectId(user.id)})

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Clean & standardize response
    return UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        srm_id=user_doc.get("srm_id"),
        name=user_doc.get("name"),
        reg_no=user_doc.get("reg_no"),
        phone=user_doc.get("phone"),
        avatar=user_doc.get("avatar"),  # or avatar_url if that’s the key you used
        wallet_balance=user_doc.get("wallet_balance", 0.0),
        role=user_doc.get("role", "student")
    )

# PUT /users/update - Update own profile
@router.put("/update", response_model=dict)
async def update_my_profile(data: UserUpdate, user: TokenUser = Depends(get_current_user)):
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await users_collection.update_one({"_id": ObjectId(user.id)}, {"$set": updates})
    return {"message": "Profile updated"}

# GET /users/purchases - Get listings bought by user
@router.get("/purchases")
async def get_purchases(user: TokenUser = Depends(get_current_user)):
    purchases = await listings_collection.find({"buyer_id": user.id}).to_list(length=None)
    
    for purchase in purchases:
        purchase["_id"] = str(purchase["_id"])
        purchase["buyer_id"] = str(purchase.get("buyer_id", ""))
        purchase["posted_by"] = str(purchase.get("posted_by", ""))
    
    return purchases    

# GET /users/sales - Get listings sold by user
@router.get("/sales")
async def get_sales(user: TokenUser = Depends(get_current_user)):
    try:
        sales = await listings_collection.find({
            "posted_by": user.id,
            "is_sold": {"$in": [True, "true"]}
        }).to_list(length=None)

        for sale in sales:
            sale["_id"] = str(sale["_id"])
            sale["buyer_id"] = str(sale.get("buyer_id", ""))
            sale["posted_by"] = str(sale.get("posted_by", ""))

        return sales
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
