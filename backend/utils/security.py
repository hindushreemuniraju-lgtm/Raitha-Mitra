"""Password hashing, JWT issuance/verification, and per-farmer FastAPI dependencies."""

from datetime import datetime, timedelta, timezone
import re
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models.farmer import Farmer


bearer_scheme = HTTPBearer(auto_error=False)


def normalize_mobile(mobile: str) -> str:
    """Normalize Indian mobile input to 10 digits where applicable."""
    digits = re.sub(r"\D", "", mobile or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def hash_password(password: str) -> str:
    """Hash password securely using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    if not plain_password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(farmer_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create signed HS256 JWT access token scoped to farmer_id."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(farmer_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "raitha-mitra",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> int:
    """Validate JWT and extract integer farmer_id."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            issuer="raitha-mitra",
        )
        sub = payload.get("sub")
        if sub is None:
            raise ValueError("Missing subject")
        return int(sub)
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_farmer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Farmer:
    """FastAPI dependency returning the authenticated Farmer ORM instance."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    farmer_id = decode_access_token(credentials.credentials)
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if farmer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Farmer account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return farmer
