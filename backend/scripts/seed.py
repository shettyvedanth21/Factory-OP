"""Seed script for initial data."""
import asyncio
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import bcrypt

from app.core.database import AsyncSessionLocal
from app.models.factory import Factory
from app.models.user import User, UserRole
from app.models.device import Device


async def seed_data():
    """Seed initial factory, user, and devices."""
    async with AsyncSessionLocal() as session:
        try:
            # Create VPC Factory
            factory = Factory(
                name="VPC Factory",
                slug="vpc",
                timezone="Asia/Kolkata"
            )
            session.add(factory)
            await session.flush()  # Flush to get the factory.id
            
            print(f"✓ Created Factory: {factory.name} (ID: {factory.id})")
            
            # Create Super Admin user
            hashed_password = bcrypt.hash("Admin@123")
            user = User(
                factory_id=factory.id,
                email="admin@vpc.com",
                hashed_password=hashed_password,
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            session.add(user)
            await session.flush()
            
            print(f"✓ Created User: {user.email} (ID: {user.id})")
            
            # Create Device 1
            device1 = Device(
                factory_id=factory.id,
                device_key="M01",
                name="Compressor 1",
                manufacturer="Siemens",
                region="Zone A",
                is_active=True
            )
            session.add(device1)
            await session.flush()
            
            print(f"✓ Created Device: {device1.name} (ID: {device1.id})")
            
            # Create Device 2
            device2 = Device(
                factory_id=factory.id,
                device_key="M02",
                name="Pump 1",
                manufacturer="ABB",
                region="Zone B",
                is_active=True
            )
            session.add(device2)
            await session.flush()
            
            print(f"✓ Created Device: {device2.name} (ID: {device2.id})")
            
            await session.commit()
            print("\n✅ Seeding completed successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Seeding failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())
