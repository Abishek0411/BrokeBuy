from fastapi import FastAPI
from app.routes import auth, listings, messages, users, wallet, admin
from app.tasks.image_cleanup import start_cleanup_scheduler

app = FastAPI()

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(wallet.router)
app.include_router(admin.router, prefix="/admin")
app.include_router(listings.router)
start_cleanup_scheduler()