"""Parameter discovery handler for telemetry ingestion."""
from typing import Dict, Union

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

logger = get_logger(__name__)


async def discover_parameters(
    db: AsyncSession,
    factory_id: int,
    device_id: int,
    metrics: Dict[str, Union[float, int]]
) -> Dict[str, bool]:
    """
    Upserts all metric keys into device_parameters.
    
    Returns dict of {parameter_key: is_newly_discovered}
    Must be idempotent — safe to call on every message.
    """
    newly_discovered = {}
    
    for key, value in metrics.items():
        # Determine data type
        data_type = "float" if isinstance(value, float) else "int"
        
        # Build display name from key (e.g., "voltage_l1" -> "Voltage L1")
        display_name = key.replace("_", " ").title()
        
        # INSERT ... ON DUPLICATE KEY UPDATE (idempotent upsert)
        query = text("""
            INSERT INTO device_parameters 
                (factory_id, device_id, parameter_key, display_name, data_type, is_kpi_selected, discovered_at, updated_at)
            VALUES 
                (:factory_id, :device_id, :key, :display_name, :data_type, TRUE, NOW(), NOW())
            ON DUPLICATE KEY UPDATE 
                updated_at = NOW()
        """)
        
        result = await db.execute(query, {
            "factory_id": factory_id,
            "device_id": device_id,
            "key": key,
            "display_name": display_name,
            "data_type": data_type,
        })
        
        # rowcount: 1 = insert, 2 = update (MySQL behavior)
        is_newly_discovered = result.rowcount == 1
        newly_discovered[key] = is_newly_discovered
        
        if is_newly_discovered:
            logger.info(
                "parameter.discovered",
                factory_id=factory_id,
                device_id=device_id,
                parameter=key,
                data_type=data_type,
            )
    
    await db.commit()
    return newly_discovered
