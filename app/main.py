from fastapi import FastAPI
from app.routes import auth, listings, messages, users, wallet, admin, notifications
from app.tasks.image_cleanup import start_cleanup_scheduler
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://127.0.0.1:8080",  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(wallet.router)
app.include_router(admin.router, prefix="/admin")
app.include_router(listings.router)
app.include_router(notifications.router)
start_cleanup_scheduler()

@app.get("/test")
def test_route():
    return {"message": "Hey, it's working!"}
