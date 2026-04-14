import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# =========================
# CONFIG
# =========================

SECRET_KEY = os.getenv("NOVA_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "Missing required environment variable: NOVA_SECRET_KEY. "
        "Set it in your environment or .env file (example: NOVA_SECRET_KEY=replace-with-a-secret)."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

ADMIN_USERNAME = os.getenv("NOVA_ADMIN_USER")
ADMIN_PASSWORD = os.getenv("NOVA_ADMIN_PASS")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError(
        "Missing required environment variables: NOVA_ADMIN_USER and/or NOVA_ADMIN_PASS. "
        "Set both values (example: NOVA_ADMIN_USER=admin, NOVA_ADMIN_PASS=change-me)."
    )


# =========================
# AUTHENTICATE
# =========================

def authenticate_user(username: str, password: str):
    if username != ADMIN_USERNAME:
        return False

    if password != ADMIN_PASSWORD:
        return False

    return {"username": username, "role": "admin"}


# =========================
# TOKEN
# =========================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =========================
# DEPENDENCY
# =========================

def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        return verify_admin_token(token)
    except Exception:
        raise credentials_exception


def verify_admin_token(token: str):
    """
    Shared verifier for HTTP and WebSocket authentication.
    Raises on invalid token.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    role: str = payload.get("role")

    if username is None or role != "admin":
        raise RuntimeError("invalid_role")

    return {"username": username, "role": role}
