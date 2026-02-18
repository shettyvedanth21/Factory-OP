"""InfluxDB writer for telemetry data."""
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from datetime import datetime
from typing import List, Dict, Union

from influxdb_client import Point
from influxdb_client.client.write_api import WriteApi
from structlog import get_logger

from app.core.config import settings

logger = get_logger(__name__)


def build_points(
    factory_id: int,
    device_id: int,
    metrics: Dict[str, Union[float, int]],
    timestamp: datetime
) -> List[Point]:
    """
    Build InfluxDB Point objects from metrics.
    
    Args:
        factory_id: Factory ID for tag
        device_id: Device ID for tag
        metrics: Dict of parameter_key -> numeric value
        timestamp: Datetime for the point
    
    Returns:
        List of InfluxDB Point objects
    """
    points = []
    
    for param_key, value in metrics.items():
        try:
            point = (
                Point("device_metrics")
                .tag("factory_id", str(factory_id))
                .tag("device_id", str(device_id))
                .tag("parameter", param_key)
                .field("value", float(value))
                .time(timestamp)
            )
            points.append(point)
        except Exception as e:
            logger.warning(
                "point.build_failed",
                factory_id=factory_id,
                device_id=device_id,
                parameter=param_key,
                error=str(e),
            )
    
    return points


async def write_batch(write_api: WriteApi, points: List[Point]) -> None:
    """
    Write batch of points to InfluxDB.
    
    Errors are logged but NOT raised — telemetry loss is acceptable,
    service crash is not.
    """
    if not points:
        return
    
    try:
        write_api.write(
            bucket=settings.influxdb_bucket,
            org=settings.influxdb_org,
            record=points,
        )
        logger.debug(
            "influx.write_success",
            point_count=len(points),
        )
    except Exception as e:
        logger.error(
            "influx.write_failed",
            point_count=len(points),
            error=str(e),
            error_type=type(e).__name__,
        )
        # Do NOT raise — continue processing other messages
