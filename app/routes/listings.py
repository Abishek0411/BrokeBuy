from fastapi import APIRouter, Depends, HTTPException, status
from app.models.listing import ListingCreate, ListingResponse
from app.utils.auth import get_current_user
from app.database import db
from datetime import datetime
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/listings", tags=["Listings"])

@router.post("/create", response_model=dict)
async def create_listing(data: ListingCreate, user=Depends(get_current_user)):
    new_listing = {
        **data.model_dump(),
        "posted_by": user.id,  # ✅ not user["sub"]
        "is_sold": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.listings.insert_one(new_listing)
    return {"message": "Listing created", "id": str(result.inserted_id)}

@router.get("/", response_model=List[ListingResponse])
async def get_all_listings():
    listings_cursor = db.listings.find({"is_sold": False})
    listings = []
    async for listing in listings_cursor:
        listing["id"] = str(listing["_id"])
        listings.append(ListingResponse(**listing))
    return listings

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing_by_id(listing_id: str):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing["id"] = str(listing["_id"])
    return ListingResponse(**listing)

@router.post("/buy/{listing_id}", response_model=dict)
async def buy_listing(listing_id: str, user=Depends(get_current_user)):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing["is_sold"]:
        raise HTTPException(status_code=400, detail="Listing already sold")
    
    if listing["posted_by"] == user.id:
        raise HTTPException(status_code=400, detail="You can't buy your own listing")
    
    user_data = await db.users.find_one({"_id": ObjectId(user.id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    user_wallet = user_data.get("wallet_balance", 0.0)
    price = listing["price"]

    if user_wallet < price:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")
    
    # Deduct from wallet
    await db.users.update_one(
        {"_id": ObjectId(user.id)},
        {"$inc": {"wallet_balance": -price}}
    )

    # Mark listing as sold
    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {
            "$set": {
                "is_sold": True,
                "buyer_id": user.id,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Listing purchased successfully ✅"}