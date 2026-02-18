import enum
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import ForeignKey, Index, String, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(50))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, default=UserRole.ADMIN
    )
    permissions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)
    invite_token: Mapped[Optional[str]] = mapped_column(String(255))
    invited_at: Mapped[Optional[datetime]] = mapped_column()
    last_login: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    factory: Mapped["Factory"] = relationship("Factory", back_populates="users")
    rules: Mapped[list["Rule"]] = relationship("Rule", back_populates="creator")
    analytics_jobs: Mapped[list["AnalyticsJob"]] = relationship(
        "AnalyticsJob", back_populates="creator"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="creator")

    # Unique constraint on factory_id + email
    __table_args__ = (
        Index("uq_factory_email", "factory_id", "email", unique=True),
    )
