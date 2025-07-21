import jwt
from datetime import datetime, timedelta, timezone
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.database import db
from bson import ObjectId
from pydantic import BaseModel

class TokenUser(BaseModel):
    id: str
    email: str
    role: str
    wallet_balance: float = 0.0

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # This is just a dummy path; it's required

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("🔑 Decoded JWT payload:", payload)
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
    
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenUser:
    try:
        payload = decode_access_token(token)
        print("✅ Decoded JWT payload:", payload)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return TokenUser(
            id=str(user["_id"]),
            email=user["email"],
            role=user.get("role", "student"),
            wallet_balance=user.get("wallet_balance", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
