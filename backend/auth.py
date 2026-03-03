import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# =========================
# CONFIG
# =========================

SECRET_KEY = os.getenv("NOVA_SECRET_KEY", "dev-secret-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

ADMIN_USERNAME = os.getenv("NOVA_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("NOVA_ADMIN_PASS", "admin123")


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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role != "admin":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return {"username": username, "role": role}
