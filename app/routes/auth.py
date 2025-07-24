from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import get_current_user
from app.models.user import TokenUser
from pydantic import BaseModel
import requests
from app.database import db
from app.utils.auth import create_access_token
import requests

router = APIRouter()

class LoginRequest(BaseModel):
    account: str
    password: str

@router.post("/login")
async def login(data: LoginRequest):
    try:
        res = requests.post("http://localhost:9000/login", json=data.model_dump())
        result = res.json()

        if not result.get("authenticated"):
            raise HTTPException(status_code=401, detail="SRM login failed")

        token = result["cookies"]
        headers = {"X-CSRF-Token": token}

        # 🔥 Fetch /user profile info from SRM
        user_profile = requests.get("http://localhost:9000/user", headers=headers).json()

        srm_id = result["lookup"]["identifier"]
        email = result["lookup"]["loginid"]
        name = user_profile.get("name")
        mobile = user_profile.get("mobile", "")
        reg_no = user_profile.get("regNumber", "")
        photo = user_profile.get("photoUrl", "")

        user = await db.users.find_one({"email": email})

        if not user:
            user_data = {
                "email": email,
                "srm_id": srm_id,
                "reg_no": reg_no,
                "name": name,
                "phone": mobile,
                "avatar": photo,
                "role": "student",
                "wallet_balance": 0.0
            }
            insert_result = await db.users.insert_one(user_data)
            user = await db.users.find_one({"_id": insert_result.inserted_id})
        else:
            # Optional: Update profile fields if user already exists
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "name": name,
                    "reg_no": reg_no,
                    "phone": mobile,
                    "avatar": photo
                }}
            )

        # 🔐 Create and return JWT
        access_token = create_access_token({
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"]
        })

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    
@router.post("/logout")
async def logout(user: TokenUser = Depends(get_current_user)):
    try:
        # Forward the logout call to academia scraper
        headers = {"X-CSRF-Token": user.srm_token}
        res = requests.delete("http://localhost:9000/logout", headers=headers)

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to logout from SRM")

        return {"message": "Successfully logged out"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
