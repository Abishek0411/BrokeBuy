from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from app.models.listing import ListingCreate, ListingResponse, ListingUpdate
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.utils.cloudinary import upload_image_to_cloudinary
from app.database import db
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional

router = APIRouter(prefix="/listings", tags=["Listings"])

@router.post("/create")
async def create_listing(data: ListingCreate, user: TokenUser = Depends(get_current_user)):
    listing = data.dict()
    listing["posted_by"] = user.id
    listing["is_sold"] = False
    listing["created_at"] = datetime.utcnow()
    listing["updated_at"] = datetime.utcnow()

    result = await db.listings.insert_one(listing)
    return {"message": "Listing created", "listing_id": str(result.inserted_id)}


@router.get("/", response_model=List[dict])
async def get_all_listings():
    listings = await db.listings.find({"is_sold": False}).to_list(length=None)

    # Clean up object IDs and other conversions
    for listing in listings:
        listing["id"] = str(listing["_id"])
        listing["posted_by"] = str(listing["posted_by"])
        listing["images"] = listing.get("images", [])
        listing.pop("_id", None)

    return listings


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
    price = float(listing["price"])

    if user_wallet < price:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")
    
    # Deduct from wallet
    await db.users.update_one(
        {"_id": ObjectId(user.id)},
        {"$inc": {"wallet_balance": -price}}
    )

    await db.wallet_history.insert_one({
        "user_id": user.id,
        "type": "debit",
        "amount": price,
        "ref_note": f"Purchased listing: {listing['title']}",
        "timestamp": datetime.utcnow()
    })

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

@router.get("/search")
async def search_listings(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    query: Optional[str] = None,
    exclude_sold: bool = True,
):
    search_query = {}

    if category:
        search_query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        search_query["price"] = price_filter

    if query:
        search_query["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]

    if exclude_sold:
        search_query["is_sold"] = False

    results = await db.listings.find(search_query).to_list(length=None)

    for listing in results:
        listing["id"] = str(listing["_id"])
        listing["posted_by"] = str(listing.get("posted_by", ""))
        listing["buyer_id"] = str(listing.get("buyer_id", ""))
        listing["images"] = listing.get("images", [])
        listing.pop("_id", None)
    return results


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing_by_id(listing_id: str):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing["id"] = str(listing["_id"])
    listing["images"] = listing.get("images", [])
    listing["posted_by"] = str(listing.get("posted_by", ""))
    listing["buyer_id"] = str(listing.get("buyer_id", ""))

    return ListingResponse(**listing)

@router.post("/upload-image", response_model=dict)
async def upload_image(
    file: UploadFile = File(...), 
    user: TokenUser = Depends(get_current_user)
):
    try:
        image_url = await upload_image_to_cloudinary(file)
        return {"image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    update_data: ListingUpdate,
    user: TokenUser = Depends(get_current_user)
):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="You are not allowed to update this listing")

    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()

    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {"$set": update_dict}
    )

    return {"message": "Listing updated successfully"}

@router.delete("/{listing_id}")
async def delete_listing(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="You are not allowed to delete this listing")

    await db.listings.delete_one({"_id": ObjectId(listing_id)})
    
    return {"message": "Listing deleted successfully"}
