from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
import requests
from app.database import db
from app.utils.auth import create_access_token
import os

router = APIRouter()

class LoginRequest(BaseModel):
    account: str
    password: str

@router.post("/login")
async def login(data: LoginRequest):
    try:
        res = requests.post("http://localhost:9000/login", json=data.model_dump())
        print(f"SRM response: {res.status_code}, {res.text}")
        result = res.json()

        if not result.get("authenticated"):
            raise HTTPException(status_code=401, detail="SRM login failed")

        srm_id = result["lookup"]["identifier"]
        email = result["lookup"]["loginid"]

        print(f"Authenticated user: {email} | ID: {srm_id}")

        # 🔍 Check if DB connection is okay
        user = await db.users.find_one({"email": email})
        print(f"User in DB: {user}")

        if not user:
            user_data = {
                "email": email,
                "srm_id": srm_id,
                "role": "student",
                "wallet": 0.0,
                "avatar": "",
                "name": email.split("@")[0]
            }
            insert_result = await db.users.insert_one(user_data)
            print(f"User created: {insert_result.inserted_id}")

            user = await db.users.find_one({"_id": insert_result.inserted_id})

        # ✅ Create JWT
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