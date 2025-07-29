from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
import cloudinary
import cloudinary.uploader
from app.database import db
import os

# Set Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def get_tiny_thumbnail_url(public_id: str):
    return f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload/w_100,h_100,c_fill,f_webp,q_10/{public_id}.jpg"

async def delete_old_listing_images():
    print("🔁 Running auto-cleanup job...")

    now = datetime.now(timezone.utc)
    grace_period_days = 14

    listings = await db.listings.find({
        "is_sold": True,
        "sold_at": {"$lt": now - timedelta(days=grace_period_days)}
    }).to_list(length=None)

    for listing in listings:
        image_ids = listing.get("images", [])
        if not image_ids or len(image_ids) == 0:
            continue

        keep_id = image_ids[0]
        try:
            # Delete all except the first one
            for pid in image_ids[1:]:
                cloudinary.uploader.destroy(pid)

            # Replace all with just the tiny thumbnail one
            await db.listings.update_one(
                {"_id": listing["_id"]},
                {"$set": {"images": [keep_id]}}
            )
            print(f"🧼 Cleaned up listing {listing['_id']} → kept: {keep_id}")
        except Exception as e:
            print(f"❌ Error cleaning up {listing['_id']}: {e}")

def start_cleanup_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(delete_old_listing_images, "interval", days=1)
    scheduler.start()
