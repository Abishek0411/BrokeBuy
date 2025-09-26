import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Request
from app.models.listing import ListingResponse, ListingUpdate, ListingOut
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.utils.cloudinary import upload_image_to_cloudinary, get_optimized_image_url
from app.database import db
from pydantic import BaseModel
from cloudinary import uploader
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional

router = APIRouter(prefix="/listings", tags=["Listings"])

MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

def serialize_objectid(value):
    if isinstance(value, ObjectId):
        return str(value)
    elif isinstance(value, list):
        return [serialize_objectid(v) for v in value]
    elif isinstance(value, dict):
        return {k: serialize_objectid(v) for k, v in value.items()}
    return value

# Dependency function to extract form data for listing updates
async def get_listing_update_data(
    title: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    category: str = Form(None),
    condition: str = Form(None),
    location: str = Form(None)
) -> ListingUpdate:
    return ListingUpdate(
        title=title,
        description=description,
        price=price,
        category=category,
        condition=condition,
        location=location
    )

# ---------- Models ----------
class BuyRequestCreate(BaseModel):
    # optional note that buyer can send along
    note: Optional[str] = None

class BuyRequestOut(BaseModel):
    id: str
    listing_id: str
    seller_id: str
    buyer_id: str
    status: str
    created_at: str
    updated_at: str
    # extra hydrated fields for UI niceness
    listing_title: Optional[str] = None
    listing_image: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_reg_no: Optional[str] = None

