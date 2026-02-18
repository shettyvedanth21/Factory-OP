from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, Index, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"), nullable=False
    )
    device_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255))
    model: Mapped[Optional[str]] = mapped_column(String(255))
    region: Mapped[Optional[str]] = mapped_column(String(255))
    api_key: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    factory: Mapped["Factory"] = relationship("Factory", back_populates="devices")
    parameters: Mapped[list["DeviceParameter"]] = relationship(
        "DeviceParameter", back_populates="device"
    )
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="device")
    rules: Mapped[List["Rule"]] = relationship(
        "Rule", secondary="rule_devices", back_populates="devices"
    )

    __table_args__ = (
        Index("uq_factory_device", "factory_id", "device_key", unique=True),
        Index("idx_factory_id", "factory_id"),
    )
