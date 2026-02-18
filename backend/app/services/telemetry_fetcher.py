"""Telemetry data fetcher service for analytics."""
import json
from datetime import datetime
from typing import List, Optional

import pandas as pd
import numpy as np

from app.core.config import settings
from app.core.influx import get_influx_client
from app.core.logging import get_logger

logger = get_logger(__name__)


async def fetch_as_dataframe(
    factory_id: int,
    device_ids: List[int],
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    """Fetch telemetry data from InfluxDB and return as pivoted DataFrame.
    
    Args:
        factory_id: Factory ID for filtering
        device_ids: List of device IDs to fetch data for
        start: Start datetime
        end: End datetime
        
    Returns:
        DataFrame with columns: timestamp, device_id, <parameter columns...>
        Each parameter becomes its own column (wide format)
    """
    if not device_ids:
        logger.warning("telemetry_fetch.no_devices", factory_id=factory_id)
        return pd.DataFrame()
    
    # Build Flux query
    device_id_strs = [str(did) for did in device_ids]
    flux = f'''
    from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
        |> filter(fn: (r) => r._measurement == "device_metrics")
        |> filter(fn: (r) => r.factory_id == "{factory_id}")
        |> filter(fn: (r) => contains(value: r.device_id, set: {json.dumps(device_id_strs)}))
    '''
    
    try:
        client = get_influx_client()
        records = await client.query(flux)
        
        if not records:
            logger.info(
                "telemetry_fetch.no_data",
                factory_id=factory_id,
                device_ids=device_ids,
                start=start.isoformat(),
                end=end.isoformat(),
            )
            return pd.DataFrame()
        
        # Extract records into list of dicts
        rows = []
        for table in records:
            for record in table.records:
                rows.append({
                    "timestamp": record.get_time(),
                    "device_id": record.values.get("device_id"),
                    "parameter": record.values.get("parameter"),
                    "value": record.get_value(),
                })
        
        if not rows:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Convert device_id to int for consistency
        df["device_id"] = df["device_id"].astype(int)
        
        # Pivot to wide format: timestamp + device_id as index, parameters as columns
        df_pivot = df.pivot_table(
            index=["timestamp", "device_id"],
            columns="parameter",
            values="value",
            aggfunc="mean",  # In case of duplicates, take mean
        ).reset_index()
        
        # Flatten column names
        df_pivot.columns.name = None
        
        logger.info(
            "telemetry_fetch.success",
            factory_id=factory_id,
            device_count=len(device_ids),
            row_count=len(df_pivot),
            parameter_count=len(df_pivot.columns) - 2,  # exclude timestamp and device_id
        )
        
        return df_pivot
        
    except Exception as e:
        logger.error(
            "telemetry_fetch.error",
            factory_id=factory_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
