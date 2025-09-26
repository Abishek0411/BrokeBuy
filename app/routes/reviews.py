from fastapi import APIRouter, Depends, HTTPException
from app.models.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.utils.sanitizer import InputSanitizer
from app.database import db
from bson import ObjectId
from datetime import datetime, timezone
from typing import List

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=ReviewResponse)
async def create_review(
    review_data: ReviewCreate,
    user: TokenUser = Depends(get_current_user)
):
    """Create a review for a listing (only if user purchased it)"""
    
    # 1. Sanitize input
    comment = InputSanitizer.sanitize_text(review_data.comment, max_length=500)
    
    # 2. Check if listing exists
    listing = await db.listings.find_one({"_id": ObjectId(review_data.listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # 3. Check if user actually purchased this listing
    purchase_verified = await db.listings.find_one({
        "_id": ObjectId(review_data.listing_id),
        "buyer_id": user.id,
        "is_sold": True
    })
    
    if not purchase_verified:
        raise HTTPException(
            status_code=403, 
            detail="You can only review items you have purchased"
        )
    
    # 4. Check if user already reviewed this listing
    existing_review = await db.reviews.find_one({
        "listing_id": ObjectId(review_data.listing_id),
        "reviewer_id": ObjectId(user.id)
    })
    
    if existing_review:
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this item"
        )
    
    # 5. Create review
    review_doc = {
        "listing_id": ObjectId(review_data.listing_id),
        "reviewer_id": ObjectId(user.id),
        "rating": review_data.rating,
        "comment": comment,
        "is_verified": True,  # Since we verified the purchase
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.reviews.insert_one(review_doc)
    
    # 6. Get reviewer info for response
    reviewer = await db.users.find_one(
        {"_id": ObjectId(user.id)},
        {"name": 1, "reg_no": 1}
    )
    
    return ReviewResponse(
        id=str(result.inserted_id),
        listing_id=review_data.listing_id,
        reviewer_id=user.id,
        reviewer_name=reviewer.get("name", "Unknown"),
        reviewer_reg_no=reviewer.get("reg_no", "N/A"),
        rating=review_data.rating,
        comment=comment,
        created_at=review_doc["created_at"],
        is_verified=True
    )

@router.get("/listing/{listing_id}", response_model=List[ReviewResponse])
async def get_listing_reviews(listing_id: str):
    """Get all reviews for a specific listing"""
    
    # Check if listing exists
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Get reviews
    reviews_cursor = db.reviews.find(
        {"listing_id": ObjectId(listing_id)}
    ).sort("created_at", -1)
    
    reviews = await reviews_cursor.to_list(length=None)
    
    # Get reviewer info for each review
    reviewer_ids = [review["reviewer_id"] for review in reviews]
    reviewers = await db.users.find(
        {"_id": {"$in": reviewer_ids}},
        {"name": 1, "reg_no": 1}
    ).to_list(length=None)
    
    reviewer_map = {
        str(reviewer["_id"]): {
            "name": reviewer.get("name", "Unknown"),
            "reg_no": reviewer.get("reg_no", "N/A")
        }
        for reviewer in reviewers
    }
    
    result = []
    for review in reviews:
        reviewer_info = reviewer_map.get(str(review["reviewer_id"]), {"name": "Unknown", "reg_no": "N/A"})
        
        result.append(ReviewResponse(
            id=str(review["_id"]),
            listing_id=str(review["listing_id"]),
            reviewer_id=str(review["reviewer_id"]),
            reviewer_name=reviewer_info["name"],
            reviewer_reg_no=reviewer_info["reg_no"],
            rating=review["rating"],
            comment=review["comment"],
            created_at=review["created_at"],
            is_verified=review.get("is_verified", False)
        ))
    
    return result

@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    user: TokenUser = Depends(get_current_user)
):
    """Update a review (only by the reviewer)"""
    
    # 1. Check if review exists and belongs to user
    review = await db.reviews.find_one({
        "_id": ObjectId(review_id),
        "reviewer_id": ObjectId(user.id)
    })
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found or you don't have permission to edit it")
    
    # 2. Prepare update data
    update_data = {}
    
    if review_data.rating is not None:
        update_data["rating"] = review_data.rating
    
    if review_data.comment is not None:
        update_data["comment"] = InputSanitizer.sanitize_text(review_data.comment, max_length=500)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # 3. Update review
    await db.reviews.update_one(
        {"_id": ObjectId(review_id)},
        {"$set": update_data}
    )
    
    # 4. Get updated review
    updated_review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    
    # 5. Get reviewer info
    reviewer = await db.users.find_one(
        {"_id": ObjectId(user.id)},
        {"name": 1, "reg_no": 1}
    )
    
    return ReviewResponse(
        id=str(updated_review["_id"]),
        listing_id=str(updated_review["listing_id"]),
        reviewer_id=str(updated_review["reviewer_id"]),
        reviewer_name=reviewer.get("name", "Unknown"),
        reviewer_reg_no=reviewer.get("reg_no", "N/A"),
        rating=updated_review["rating"],
        comment=updated_review["comment"],
        created_at=updated_review["created_at"],
        is_verified=updated_review.get("is_verified", False)
    )

@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    user: TokenUser = Depends(get_current_user)
):
    """Delete a review (only by the reviewer)"""
    
    # Check if review exists and belongs to user
    review = await db.reviews.find_one({
        "_id": ObjectId(review_id),
        "reviewer_id": ObjectId(user.id)
    })
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found or you don't have permission to delete it")
    
    # Delete review
    await db.reviews.delete_one({"_id": ObjectId(review_id)})
    
    return {"message": "Review deleted successfully"}

@router.get("/my-reviews", response_model=List[ReviewResponse])
async def get_my_reviews(user: TokenUser = Depends(get_current_user)):
    """Get all reviews by the current user"""
    
    reviews_cursor = db.reviews.find(
        {"reviewer_id": ObjectId(user.id)}
    ).sort("created_at", -1)
    
    reviews = await reviews_cursor.to_list(length=None)
    
    # Get reviewer info
    reviewer = await db.users.find_one(
        {"_id": ObjectId(user.id)},
        {"name": 1, "reg_no": 1}
    )
    
    result = []
    for review in reviews:
        result.append(ReviewResponse(
            id=str(review["_id"]),
            listing_id=str(review["listing_id"]),
            reviewer_id=str(review["reviewer_id"]),
            reviewer_name=reviewer.get("name", "Unknown"),
            reviewer_reg_no=reviewer.get("reg_no", "N/A"),
            rating=review["rating"],
            comment=review["comment"],
            created_at=review["created_at"],
            is_verified=review.get("is_verified", False)
        ))
    
    return result
