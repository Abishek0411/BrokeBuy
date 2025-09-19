from fastapi import FastAPI
from app.routes import auth, listings, messages, users, wallet, admin, notifications
from app.tasks.image_cleanup import AsyncIOScheduler, delete_old_listing_images
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://127.0.0.1:8080",  
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://pk5vnpvw-8080.inc1.devtunnels.ms/", 
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(wallet.router)
app.include_router(admin.router, prefix="/admin")
app.include_router(listings.router)
app.include_router(notifications.router)

# Initialize scheduler
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    """Start the cleanup scheduler when the app starts"""
    scheduler.add_job(delete_old_listing_images, "interval", days=1)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler when the app shuts down"""
    scheduler.shutdown()

@app.get("/test")
def test_route():
    return {"message": "Hey, it's working!"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    try:
        # Test database connection
        from app.database import client
        await client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
