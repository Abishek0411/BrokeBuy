from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_403_FORBIDDEN
from app.utils.auth import decode_access_token

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            try:
                payload = decode_access_token(credentials.credentials)
                request.state.user = payload
                return credentials.credentials
            except Exception as e:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid auth token")
