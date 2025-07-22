import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
BASE_URL = f"https://res.cloudinary.com/{CLOUD_NAME}/image/upload"

def get_optimized_image_url(public_id: str) -> str:
    # If it's already a full URL, return as is
    if public_id.startswith("http://") or public_id.startswith("https://"):
        return public_id

    # Use the public_id as-is (includes folder already)
    return (
        f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload"
        f"/w_400,c_scale,f_auto,q_auto/{public_id}"
    )

async def upload_image_to_cloudinary(file):
    result = cloudinary.uploader.upload(file.file, folder="BrokeBuyListings")
    public_id = result["public_id"]
    optimized_url = get_optimized_image_url(public_id)
    return {
        "public_id": public_id,
        "optimized_url": optimized_url
    }
