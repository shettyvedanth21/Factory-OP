import enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    ForeignKey, Index, String, Boolean, JSON, Integer, Enum as SQLEnum, Table, Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RuleScope(str, enum.Enum):
    DEVICE = "device"
    GLOBAL = "global"


class ScheduleType(str, enum.Enum):
    ALWAYS = "always"
    TIME_WINDOW = "time_window"
    DATE_RANGE = "date_range"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Association table for Rule <-> Device many-to-many
rule_devices = Table(
    "rule_devices",
    Base.metadata,
    Column("rule_id", ForeignKey("rules.id", ondelete="CASCADE"), primary_key=True),
    Column("device_id", ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True),
)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    scope: Mapped[RuleScope] = mapped_column(
        SQLEnum(RuleScope), nullable=False, default=RuleScope.DEVICE
    )
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_active: Mapped[bool] = mapped_column(default=True)
    schedule_type: Mapped[ScheduleType] = mapped_column(
        SQLEnum(ScheduleType), default=ScheduleType.ALWAYS
    )
    schedule_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    severity: Mapped[Severity] = mapped_column(
        SQLEnum(Severity), default=Severity.MEDIUM
    )
    notification_channels: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    factory: Mapped["Factory"] = relationship("Factory", back_populates="rules")
    creator: Mapped["User"] = relationship("User", back_populates="rules")
    devices: Mapped[List["Device"]] = relationship(
        "Device", secondary=rule_devices, back_populates="rules"
    )
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="rule")
    cooldowns: Mapped[list["RuleCooldown"]] = relationship(
        "RuleCooldown", back_populates="rule"
    )

    __table_args__ = (
        Index("idx_factory_active", "factory_id", "is_active"),
    )
