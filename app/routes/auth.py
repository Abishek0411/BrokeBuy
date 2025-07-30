from collections import defaultdict
import traceback
from fastapi import APIRouter, HTTPException, Request, Depends
import asyncio  
import httpx # Use async-native httpx
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import get_current_user
from app.models.user import TokenUser
from pydantic import BaseModel
import requests
from datetime import datetime, timedelta, timezone
from app.database import db
from app.utils.auth import create_access_token
import requests
from bson import ObjectId

router = APIRouter()
SRM_SESSION_TTL_MINUTES = 20

class LoginRequest(BaseModel):
    account: str
    password: str

# In-memory lock to handle concurrent requests for the same user
login_locks = defaultdict(asyncio.Lock)

@router.post("/login")
async def login(data: LoginRequest):
    email = data.account
    user_lock = login_locks[email]

    try:
        async with user_lock:
            user = await db.users.find_one({"email": email})
            srm_token = None

            # Step 1: Check for a valid, reusable SRM session
            if user and "srm_session" in user:
                srm_data = user["srm_session"]
                expires_at = srm_data.get("expires_at")
                if expires_at and datetime.fromisoformat(expires_at) > datetime.now(timezone.utc):
                    srm_token = srm_data["token"]
                    print("✅ Reusing SRM session token")

            # Step 2: Login to SRM only if no valid session exists
            if not srm_token:
                async with httpx.AsyncClient() as client:
                    res = await client.post("http://localhost:9000/login", json=data.model_dump())
                
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail="SRM authentication service failed.")
                
                result = res.json()
                if not result.get("authenticated"):
                    raise HTTPException(status_code=401, detail="Invalid credentials provided.")
                
                srm_token = result["cookies"]

            # Step 3: Fetch profile and update DB if needed
            if not user or not user.get("srm_id"):
                async with httpx.AsyncClient() as client:
                    headers = {"X-CSRF-Token": srm_token}
                    profile_res = await client.get("http://localhost:9000/user", headers=headers)
                
                profile = profile_res.json()
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=SRM_SESSION_TTL_MINUTES)

                update_data = {
                    "email": email,
                    "srm_id": profile.get("srmId"),
                    "reg_no": profile.get("regNumber", ""),
                    "name": profile.get("name"),
                    "phone": profile.get("mobile", ""),
                    "avatar": profile.get("photoUrl", ""),
                    "role": "student",
                    "wallet_balance": user.get("wallet_balance", 0.0) if user else 0.0,
                    "srm_session": {
                        "token": srm_token,
                        "expires_at": expires_at.isoformat()
                    }
                }
                
                await db.users.update_one(
                    {"email": email},
                    {"$set": update_data},
                    upsert=True
                )
            
            final_user = await db.users.find_one({"email": email})

            # Step 4: Issue application access token
            access_token = create_access_token({
                "sub": str(final_user["_id"]),
                "email": final_user["email"],
                "role": final_user["role"]
            })

            return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        traceback.print_exc()
        # Re-raise as a standard HTTP exception
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

    finally:
        # --- YOUR SUGGESTION APPLIED ---
        # Safely clean up the lock to prevent memory leaks without crashing the request.
        try:
            if email in login_locks and not login_locks[email].locked():
                del login_locks[email]
        except Exception:
            pass # Don't let cleanup errors affect the response

    
@router.post("/logout")
# It still depends on get_current_user to run the auth and populate request.state
async def logout(request: Request, user: TokenUser = Depends(get_current_user)):
    try:
        # Access the full user document from the request state (NO new DB call)
        user_doc = request.state.user

        srm_session = user_doc.get("srm_session", {})
        token = srm_session.get("token")

        if not token:
            return {"message": "No active session to log out from."}
        
        async with httpx.AsyncClient() as client:
            headers = {"X-CSRF-Token": token}
            await client.delete("http://localhost:9000/logout", headers=headers)

        # Use the correct ObjectId from the full document
        await db.users.update_one(
            {"_id": user_doc["_id"]},
            {"$unset": {"srm_session": 1}}
        )

        return {"message": "Successfully logged out"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

