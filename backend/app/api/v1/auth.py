"""Authentication router."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.dependencies import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.core.logging import get_logger
from app.models.factory import Factory
from app.repositories import user_repo, factory_repo

router = APIRouter(tags=["auth"])
logger = get_logger(__name__)


class LoginRequest(BaseModel):
    factory_id: int
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class FactoryResponse(BaseModel):
    id: int
    name: str
    slug: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.get("/factories", response_model=List[FactoryResponse])
async def list_factories(db: AsyncSession = Depends(get_db)):
    """List all factories (public endpoint)."""
    factories = await factory_repo.get_all(db)
    return [FactoryResponse(id=f.id, name=f.name, slug=f.slug) for f in factories]


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    # Verify factory exists
    factory = await factory_repo.get_by_id(db, request.factory_id)
    if not factory:
        logger.warning(
            "Login failed - factory not found",
            factory_id=request.factory_id,
            email=request.email,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Get user by email and factory
    user = await user_repo.get_by_email(db, request.factory_id, request.email)
    if not user:
        logger.warning(
            "Login failed - user not found",
            factory_id=request.factory_id,
            email=request.email,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        logger.warning(
            "Login failed - invalid password",
            factory_id=request.factory_id,
            email=request.email,
            user_id=user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Create access token
    access_token = create_access_token(
        user_id=user.id,
        factory_id=factory.id,
        factory_slug=factory.slug,
        role=user.role.value,
    )
    
    logger.info(
        "User logged in successfully",
        factory_id=factory.id,
        user_id=user.id,
        email=user.email,
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours
        user={
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "permissions": user.permissions or {},
        },
    )


@router.post("/auth/refresh", response_model=RefreshResponse)
async def refresh_token(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login"))):
    """Refresh access token."""
    payload = decode_access_token(token)
    
    # Create new token with same claims
    new_token = create_access_token(
        user_id=int(payload["sub"]),
        factory_id=payload["factory_id"],
        factory_slug=payload["factory_slug"],
        role=payload["role"],
    )
    
    return RefreshResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=86400,
    )
