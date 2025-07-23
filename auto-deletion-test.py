import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

client = AsyncIOMotorClient(MONGO_URI)
db = client["broke_buy"]  # or whatever your db name is

def get_tiny_thumbnail_url(public_id: str) -> str:
    return f"https://res.cloudinary.com/{CLOUD_NAME}/image/upload/w_100,h_100,c_fill,q_10,f_webp/{public_id}.jpg"

async def delete_old_listing_images():
    print("🔁 Running auto-cleanup job...")

    cutoff_time = datetime.now(timezone.utc) - timedelta(days=14)
    listings = await db.listings.find({
        "is_sold": True,
        "sold_at": {"$lte": cutoff_time}
    }).to_list(length=None)

    for listing in listings:
        public_ids = listing.get("images", [])
        if not public_ids:
            continue

        # Delete all except the first one (keep it as thumbnail)
        to_delete = public_ids[1:]
        thumbnail = public_ids[0]

        # Delete originals
        for pid in to_delete:
            try:
                cloudinary.uploader.destroy(pid)
                print(f"🗑️ Deleted: {pid}")
            except Exception as e:
                print(f"❌ Failed to delete {pid}: {e}")

        # Replace with only the thumbnail
        new_url = get_tiny_thumbnail_url(thumbnail)
        await db.listings.update_one(
            {"_id": listing["_id"]},
            {"$set": {"images": [thumbnail], "optimized_images": [new_url]}}
        )
        print(f"✅ Kept thumbnail: {thumbnail}")

async def main():
    try:
        print("MongoDB connection successful")
        await delete_old_listing_images()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
