from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from app.utils.auth import get_current_user, TokenUser
from app.database import db  # make sure db is accessible
from datetime import datetime, timezone

router = APIRouter()

@router.delete("/delete-listing/{listing_id}")
async def admin_delete_listing(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")

    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    await db.listings.delete_one({"_id": ObjectId(listing_id)})
    return {"message": f"Listing {listing_id} deleted by admin"}

@router.post("/mark-sold/{listing_id}")
async def admin_mark_sold(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")

    now = datetime.now(timezone.utc)
    result = await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {"$set": {"is_sold": True, "updated_at": now}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Listing not found or already sold")

    return {"message": "Marked as sold ✅"}

@router.post("/mark-available/{listing_id}")
async def admin_mark_available(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")

    now = datetime.now(timezone.utc)
    result = await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {"$set": {"is_sold": False, "updated_at": now}, "$unset": {"buyer_id": ""}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Listing not found or already available")

    return {"message": "Marked as available ✅"}

@router.get("/listings")
async def get_all_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: TokenUser = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    cursor = db.listings.find().skip(skip).limit(limit)
    listings = await cursor.to_list(length=limit)

    # Convert ObjectId to string for each listing
    for listing in listings:
        listing["_id"] = str(listing["_id"])
        listing["posted_by"] = str(listing["posted_by"])
        if "buyer_id" in listing:
            listing["buyer_id"] = str(listing["buyer_id"])

    return {
        "skip": skip,
        "limit": limit,
        "count": len(listings),
        "listings": listings
    }

@router.get("/listings/user/{user_id}")
async def get_listings_by_user(user_id: str, user: TokenUser = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")

    listings = await db.listings.find({"posted_by": user_id}).to_list(length=100)
    return {"user_id": user_id, "listings": listings}

@router.get("/user-wallet/{user_id}")
async def get_user_wallet_and_history(user_id: str, user: TokenUser = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")

    user_data = await db.users.find_one({"_id": ObjectId(user_id)}, {"wallet_balance": 1})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = await db.wallet_history.find({"user_id": user_id}).sort("timestamp", -1).to_list(length=50)
    return {
        "user_id": user_id,
        "wallet_balance": user_data["wallet_balance"],
        "wallet_history": transactions
    }

