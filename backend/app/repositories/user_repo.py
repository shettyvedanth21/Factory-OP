"""User repository for database operations."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_by_id(db: AsyncSession, factory_id: int, user_id: int) -> Optional[User]:
    """Get user by ID within a factory."""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.factory_id == factory_id,
        )
    )
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, factory_id: int, email: str) -> Optional[User]:
    """Get user by email within a factory."""
    result = await db.execute(
        select(User).where(
            User.factory_id == factory_id,
            User.email == email,
        )
    )
    return result.scalar_one_or_none()


async def get_all(db: AsyncSession, factory_id: int) -> List[User]:
    """Get all users within a factory."""
    result = await db.execute(
        select(User).where(User.factory_id == factory_id)
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    factory_id: int,
    email: str,
    hashed_password: str,
    role: UserRole = UserRole.ADMIN,
    permissions: Optional[Dict[str, Any]] = None,
    whatsapp_number: Optional[str] = None,
    invite_token: Optional[str] = None,
) -> User:
    """Create a new user."""
    user = User(
        factory_id=factory_id,
        email=email,
        hashed_password=hashed_password,
        role=role,
        permissions=permissions,
        whatsapp_number=whatsapp_number,
        invite_token=invite_token,
        invited_at=datetime.utcnow() if invite_token else None,
        is_active=invite_token is None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_permissions(
    db: AsyncSession,
    factory_id: int,
    user_id: int,
    permissions: Dict[str, Any],
) -> Optional[User]:
    """Update user permissions."""
    result = await db.execute(
        update(User)
        .where(
            User.id == user_id,
            User.factory_id == factory_id,
            User.role != UserRole.SUPER_ADMIN,
        )
        .values(permissions=permissions)
        .returning(User)
    )
    await db.commit()
    return result.scalar_one_or_none()


async def deactivate(
    db: AsyncSession,
    factory_id: int,
    user_id: int,
) -> Optional[User]:
    """Deactivate a user (soft delete)."""
    result = await db.execute(
        update(User)
        .where(
            User.id == user_id,
            User.factory_id == factory_id,
            User.role != UserRole.SUPER_ADMIN,
        )
        .values(is_active=False)
        .returning(User)
    )
    await db.commit()
    return result.scalar_one_or_none()


async def get_by_invite_token(db: AsyncSession, token: str) -> Optional[User]:
    """Get user by invite token."""
    result = await db.execute(
        select(User).where(
            User.invite_token == token,
            User.is_active == False,
        )
    )
    return result.scalar_one_or_none()


async def set_password_and_activate(
    db: AsyncSession,
    user_id: int,
    hashed_password: str,
) -> Optional[User]:
    """Set password and activate user after invite acceptance."""
    result = await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            hashed_password=hashed_password,
            is_active=True,
            invite_token=None,
            invited_at=None,
        )
        .returning(User)
    )
    await db.commit()
    return result.scalar_one_or_none()


async def update_last_login(db: AsyncSession, user_id: int) -> None:
    """Update user's last login timestamp."""
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_login=datetime.utcnow())
    )
    await db.commit()
