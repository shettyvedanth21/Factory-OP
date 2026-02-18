"""Users API router."""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.logging import get_logger
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.repositories import user_repo

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


class InviteRequest(BaseModel):
    email: EmailStr
    whatsapp_number: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None


class InviteResponse(BaseModel):
    id: int
    email: str
    invite_sent: bool


class AcceptInviteRequest(BaseModel):
    token: str
    password: str


class PermissionsUpdate(BaseModel):
    permissions: Dict[str, bool]


class UserResponse(BaseModel):
    id: int
    email: str
    whatsapp_number: Optional[str] = None
    role: str
    permissions: Optional[Dict[str, Any]] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime


def check_super_admin(current_user: User) -> User:
    """Ensure current user is a super_admin."""
    if current_user.role != UserRole.SUPER_ADMIN:
        logger.warning(
            "Unauthorized access attempt to super_admin endpoint",
            user_id=current_user.id,
            role=current_user.role.value,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users in the factory. Requires super_admin."""
    check_super_admin(current_user)
    
    users = await user_repo.get_all(db, current_user.factory_id)
    
    logger.info(
        "Users listed",
        factory_id=current_user.factory_id,
        user_id=current_user.id,
        count=len(users),
    )
    
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            whatsapp_number=u.whatsapp_number,
            role=u.role.value,
            permissions=u.permissions,
            is_active=u.is_active,
            last_login=u.last_login,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("/invite", response_model=InviteResponse)
async def invite_user(
    request: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a new user to the factory. Requires super_admin."""
    check_super_admin(current_user)
    
    existing = await user_repo.get_by_email(db, current_user.factory_id, request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists in this factory",
        )
    
    invite_token = secrets.token_urlsafe(32)
    hashed_password = get_password_hash(secrets.token_urlsafe(32))
    
    user = await user_repo.create(
        db=db,
        factory_id=current_user.factory_id,
        email=request.email,
        hashed_password=hashed_password,
        role=UserRole.ADMIN,
        permissions=request.permissions,
        whatsapp_number=request.whatsapp_number,
        invite_token=invite_token,
    )
    
    invite_link = f"{settings.app_url}/accept-invite?token={invite_token}"
    
    if settings.smtp_host:
        logger.info(
            "Invite email would be sent",
            factory_id=current_user.factory_id,
            user_id=current_user.id,
            invite_token=invite_token[:8] + "...",
        )
    else:
        logger.info(
            "Invite link (SMTP not configured)",
            factory_id=current_user.factory_id,
            invite_link=invite_link,
        )
    
    return InviteResponse(
        id=user.id,
        email=user.email,
        invite_sent=bool(settings.SMTP_HOST),
    )


@router.post("/accept-invite")
async def accept_invite(
    request: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept invitation and set password. No auth required."""
    user = await user_repo.get_by_invite_token(db, request.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token",
        )
    
    if user.invited_at and datetime.utcnow() - user.invited_at > timedelta(hours=48):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation token has expired",
        )
    
    hashed_password = get_password_hash(request.password)
    user = await user_repo.set_password_and_activate(db, user.id, hashed_password)
    
    logger.info(
        "User activated via invite",
        factory_id=user.factory_id,
        user_id=user.id,
        email=user.email,
    )
    
    from app.core.security import create_access_token
    from app.models.factory import Factory
    from sqlalchemy import select
    
    result = await db.execute(select(Factory).where(Factory.id == user.factory_id))
    factory = result.scalar_one()
    
    access_token = create_access_token(
        user_id=user.id,
        factory_id=factory.id,
        factory_slug=factory.slug,
        role=user.role.value,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "permissions": user.permissions or {},
        },
    }


@router.patch("/{user_id}/permissions")
async def update_permissions(
    user_id: int,
    request: PermissionsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user permissions. Requires super_admin."""
    check_super_admin(current_user)
    
    target_user = await user_repo.get_by_id(db, current_user.factory_id, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if target_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify super_admin permissions",
        )
    
    updated = await user_repo.update_permissions(
        db, current_user.factory_id, user_id, request.permissions
    )
    
    logger.info(
        "User permissions updated",
        factory_id=current_user.factory_id,
        user_id=current_user.id,
        target_user_id=user_id,
    )
    
    return {
        "id": updated.id,
        "email": updated.email,
        "permissions": updated.permissions,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user. Requires super_admin."""
    check_super_admin(current_user)
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )
    
    target_user = await user_repo.get_by_id(db, current_user.factory_id, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if target_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate super_admin users",
        )
    
    await user_repo.deactivate(db, current_user.factory_id, user_id)
    
    logger.info(
        "User deactivated",
        factory_id=current_user.factory_id,
        user_id=current_user.id,
        target_user_id=user_id,
    )
    
    return None
