from fastapi import APIRouter, HTTPException, status, Request, Depends
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

@router.post("/login")
async def login(data: LoginRequest):
    try:
        email = data.account
        password = data.password

        # Step 1: Attempt login to SRM always
        res = requests.post("http://localhost:9000/login", json=data.model_dump())
        result = res.json()

        if not result.get("authenticated"):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        srm_token = result["cookies"]
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=SRM_SESSION_TTL_MINUTES)

        # Step 2: Upsert session in DB
        await db.users.update_one(
            {"email": email},
            {"$set": {
                "srm_session": {
                    "token": srm_token,
                    "expires_at": expires_at.isoformat()
                }
            }},
            upsert=True
        )

        # Step 3: If new user, fetch SRM profile
        srm_user = await db.users.find_one({"email": email})
        if not srm_user or not srm_user.get("srm_id"):
            headers = {"X-CSRF-Token": srm_token}
            profile = requests.get("http://localhost:9000/user", headers=headers).json()

            new_user_data = {
                "email": email,
                "srm_id": profile.get("srmId") or result["lookup"]["identifier"],
                "reg_no": profile.get("regNumber", ""),
                "name": profile.get("name"),
                "phone": profile.get("mobile", ""),
                "avatar": profile.get("photoUrl", ""),
                "role": "student",
                "wallet_balance": 0.0,
                "srm_session": {
                    "token": srm_token,
                    "expires_at": expires_at.isoformat()
                }
            }

            await db.users.update_one(
                {"email": email},
                {"$set": new_user_data},
                upsert=True
            )
            srm_user = await db.users.find_one({"email": email})

        # Step 4: Create JWT token
        access_token = create_access_token({
            "sub": str(srm_user["_id"]),
            "email": srm_user["email"],
            "role": srm_user["role"]
        })

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    
@router.post("/logout")
async def logout(user: TokenUser = Depends(get_current_user)):
    try:
        # Get token from DB if stored
        user_doc = await db.users.find_one({"_id": ObjectId(user.id)})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        token = user_doc.get("srm_session", {}).get("token")
        if not token:
            raise HTTPException(status_code=400, detail="No active session found")

        # Forward logout request to academia scraper
        headers = {"X-CSRF-Token": token}
        res = requests.delete("http://localhost:9000/logout", headers=headers)

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to logout from SRM")

        # Remove session token from DB
        await db.users.update_one({"_id": user.id}, {"$unset": {"srm_session": 1}})

        return {"message": "Successfully logged out"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