# ---------- Helpers ----------
async def _notify(user_id: ObjectId, ntype: str, title: str, message: str, meta: Optional[dict] = None):
    """Minimal inline notification insert. If you already have a helper, use that instead."""
    doc = {
        "user_id": user_id,
        "type": ntype,  # "message" | "buy_request" | "system"
        "title": title,
        "message": message,
        "metadata": meta or {},
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.notifications.insert_one(doc)

def _oid(val: str) -> ObjectId:
    try:
        return ObjectId(val)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

@router.post("/create")
async def create_listing(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    condition: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    user: TokenUser = Depends(get_current_user)
):
    try:
        public_ids = []

        for file in images:
            # ⏳ Read file once and check size
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"One of the images is too large. Max allowed is 5MB."
                )

            # ✅ Upload to Cloudinary
            uploaded = await upload_image_to_cloudinary(content)
            public_ids.append(uploaded["public_id"])

        # 🧱 Construct listing
        listing = {
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "condition": condition,
            "location": location,
            "images": public_ids,
            "posted_by": user.id,
            "is_sold": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        result = await db.listings.insert_one(listing)

        return {
            "message": "Listing created ✅",
            "listing_id": str(result.inserted_id),
            "uploaded_images": public_ids  # optionally return URLs if you want
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create listing")

@router.get("/", response_model=List[dict])
async def get_all_listings(
    page: int = 1,
    limit: int = 20,
    include_sold: bool = False
):
    skip = (page - 1) * limit
    query = {} if include_sold else {"is_sold": False}

    listings_cursor = db.listings.find(query).skip(skip).limit(limit)
    listings = await listings_cursor.to_list(length=limit)

    # Step 1: Collect all seller IDs
    seller_ids = list(set(str(listing["posted_by"]) for listing in listings))
    sellers = await db.users.find(
        {"_id": {"$in": [ObjectId(uid) for uid in seller_ids]}},
        {"name": 1, "reg_no": 1}
    ).to_list(None)

    # Step 2: Build seller lookup map
    seller_map = {
        str(seller["_id"]): {
            "name": seller.get("name", "Unknown"),
            "reg_no": seller.get("reg_no", "N/A")
        }
        for seller in sellers
    }

    enriched = []
    for listing in listings:
        listing = serialize_objectid(listing)  # Convert all ObjectIds → str

        listing["id"] = listing.pop("_id", listing.get("id"))
        listing["seller"] = seller_map.get(listing["posted_by"], {"name": "Unknown", "reg_no": "N/A"})
        listing["created_at"] = listing.get("created_at", datetime.now(timezone.utc).isoformat())
        listing["is_available"] = not listing.get("is_sold", False)
        listing["is_sold"] = listing.get("is_sold", False)
        listing["images"] = [get_optimized_image_url(pid) for pid in listing.get("images", [])]

        enriched.append(listing)

    return enriched

# ---------- Buy Endpoints ----------

@router.post("/{listing_id}/buy-request", response_model=dict)
async def create_buy_request(
    listing_id: str,
    payload: Optional[BuyRequestCreate] = None,
    user: TokenUser = Depends(get_current_user),
):
    listing_obj_id = _oid(listing_id)

    listing = await db.listings.find_one({"_id": listing_obj_id})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    seller_id = listing["posted_by"]
    if str(seller_id) == str(user.id):
        raise HTTPException(status_code=400, detail="You cannot request to buy your own listing")

    if listing.get("is_sold"):
        raise HTTPException(status_code=400, detail="Listing already sold")

    existing = await db.purchase_requests.find_one({
        "listing_id": listing_obj_id,
        "buyer_id": _oid(user.id),
        "status": {"$in": ["pending", "accepted"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active request for this listing")

    now = datetime.now(timezone.utc)
    doc = {
        "listing_id": listing_obj_id,
        "seller_id": seller_id if isinstance(seller_id, ObjectId) else _oid(seller_id),
        "buyer_id": _oid(user.id),
        "note": (payload.note if payload and hasattr(payload, "note") else ""),
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    res = await db.purchase_requests.insert_one(doc)

    # --- Auto-create notification for seller ---
    buyer = await db.users.find_one({"_id": _oid(user.id)}, {"name": 1, "reg_no": 1})
    title = "Buying Request"
    msg = f"{buyer.get('name', 'A buyer')} requested to purchase: {listing.get('title', 'listing')}"
    await _notify(
        _oid(seller_id) if not isinstance(seller_id, ObjectId) else seller_id,
        "buy_request",
        title,
        msg,
        meta={
            "listing_id": str(listing_obj_id),
            "buyer_id": str(user.id),
            "request_id": str(res.inserted_id),
            "listing_title": listing.get("title"),
            "listing_image": get_optimized_image_url((listing.get("images") or [None])[0]) if listing.get("images") else None
        }
    )

     # --- Auto-create notification for buyer ---
    buyer_notification_meta = {
        "listing_id": str(listing_obj_id),
        "seller_id": str(seller_id),
        "request_id": str(res.inserted_id),
        "listing_title": listing.get("title"),
        "listing_image": get_optimized_image_url((listing.get("images") or [None])[0]) if listing.get("images") else None
    }

    await _notify(
        _oid(user.id),
        "system",
        "Request Sent",
        f"Your buying request for {listing.get('title', 'listing')} has been sent to the seller.",
        meta=buyer_notification_meta
    )

    return {"message": "Buy request sent to seller ✅", "request_id": str(res.inserted_id)}

@router.get("/{listing_id}/buy-requests", response_model=List[BuyRequestOut])
async def list_buy_requests_for_listing(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    listing_obj_id = _oid(listing_id)

    listing = await db.listings.find_one({"_id": listing_obj_id})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Only seller can view requests for their listing
    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view requests for this listing")

    cursor = db.purchase_requests.find({"listing_id": listing_obj_id}).sort("created_at", -1)
    reqs = await cursor.to_list(length=None)

    # Hydrate for UI
    out: List[BuyRequestOut] = []
    # Pull listing essentials once
    listing_title = listing.get("title")
    listing_image = get_optimized_image_url((listing.get("images") or [None])[0]) if listing.get("images") else None

    # Batch buyer lookup
    buyer_ids = list({r["buyer_id"] for r in reqs})
    buyers = await db.users.find({"_id": {"$in": buyer_ids}}, {"name": 1, "reg_no": 1}).to_list(None)
    buyers_map = {b["_id"]: b for b in buyers}

    for r in reqs:
        buyer_doc = buyers_map.get(r["buyer_id"], {})
        out.append(BuyRequestOut(
            id=str(r["_id"]),
            listing_id=str(r["listing_id"]),
            seller_id=str(r["seller_id"]),
            buyer_id=str(r["buyer_id"]),
            status=r.get("status", "pending"),
            created_at=r["created_at"].isoformat(),
            updated_at=r["updated_at"].isoformat(),
            listing_title=listing_title,
            listing_image=listing_image,
            buyer_name=buyer_doc.get("name"),
            buyer_reg_no=buyer_doc.get("reg_no")
        ))

    return out

@router.post("/{listing_id}/buy-requests/{request_id}/accept", response_model=dict)
async def accept_buy_request(
    listing_id: str,
    request_id: str,
    user: TokenUser = Depends(get_current_user)
):
    listing_obj_id = _oid(listing_id)
    req_obj_id = _oid(request_id)

    listing = await db.listings.find_one({"_id": listing_obj_id})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Only seller can accept
    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="Only the seller can accept a request")

    if listing.get("is_sold"):
        raise HTTPException(status_code=400, detail="Listing already sold")

    req = await db.purchase_requests.find_one({"_id": req_obj_id, "listing_id": listing_obj_id})
    if not req:
        raise HTTPException(status_code=404, detail="Buy request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {req.get('status')}")

    # Ensure IDs are ObjectId
    buyer_id = req["buyer_id"]
    if not isinstance(buyer_id, ObjectId):
        buyer_id = ObjectId(buyer_id)

    seller_id = listing["posted_by"]
    if not isinstance(seller_id, ObjectId):
        seller_id = ObjectId(seller_id)
    price = float(listing["price"])

    # Re-check buyer funds
    buyer_doc = await db.users.find_one({"_id": buyer_id}, {"wallet_balance": 1, "name": 1})
    if not buyer_doc:
        raise HTTPException(status_code=404, detail="Buyer not found")

    if float(buyer_doc.get("wallet_balance", 0.0)) < price:
        # Auto-decline with reason; notify buyer to top-up
        await db.purchase_requests.update_one(
            {"_id": req_obj_id},
            {"$set": {"status": "declined", "updated_at": datetime.now(timezone.utc), "decline_reason": "Insufficient funds"}}
        )
        await _notify(
            buyer_id,
            "buy_request",
            "Buy Request Declined",
            f"Your buy request for '{listing.get('title')}' was declined: Insufficient funds. Please top-up and try again.",
            meta={"listing_id": str(listing_obj_id), "request_id": str(req_obj_id)}
        )
        raise HTTPException(status_code=400, detail="Buyer has insufficient wallet balance")

    now = datetime.now(timezone.utc)

    # 1) Mark request accepted
    await db.purchase_requests.update_one(
        {"_id": req_obj_id},
        {"$set": {"status": "accepted", "updated_at": now}}
    )
    # Delete the original buy_request notification for this request
    await db.notifications.delete_many({
        "receiver_id": seller_id,
        "metadata.request_id": str(req_obj_id)
    })
    # 2) Debit buyer
    await db.users.update_one(
        {"_id": buyer_id},
        {"$inc": {"wallet_balance": -price}}
    )
    await db.wallet_history.insert_one({
        "user_id": buyer_id,
        "type": "debit",
        "amount": price,
        "ref_note": f"Purchased listing: {listing.get('title')}",
        "timestamp": now
    })

    # 3) Credit seller (IGNORE 50K cap for sales)
    await db.users.update_one(
        {"_id": seller_id},
        {"$inc": {"wallet_balance": price}}
    )
    await db.wallet_history.insert_one({
        "user_id": seller_id,
        "type": "credit",
        "amount": price,
        "ref_note": f"Sold listing: {listing.get('title')}",
        "timestamp": now
    })

    # 4) Mark listing as sold
    await db.listings.update_one(
        {"_id": listing_obj_id},
        {"$set": {"is_sold": True, "buyer_id": buyer_id, "sold_at": now, "updated_at": now}}
    )

    # 5) Auto-decline all other pending requests for this listing
    other_pending = db.purchase_requests.find({
        "listing_id": listing_obj_id,
        "status": "pending",
        "_id": {"$ne": req_obj_id}
    })
    others = await other_pending.to_list(length=None)
    if others:
        other_ids = [r["_id"] for r in others]
        await db.purchase_requests.update_many(
            {"_id": {"$in": other_ids}},
            {"$set": {"status": "declined", "updated_at": now, "decline_reason": "Another buyer accepted"}}
        )
        # notify those buyers
        for r in others:
            await _notify(
                r["buyer_id"],
                "buy_request",
                "Buy Request Declined",
                f"Your buy request for '{listing.get('title')}' was declined because the item was sold to another buyer.",
                meta={"listing_id": str(listing_obj_id), "request_id": str(r["_id"])}
            )

    # 6) Notify buyer of acceptance
    await _notify(
        buyer_id,
        "system",  # <-- changed from "buy_request"
        "Buy Request Accepted 🎉",
        f"Your request to buy '{listing.get('title')}' was accepted. Amount ₹{price:.0f} has been debited and the item is now yours.",
        meta={"listing_id": str(listing_obj_id), "request_id": str(req_obj_id)}
    )

    return {"message": "Request accepted and purchase completed ✅"}

@router.post("/{listing_id}/buy-requests/{request_id}/decline", response_model=dict)
async def decline_buy_request(
    listing_id: str,
    request_id: str,
    user: TokenUser = Depends(get_current_user),
    reason: Optional[str] = Body(default=None, embed=True)
):
    listing_obj_id = _oid(listing_id)
    req_obj_id = _oid(request_id)

    listing = await db.listings.find_one({"_id": listing_obj_id})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Only seller can decline
    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="Only the seller can decline a request")

    req = await db.purchase_requests.find_one({"_id": req_obj_id, "listing_id": listing_obj_id})
    if not req:
        raise HTTPException(status_code=404, detail="Buy request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {req.get('status')}")

    now = datetime.now(timezone.utc)
    await db.purchase_requests.update_one(
        {"_id": req_obj_id},
        {"$set": {"status": "declined", "updated_at": now, "decline_reason": reason or "Declined by seller"}}
    )
    # Delete the original buy_request notification for this request
    await db.notifications.delete_many({
        "receiver_id": ObjectId(user.id),
        "metadata.request_id": str(req_obj_id)
    })

    # notify buyer
    await _notify(
        req["buyer_id"],
        "system",  # <-- FIXED
        "Buy Request Declined",
        f"Your buy request for '{listing.get('title')}' was declined.",
        meta={
            "listing_id": str(listing_obj_id),
            "request_id": str(req_obj_id),
            "reason": reason or "Declined by seller"
        }
    )

    return {"message": "Request declined"}

@router.post("/buy/{listing_id}", response_model=dict)
async def buy_listing(listing_id: str, user=Depends(get_current_user)):
    buyer_id = ObjectId(user.id)  # ensure buyer ObjectId
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing["is_sold"]:
        raise HTTPException(status_code=400, detail="Listing already sold")
    
    if listing["posted_by"] == user.id:
        raise HTTPException(status_code=400, detail="You can't buy your own listing")
    
    user_data = await db.users.find_one({"_id": buyer_id})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    user_wallet = user_data.get("wallet_balance", 0.0)
    price = float(listing["price"])

    if user_wallet < price:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")
    
    now = datetime.now(timezone.utc)

    # Deduct from buyer wallet
    result = await db.users.update_one(
        {"_id": buyer_id},
        {"$inc": {"wallet_balance": -price}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to deduct from buyer wallet")

    await db.wallet_history.insert_one({
        "user_id": buyer_id,
        "type": "debit",
        "amount": price,
        "ref_note": f"Purchased listing: {listing['title']}",
        "timestamp": now
    })

    # ✅ Credit seller wallet
    seller_id = listing["posted_by"]
    if not isinstance(seller_id, ObjectId):
        seller_id = ObjectId(seller_id)

    credit_result = await db.users.update_one(
        {"_id": seller_id},
        {"$inc": {"wallet_balance": price}}
    )
    if credit_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to credit seller wallet")

    await db.wallet_history.insert_one({
        "user_id": seller_id,
        "type": "credit",
        "amount": price,
        "ref_note": f"Sold listing: {listing['title']}",
        "timestamp": now
    })

    # Mark listing as sold
    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {
            "$set": {
                "is_sold": True,
                "buyer_id": str(buyer_id),
                "sold_at": now,
                "updated_at": now
            }
        }
    )

    return {"message": "Listing purchased successfully ✅"}

@router.get("/purchased", response_model=List[ListingResponse])
async def get_purchased_listings(user: TokenUser = Depends(get_current_user)):
    pipeline = [
        {"$match": {
            "$or": [
                {"buyer_id": user.id},
                {"buyer_id": ObjectId(user.id)}
            ]
        }},
        {"$addFields": {
            "posted_by_obj": {
                "$cond": {
                    "if": {"$ne": ["$posted_by", None]},
                    "then": {"$toObjectId": "$posted_by"},
                    "else": None
                }
            }
        }},
        {"$lookup": {
            "from": "users",
            "localField": "posted_by_obj",
            "foreignField": "_id",
            "as": "seller_info"
        }},
        {"$unwind": {
            "path": "$seller_info",
            "preserveNullAndEmptyArrays": True
        }}
    ]

    listings = await db.listings.aggregate(pipeline).to_list(length=None)
    result = []

    for listing in listings:
        listing["id"] = str(listing["_id"])
        listing["posted_by"] = str(listing.get("posted_by", ""))
        listing["buyer_id"] = str(listing.get("buyer_id", ""))
        listing["is_available"] = not listing.get("is_sold", False)
        listing["created_at"] = listing.get("created_at", datetime.now(timezone.utc))
        listing["updated_at"] = listing.get("updated_at", datetime.now(timezone.utc))
        listing["images"] = [get_optimized_image_url(pid) for pid in listing.get("images", [])]
        listing["condition"] = listing.get("condition")
        listing["location"] = listing.get("location")

        seller = listing.get("seller_info", {})
        listing["seller_name"] = seller.get("name", "Unknown")
        listing["seller_reg_no"] = seller.get("reg_no", "N/A")

        result.append(ListingResponse(**listing))

    return result

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

@router.get("/my-listings", response_model=List[ListingResponse])
async def get_my_listings(user: TokenUser = Depends(get_current_user)):
    listings = await db.listings.find({"posted_by": user.id}).to_list(length=None)
    result = []
    for listing in listings:
        listing["id"] = str(listing["_id"])
        listing["posted_by"] = str(listing.get("posted_by", ""))
        listing["buyer_id"] = str(listing.get("buyer_id", ""))
        listing["created_at"] = listing.get("created_at", datetime.now(timezone.utc).isoformat())
        listing["updated_at"] = listing.get("updated_at", datetime.now(timezone.utc).isoformat())
        listing["is_available"] = not listing.get("is_sold", False)
        listing["images"] = [get_optimized_image_url(pid) for pid in listing.get("images", [])]
        
        # 🛠️ Add missing fields for frontend
        listing["views"] = listing.get("views", 0)
        listing["interested_users"] = len(listing.get("interested", [])) if "interested" in listing else 0

        # Optional fields
        listing["condition"] = listing.get("condition")
        listing["location"] = listing.get("location")
        listing["seller_name"] = user.email.split('@')[0].title()  # fallback
        listing["seller_reg_no"] = "Private"

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
        listing["is_available"] = not listing.get("is_sold", False)
        listing["created_at"] = listing.get("created_at", datetime.now(timezone.utc))
        listing["updated_at"] = listing.get("updated_at", datetime.now(timezone.utc))
        listing["images"] = [get_optimized_image_url(pid) for pid in listing.get("images", [])]

        listing["condition"] = listing.get("condition")
        listing["location"] = listing.get("location")

        # Lookup seller info
        try:
            seller = await db.users.find_one(
                {"_id": ObjectId(listing["posted_by"])},
                {"name": 1, "reg_no": 1}
            )
            listing["seller_name"] = seller.get("name", "Unknown") if seller else "Unknown"
            listing["seller_reg_no"] = seller.get("reg_no", "N/A") if seller else "N/A"
        except:
            listing["seller_name"] = "Unknown"
            listing["seller_reg_no"] = "N/A"

        result.append(ListingResponse(**listing))

    return result

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing_by_id(listing_id: str):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Format basic fields
    listing["id"] = str(listing["_id"])
    listing["posted_by"] = str(listing.get("posted_by", ""))
    listing["buyer_id"] = str(listing.get("buyer_id", "")) if listing.get("buyer_id") else None
    listing["is_available"] = not listing.get("is_sold", False)
    listing["created_at"] = listing.get("created_at", datetime.now(timezone.utc))
    listing["updated_at"] = listing.get("updated_at", datetime.now(timezone.utc))
    listing["images"] = [get_optimized_image_url(pid) for pid in listing.get("images", [])]
    listing["condition"] = listing.get("condition")
    listing["location"] = listing.get("location")
    listing["is_sold"] = listing.get("is_sold", False)

    # ✅ Inject seller_name and seller_reg_no for existing response model
    try:
        seller = await db.users.find_one(
            {"_id": ObjectId(listing["posted_by"])},
            {"name": 1, "reg_no": 1}
        )
        listing["seller_name"] = seller.get("name", "Unknown") if seller else "Unknown"
        listing["seller_reg_no"] = seller.get("reg_no", "N/A") if seller else "N/A"
    except Exception:
        listing["seller_name"] = "Unknown"
        listing["seller_reg_no"] = "N/A"

    return ListingResponse(**listing)

@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    update_data: ListingUpdate = Depends(get_listing_update_data),  # the base metadata updates
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
        uploader.destroy(public_id)

    # 2. Upload new images to Cloudinary
    new_image_ids = []
    for image in new_images:
        uploaded = await upload_image_to_cloudinary(await image.read())
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
            await asyncio.to_thread(uploader.destroy, public_id)
        except Exception as e:
            print(f"⚠️ Failed to delete image: {public_id} — {e}")

    # 🗑️ Step 2: Delete the listing from DB
    await db.listings.delete_one({"_id": ObjectId(listing_id)})

    return {
        "message": "Listing deleted successfully 🗑️",
        "deleted_image_count": len(image_ids)
    }

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

@router.put("/mark-unavailable/{listing_id}")
async def mark_listing_as_unavailable(
    listing_id: str,
    user: TokenUser = Depends(get_current_user)
):
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if str(listing["posted_by"]) != str(user.id):
        raise HTTPException(status_code=403, detail="You're not allowed to modify this listing")

    if listing.get("is_sold", False):
        raise HTTPException(status_code=400, detail="Listing is already marked as unavailable")

    await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {
            "$set": {
                "is_sold": True,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return {"message": "Listing marked as unavailable ✅"}

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