from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from app.models.listing import ListingCreate, ListingResponse, ListingUpdate, ListingOut
from app.models.user import TokenUser
from app.utils import cloudinary
from app.utils.auth import get_current_user
from app.utils.cloudinary import upload_image_to_cloudinary, get_optimized_image_url
from app.database import db
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional

router = APIRouter(prefix="/listings", tags=["Listings"])

MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

@router.post("/create")
async def create_listing(
    data: ListingCreate,
    user: TokenUser = Depends(get_current_user)
):
    listing = data.model_dump()
    listing["posted_by"] = user.id
    listing["is_sold"] = False

    now = datetime.now(timezone.utc)
    listing["created_at"] = now
    listing["updated_at"] = now

    # ✅ Store only public_ids (no raw URLs)
    listing["images"] = listing.get("images", [])

    result = await db.listings.insert_one(listing)
    return {"message": "Listing created", "listing_id": str(result.inserted_id)}

@router.get("/", response_model=List[dict])
async def get_all_listings():
    listings = await db.listings.find({"is_sold": False}).to_list(length=None)

    for listing in listings:
        listing["id"] = str(listing["_id"])
        listing["posted_by"] = str(listing["posted_by"])

        # 👇 Include seller info if populated from DB
        seller = await db.users.find_one({"_id": ObjectId(listing["posted_by"])}, {"name": 1, "reg_no": 1})
        listing["seller"] = {
            "name": seller.get("name", "Unknown"),
            "reg_no": seller.get("reg_no", "N/A")
        }

        # 👇 Default values to avoid undefined errors
        listing["created_at"] = listing.get("created_at", datetime.utcnow().isoformat())
        listing["is_available"] = not listing.get("is_sold", False)

        listing["images"] = [get_optimized_image_url(pid) for pid in listing.get("images", [])]
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

    now = datetime.now(timezone.utc)
    await db.wallet_history.insert_one({
        "user_id": user.id,
        "type": "debit",
        "amount": price,
        "ref_note": f"Purchased listing: {listing['title']}",
        "timestamp": now
    })

    # Mark listing as sold
    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {
            "$set": {
                "is_sold": True,
                "buyer_id": user.id,
                "sold_at": now,
                "updated_at": now
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

@router.post("/upload-image", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    user: TokenUser = Depends(get_current_user)
):
    try:
        # Read the file content to check size
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Image too large. Limit is {MAX_UPLOAD_SIZE_MB}MB. Please compress the image and try again."
            )

        # Reset file pointer before uploading
        file.file.seek(0)

        # Upload to Cloudinary
        image_data = await upload_image_to_cloudinary(file)
        return image_data

    except HTTPException:
        raise  # Pass on explicitly raised HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/my-listings", response_model=List[ListingResponse])
async def get_my_listings(user: TokenUser = Depends(get_current_user)):
    print("📌 Current user ID:", user.id)  # Add this
    listings = await db.listings.find({"posted_by": user.id}).to_list(length=None)
    result = []
    for listing in listings:
        listing["id"] = str(listing["_id"])
        listing["posted_by"] = str(listing.get("posted_by", ""))
        listing["buyer_id"] = str(listing.get("buyer_id", ""))
        listing["created_at"] = listing.get("created_at", datetime.now(timezone.utc).isoformat())
        listing["is_available"] = not listing.get("is_sold", False)
        listing["images"] = [get_optimized_image_url(pid) for pid in listing.get("images", [])]
        
        # 🛠️ Add missing fields for frontend
        listing["views"] = listing.get("views", 0)
        listing["interested_users"] = len(listing.get("interested", [])) if "interested" in listing else 0

        result.append(ListingResponse(**listing))

    return result

@router.get("/recent", response_model=List[ListingResponse])
async def get_recent_listings(limit: int = 3):
    listings_cursor = db.listings.find({"is_sold": False}).sort("created_at", -1).limit(limit)
    listings = await listings_cursor.to_list(length=limit)

    result = []
    for listing in listings:
        listing["id"] = str(listing["_id"])
        listing["posted_by"] = str(listing.get("posted_by", ""))
        listing["buyer_id"] = str(listing.get("buyer_id", ""))

        # Convert image public IDs to URLs
        image_ids = listing.get("images", [])
        listing["images"] = [get_optimized_image_url(pid) for pid in image_ids]

        # Fetch seller info (optional but useful)
        seller = await db.users.find_one(
            {"_id": ObjectId(listing["posted_by"])},
            {"name": 1, "reg_no": 1}
        )
        if seller:
            listing["seller_name"] = seller.get("name", "Unknown")
            listing["seller_reg_no"] = seller.get("reg_no", "N/A")
        else:
            listing["seller_name"] = "Unknown"
            listing["seller_reg_no"] = "N/A"

        listing["is_available"] = not listing.get("is_sold", False)
        listing["created_at"] = listing.get("created_at", datetime.utcnow().isoformat())
        listing["views"] = listing.get("views", 0)
        listing["interested_users"] = len(listing.get("interested", [])) if "interested" in listing else 0

        result.append(ListingResponse(**listing))

    return result

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing_by_id(listing_id: str):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing["id"] = str(listing["_id"])
    listing["posted_by"] = str(listing.get("posted_by", ""))
    listing["buyer_id"] = str(listing.get("buyer_id", ""))
    
    # Convert public_ids → optimized URLs
    image_ids = listing.get("images", [])
    listing["images"] = [get_optimized_image_url(pid) for pid in image_ids]

    return ListingResponse(**listing)

@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    update_data: ListingUpdate = Depends(),  # the base metadata updates
    images_to_keep: List[str] = Form([]),    # `public_id`s from frontend
    new_images: List[UploadFile] = File([]), # new files to upload
    user: TokenUser = Depends(get_current_user)
):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="You are not allowed to update this listing")

    # Handle image update logic
    existing_ids = listing.get("images", [])
    
    # 1. Delete removed public_ids from Cloudinary
    to_delete = list(set(existing_ids) - set(images_to_keep))
    for public_id in to_delete:
        cloudinary.uploader.destroy(public_id)

    # 2. Upload new images to Cloudinary
    new_image_ids = []
    for image in new_images:
        uploaded = await upload_image_to_cloudinary(image)
        new_image_ids.append(uploaded["public_id"])

    # 3. Final image list = kept + new
    final_image_ids = images_to_keep + new_image_ids

    # 4. Apply metadata updates
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["images"] = final_image_ids
    update_dict["updated_at"] = datetime.now(timezone.utc)

    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {"$set": update_dict}
    )

    return {
        "message": "Listing updated successfully ✅",
        "updated_images": [get_optimized_image_url(pid) for pid in final_image_ids]
    }

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

    # 🧹 Step 1: Delete all images from Cloudinary
    image_ids = listing.get("images", [])
    for public_id in image_ids:
        try:
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"⚠️ Failed to delete image: {public_id} — {e}")

    # 🗑️ Step 2: Delete the listing from DB
    await db.listings.delete_one({"_id": ObjectId(listing_id)})

    return {
        "message": "Listing deleted successfully 🗑️",
        "deleted_image_count": len(image_ids)
    }

@router.put("/{listing_id}/mark-sold")
async def mark_listing_as_sold(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="You are not allowed to update this listing")

    if listing.get("is_sold", False):
        return {"message": "This listing is already marked as sold"}

    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {
            "$set": {
                "is_sold": True,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return {"message": "Listing marked as sold ✅"}
    
@router.put("/mark-available/{listing_id}")
async def mark_listing_as_available(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="You're not allowed to modify this listing")

    if not listing.get("is_sold", False):
        raise HTTPException(status_code=400, detail="Listing is already available")

    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {
            "$set": {
                "is_sold": False,
                "buyer_id": None,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return {"message": "Listing marked as available again ✅"}

@router.get("/my-sold-listings", response_model=List[ListingOut])
async def get_my_sold_listings(user: TokenUser = Depends(get_current_user)):
    listings_cursor = db.listings.find({
        "posted_by": user.id,
        "is_sold": True
    }).sort("updated_at", -1)

    listings = await listings_cursor.to_list(length=100)
    return listings

# Temporary endpoint to trigger test
@router.get("/cleanup-test")
async def trigger_cleanup_test():
    from app.tasks.image_cleanup import delete_old_listing_images
    await delete_old_listing_images()
    return {"message": "Cleanup test triggered"}