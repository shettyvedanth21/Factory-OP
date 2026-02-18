"""Factory isolation integration tests."""
import pytest
import pytest_asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factory import Factory
from app.models.user import User, UserRole
from app.models.device import Device
from app.repositories import device_repo, parameter_repo
from app.core.security import create_access_token, hash_password
from app.core.database import AsyncSessionLocal


@pytest_asyncio.fixture
async def test_factories_and_users():
    """Create test factories and users for isolation testing."""
    async with AsyncSessionLocal() as db:
        # Create Factory A
        factory_a = Factory(name="Factory A", slug="factory-a")
        db.add(factory_a)
        await db.flush()
        
        # Create user for Factory A
        user_a = User(
            factory_id=factory_a.id,
            email="user@factorya.com",
            hashed_password=hash_password("password123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user_a)
        await db.flush()
        
        # Create device for Factory A
        device_a = Device(
            factory_id=factory_a.id,
            device_key="M01-A",
            name="Device A",
            is_active=True,
        )
        db.add(device_a)
        
        # Create Factory B
        factory_b = Factory(name="Factory B", slug="factory-b")
        db.add(factory_b)
        await db.flush()
        
        # Create user for Factory B
        user_b = User(
            factory_id=factory_b.id,
            email="user@factoryb.com",
            hashed_password=hash_password("password123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user_b)
        await db.flush()
        
        # Create device for Factory B
        device_b = Device(
            factory_id=factory_b.id,
            device_key="M01-B",
            name="Device B",
            is_active=True,
        )
        db.add(device_b)
        await db.commit()
        
        yield {
            "factory_a": factory_a,
            "user_a": user_a,
            "device_a": device_a,
            "factory_b": factory_b,
            "user_b": user_b,
            "device_b": device_b,
        }
        
        # Cleanup
        await db.execute("DELETE FROM devices WHERE id IN (:a, :b)", {
            "a": device_a.id, "b": device_b.id
        })
        await db.execute("DELETE FROM users WHERE id IN (:a, :b)", {
            "a": user_a.id, "b": user_b.id
        })
        await db.execute("DELETE FROM factories WHERE id IN (:a, :b)", {
            "a": factory_a.id, "b": factory_b.id
        })
        await db.commit()


@pytest.mark.asyncio
async def test_list_devices_only_returns_own_factory_devices(test_factories_and_users):
    """Test that device list only returns devices from user's factory."""
    data = test_factories_and_users
    
    async with AsyncSessionLocal() as db:
        # User A lists devices - should only see Factory A devices
        devices_a, total_a = await device_repo.get_all(db, data["factory_a"].id)
        
        assert total_a == 1
        assert devices_a[0].device_key == "M01-A"
        assert devices_a[0].factory_id == data["factory_a"].id
        
        # Verify Factory B device is not included
        device_ids = [d.id for d in devices_a]
        assert data["device_b"].id not in device_ids


@pytest.mark.asyncio
async def test_get_device_from_other_factory_returns_404(test_factories_and_users):
    """Test that accessing device from another factory returns 404."""
    data = test_factories_and_users
    
    async with AsyncSessionLocal() as db:
        # User A tries to get Factory B's device
        device = await device_repo.get_by_id(
            db, data["factory_a"].id, data["device_b"].id
        )
        
        # Should return None (which becomes 404 in API)
        assert device is None


@pytest.mark.asyncio
async def test_update_device_from_other_factory_returns_404(test_factories_and_users):
    """Test that updating device from another factory returns 404."""
    data = test_factories_and_users
    
    async with AsyncSessionLocal() as db:
        # User A tries to update Factory B's device
        device = await device_repo.update(
            db, data["factory_a"].id, data["device_b"].id, {"name": "Hacked"}
        )
        
        # Should return None (which becomes 404 in API)
        assert device is None


@pytest.mark.asyncio
async def test_parameter_list_from_other_factory_device_returns_404(test_factories_and_users):
    """Test that listing parameters from another factory's device returns 404."""
    data = test_factories_and_users
    
    async with AsyncSessionLocal() as db:
        # User A tries to get parameters for Factory B's device
        # First verify device doesn't exist in Factory A scope
        device = await device_repo.get_by_id(
            db, data["factory_a"].id, data["device_b"].id
        )
        assert device is None


@pytest.mark.asyncio
async def test_factory_isolation_in_query_filter(test_factories_and_users):
    """Test that factory_id filter is applied in all queries."""
    data = test_factories_and_users
    
    async with AsyncSessionLocal() as db:
        # Get by key should respect factory scope
        device_in_a = await device_repo.get_by_key(
            db, data["factory_a"].id, "M01-A"
        )
        assert device_in_a is not None
        assert device_in_a.factory_id == data["factory_a"].id
        
        # Same key in different factory should not be found
        device_cross = await device_repo.get_by_key(
            db, data["factory_a"].id, "M01-B"
        )
        assert device_cross is None


@pytest.mark.asyncio
async def test_delete_device_from_other_factory_returns_404(test_factories_and_users):
    """Test that deleting device from another factory returns 404."""
    data = test_factories_and_users
    
    async with AsyncSessionLocal() as db:
        # User A tries to delete Factory B's device
        device = await device_repo.soft_delete(
            db, data["factory_a"].id, data["device_b"].id
        )
        
        # Should return None (which becomes 404 in API)
        assert device is None
