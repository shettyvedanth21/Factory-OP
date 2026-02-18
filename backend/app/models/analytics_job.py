import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, Index, String, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class JobType(str, enum.Enum):
    ANOMALY = "anomaly"
    FAILURE_PREDICTION = "failure_prediction"
    ENERGY_FORECAST = "energy_forecast"
    AI_COPILOT = "ai_copilot"


class JobMode(str, enum.Enum):
    STANDARD = "standard"
    AI_COPILOT = "ai_copilot"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalyticsJob(Base):
    __tablename__ = "analytics_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"), nullable=False
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    job_type: Mapped[JobType] = mapped_column(String(50), nullable=False)
    mode: Mapped[JobMode] = mapped_column(String(20), default=JobMode.STANDARD)
    device_ids: Mapped[List[int]] = mapped_column(JSON, nullable=False)
    date_range_start: Mapped[datetime] = mapped_column(nullable=False)
    date_range_end: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        String(20), default=JobStatus.PENDING
    )
    result_url: Mapped[Optional[str]] = mapped_column(String(500))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column()
    completed_at: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    factory: Mapped["Factory"] = relationship(
        "Factory", back_populates="analytics_jobs"
    )
    creator: Mapped["User"] = relationship(
        "User", back_populates="analytics_jobs"
    )

    __table_args__ = (
        Index("idx_factory_status", "factory_id", "status"),
    )
