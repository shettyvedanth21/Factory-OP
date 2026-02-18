"""InfluxDB client configuration."""
from typing import List, Any
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.domain.write_precision import WritePrecision
from influxdb_client.client.write.point import Point

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class InfluxDBClient:
    """Async InfluxDB client wrapper."""
    
    def __init__(self):
        self.client: InfluxDBClientAsync = InfluxDBClientAsync(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org,
        )
    
    async def write_points(self, points: List[Point], precision: str = "s") -> None:
        """Write points to InfluxDB."""
        try:
            write_api = self.client.write_api()
            await write_api.write(
                bucket=settings.influxdb_bucket,
                record=points,
                write_precision=getattr(WritePrecision, precision.upper()),
            )
        except Exception as e:
            logger.error("InfluxDB write failed", error=str(e))
            raise
    
    async def query(self, flux: str) -> List[Any]:
        """Execute Flux query."""
        try:
            query_api = self.client.query_api()
            result = await query_api.query(query=flux)
            return result
        except Exception as e:
            logger.error("InfluxDB query failed", error=str(e))
            raise
    
    async def close(self) -> None:
        """Close client connection."""
        await self.client.close()


# Singleton instance
_influx_client: InfluxDBClient = None


def get_influx_client() -> InfluxDBClient:
    """Get or create InfluxDB client instance."""
    global _influx_client
    if _influx_client is None:
        _influx_client = InfluxDBClient()
    return _influx_client


async def check_influx_health() -> bool:
    """Check if InfluxDB is reachable."""
    try:
        client = get_influx_client()
        # Try to query the health endpoint
        health = await client.client.health()
        return health.status == "pass"
    except Exception as e:
        logger.error("InfluxDB health check failed", error=str(e))
        return False
