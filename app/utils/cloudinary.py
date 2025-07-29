import asyncio
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
    if public_id.startswith("http"):
        return public_id
    
    # Construct the URL with transformations
    transformations = "w_400,c_scale,f_auto,q_auto"
    return f"{BASE_URL}/{transformations}/{public_id}"

# --- Refactored Async Upload Helper ---
async def upload_image_to_cloudinary(file_contents: bytes):
    """
    Runs the synchronous Cloudinary upload function in a separate thread 
    to avoid blocking the main asyncio event loop.
    """
    try:
        # Use asyncio.to_thread to run the blocking call
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            file_contents,
            folder="BrokeBuyListings"
        )
        public_id = result["public_id"]
        optimized_url = get_optimized_image_url(public_id)
        
        return {
            "public_id": public_id,
            "optimized_url": optimized_url
        }
    except Exception as e:
        # Propagate exceptions to be caught by the endpoint handler
        raise e
