"""Security utilities for JWT and password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    user_id: int,
    factory_id: int,
    factory_slug: str,
    role: str,
) -> str:
    """Create JWT access token with factory context."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=settings.jwt_expiry_hours)
    
    payload = {
        "sub": str(user_id),
        "factory_id": factory_id,
        "factory_slug": factory_slug,
        "role": role,
        "exp": expires,
        "iat": now,
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def hash_password(plain_password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)
