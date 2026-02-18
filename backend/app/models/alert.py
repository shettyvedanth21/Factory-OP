from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import ForeignKey, Index, String, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"), nullable=False
    )
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("rules.id"), nullable=False
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"), nullable=False
    )
    triggered_at: Mapped[datetime] = mapped_column(nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column()
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    telemetry_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    notification_sent: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    factory: Mapped["Factory"] = relationship("Factory", back_populates="alerts")
    rule: Mapped["Rule"] = relationship("Rule", back_populates="alerts")
    device: Mapped["Device"] = relationship("Device", back_populates="alerts")

    __table_args__ = (
        Index("idx_factory_device_time", "factory_id", "device_id", "triggered_at"),
        Index("idx_factory_time", "factory_id", "triggered_at"),
    )


class RuleCooldown(Base):
    __tablename__ = "rule_cooldowns"

    rule_id: Mapped[int] = mapped_column(
        ForeignKey("rules.id", ondelete="CASCADE"), primary_key=True
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True
    )
    last_triggered: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    rule: Mapped["Rule"] = relationship("Rule", back_populates="cooldowns")
