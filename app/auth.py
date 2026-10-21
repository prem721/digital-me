import hmac
import time

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import JWT_SECRET, OWNER_PASSWORD, TOKEN_HOURS

bearer = HTTPBearer(auto_error=False)


def auth_configured() -> bool:
    return bool(OWNER_PASSWORD and JWT_SECRET)


def verify_password(password: str) -> bool:
    # constant-time comparison avoids timing attacks
    return hmac.compare_digest(password.encode(), OWNER_PASSWORD.encode())


def create_token() -> str:
    now = int(time.time())
    payload = {"sub": "owner", "role": "owner", "iat": now, "exp": now + TOKEN_HOURS * 3600}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def require_owner(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    """Dependency: only a valid owner token gets through (fails closed)."""
    if not auth_configured():
        raise HTTPException(status_code=503, detail="Owner login is not configured.")
    if creds is None:
        raise HTTPException(status_code=401, detail="Login required.")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if payload.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Not allowed.")
    return payload
