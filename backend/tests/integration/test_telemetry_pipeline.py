"""Integration tests for telemetry pipeline."""
import sys
import os
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_asyncio

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'telemetry'))

from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from telemetry.handlers.ingestion import process_telemetry
from telemetry.handlers.cache import get_or_create_device
from app.core.database import AsyncSessionLocal
from app.models.factory import Factory
from app.models.device import Device
from app.models.device_parameter import DeviceParameter


@pytest_asyncio.fixture
async def db():
    """Database session fixture."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def redis():
    """Redis client fixture."""
    client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    yield client
    await client.close()


class TestTelemetryPipeline:
    """Integration tests for the telemetry pipeline."""
    
    @pytest.mark.asyncio
    async def test_valid_payload_writes_to_influxdb(self, db, redis):
        """Test that valid payload writes correct data to InfluxDB."""
        # Mock InfluxDB write API
        mock_write_api = Mock()
        mock_write_api.write = AsyncMock()
        
        topic = "factories/vpc/devices/M01/telemetry"
        payload = json.dumps({
            "timestamp": "2026-03-01T10:00:00Z",
            "metrics": {
                "voltage": 231.4,
                "current": 3.2,
                "power": 745.6,
            }
        }).encode()
        
        # Process telemetry
        await process_telemetry(topic, payload, db, redis, mock_write_api)
        
        # Assert InfluxDB write was called
        assert mock_write_api.write.called
        
        # Get the points passed to write
        call_args = mock_write_api.write.call_args
        assert call_args is not None
        
        # Verify points were created with correct structure
        points = call_args.kwargs.get('record') or call_args.args[0]
        assert len(points) == 3
    
    @pytest.mark.asyncio
    async def test_malformed_payload_does_not_crash(self, db, redis):
        """Test that malformed payload is handled gracefully without crashing."""
        mock_write_api = Mock()
        mock_write_api.write = AsyncMock()
        
        topic = "factories/vpc/devices/M01/telemetry"
        # Invalid JSON payload
        payload = b"not valid json {"
        
        # Should not raise exception
        await process_telemetry(topic, payload, db, redis, mock_write_api)
        
        # InfluxDB write should NOT have been called
        assert not mock_write_api.write.called
    
    @pytest.mark.asyncio
    async def test_unknown_factory_skips_processing(self, db, redis):
        """Test that unknown factory slug skips processing."""
        mock_write_api = Mock()
        mock_write_api.write = AsyncMock()
        
        topic = "factories/unknown-factory/devices/M01/telemetry"
        payload = json.dumps({
            "metrics": {"voltage": 231.4}
        }).encode()
        
        # Process telemetry
        await process_telemetry(topic, payload, db, redis, mock_write_api)
        
        # InfluxDB write should NOT have been called
        assert not mock_write_api.write.called
    
    @pytest.mark.asyncio
    async def test_new_parameter_key_auto_discovered(self, db, redis):
        """Test that new parameter keys are auto-discovered and inserted."""
        # Clear cache to ensure fresh lookup
        await redis.delete("device:1:M01")
        await redis.delete("factory:slug:vpc")
        
        mock_write_api = Mock()
        mock_write_api.write = AsyncMock()
        
        # Create test factory and device if needed
        from sqlalchemy import select
        
        # Check if VPC factory exists
        result = await db.execute(select(Factory).where(Factory.slug == "vpc"))
        factory = result.scalar_one_or_none()
        
        if not factory:
            factory = Factory(name="VPC Factory", slug="vpc")
            db.add(factory)
            await db.commit()
            await db.refresh(factory)
        
        # Check if M01 device exists
        result = await db.execute(
            select(Device).where(Device.factory_id == factory.id, Device.device_key == "M01")
        )
        device = result.scalar_one_or_none()
        
        if not device:
            device = Device(
                factory_id=factory.id,
                device_key="M01",
                is_active=True,
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)
        
        # Clear any existing parameters
        from sqlalchemy import delete
        await db.execute(
            delete(DeviceParameter).where(DeviceParameter.device_id == device.id)
        )
        await db.commit()
        
        topic = f"factories/vpc/devices/M01/telemetry"
        payload = json.dumps({
            "metrics": {
                "new_parameter_xyz": 123.45,  # New parameter
            }
        }).encode()
        
        # Process telemetry
        await process_telemetry(topic, payload, db, redis, mock_write_api)
        
        # Verify new parameter was discovered
        result = await db.execute(
            select(DeviceParameter).where(
                DeviceParameter.device_id == device.id,
                DeviceParameter.parameter_key == "new_parameter_xyz"
            )
        )
        param = result.scalar_one_or_none()
        
        assert param is not None
        assert param.parameter_key == "new_parameter_xyz"
        assert param.is_kpi_selected is True
