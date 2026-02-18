import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, String, JSON, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"), nullable=False
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(255))
    device_ids: Mapped[List[int]] = mapped_column(JSON, nullable=False)
    date_range_start: Mapped[datetime] = mapped_column(nullable=False)
    date_range_end: Mapped[datetime] = mapped_column(nullable=False)
    format: Mapped[ReportFormat] = mapped_column(String(20), nullable=False)
    include_analytics: Mapped[bool] = mapped_column(default=False)
    analytics_job_id: Mapped[Optional[str]] = mapped_column(String(36))
    status: Mapped[ReportStatus] = mapped_column(
        String(20), default=ReportStatus.PENDING
    )
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    expires_at: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    factory: Mapped["Factory"] = relationship("Factory", back_populates="reports")
    creator: Mapped["User"] = relationship("User", back_populates="reports")
