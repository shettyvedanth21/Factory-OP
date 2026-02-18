"""Factory repository for database operations."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factory import Factory


async def get_by_id(db: AsyncSession, factory_id: int) -> Optional[Factory]:
    """Get factory by ID."""
    result = await db.execute(select(Factory).where(Factory.id == factory_id))
    return result.scalar_one_or_none()


async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Factory]:
    """Get factory by slug."""
    result = await db.execute(select(Factory).where(Factory.slug == slug))
    return result.scalar_one_or_none()


async def get_all(db: AsyncSession) -> List[Factory]:
    """Get all factories."""
    result = await db.execute(select(Factory))
    return result.scalars().all()
