"""FastAPI dependencies for auth and database."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as get_db_session
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories import user_repo


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db():
    """Database session dependency."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate current user from JWT token."""
    payload = decode_access_token(token)
    
    user_id = int(payload.get("sub"))
    factory_id = payload.get("factory_id")
    
    user = await user_repo.get_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Attach factory_id from token for downstream use
    user._token_factory_id = factory_id
    
    return user


def require_super_admin(user: User = Depends(get_current_user)) -> User:
    """Require super_admin role."""
    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required",
        )
    return user


def require_permission(permission_key: str):
    """Factory for permission-checking dependency."""
    def checker(user: User = Depends(get_current_user)) -> User:
        # Super admins bypass permission checks
        if user.role == UserRole.SUPER_ADMIN:
            return user
        
        # Check specific permission
        if not user.permissions or not user.permissions.get(permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_key}' required",
            )
        return user
    return checker
