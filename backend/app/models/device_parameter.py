import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DataType(str, enum.Enum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"


class DeviceParameter(Base):
    __tablename__ = "device_parameters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"), nullable=False
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"), nullable=False
    )
    parameter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    data_type: Mapped[DataType] = mapped_column(
        SQLEnum(DataType), default=DataType.FLOAT
    )
    is_kpi_selected: Mapped[bool] = mapped_column(default=True)
    discovered_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    factory: Mapped["Factory"] = relationship(
        "Factory", back_populates="device_parameters"
    )
    device: Mapped["Device"] = relationship("Device", back_populates="parameters")

    __table_args__ = (
        Index("uq_device_param", "device_id", "parameter_key", unique=True),
        Index("idx_factory_device", "factory_id", "device_id"),
        Index("idx_device_param", "device_id", "parameter_key"),
    )
