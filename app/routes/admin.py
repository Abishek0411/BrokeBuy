from fastapi import APIRouter

router = APIRouter()

@router.get("/me")
async def get_my_profile():
    return {"message": "user profile stub"}
