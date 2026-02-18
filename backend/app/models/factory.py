from datetime import datetime
from typing import Optional

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Factory(Base):
    __tablename__ = "factories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="factory")
    devices: Mapped[list["Device"]] = relationship("Device", back_populates="factory")
    device_parameters: Mapped[list["DeviceParameter"]] = relationship(
        "DeviceParameter", back_populates="factory"
    )
    rules: Mapped[list["Rule"]] = relationship("Rule", back_populates="factory")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="factory")
    analytics_jobs: Mapped[list["AnalyticsJob"]] = relationship(
        "AnalyticsJob", back_populates="factory"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="factory")
