"""KPI service for InfluxDB queries."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.core.config import settings
from app.core.influx import get_influx_client
from app.schemas.kpi import KPIValue, DataPoint
from app.repositories import parameter_repo
from app.core.logging import get_logger

logger = get_logger(__name__)

LIVE_WINDOW_MINUTES = 5
STALE_THRESHOLD_MINUTES = 10


async def get_live_kpis(
    factory_id: int,
    device_id: int,
    selected_params: List[str],
    db,
) -> List[KPIValue]:
    """
    Get live KPI values for selected parameters.
    
    Queries last 5 minutes of data, returns most recent value per parameter.
    Marks values as stale if older than 10 minutes.
    """
    if not selected_params:
        return []
    
    # Build Flux query
    params_filter = " or ".join([f'r.parameter == "{p}"' for p in selected_params])
    
    flux = f'''
    from(bucket: "{settings.influxdb_bucket}")
        |> range(start: -{LIVE_WINDOW_MINUTES}m)
        |> filter(fn: (r) => r._measurement == "device_metrics")
        |> filter(fn: (r) => r.factory_id == "{factory_id}")
        |> filter(fn: (r) => r.device_id == "{device_id}")
        |> filter(fn: (r) => {params_filter})
        |> last()
    '''
    
    try:
        influx = get_influx_client()
        records = await influx.query(flux)
        
        # Get parameter metadata for display names and units
        all_params = await parameter_repo.get_all(db, factory_id, device_id)
        param_meta = {p.parameter_key: p for p in all_params}
        
        kpis = []
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        
        for record in records:
            param_key = record.values.get("parameter")
            if not param_key:
                continue
            
            value = record.values.get("_value")
            record_time = record.values.get("_time")
            
            # Check if stale (older than threshold)
            is_stale = False
            if record_time:
                if isinstance(record_time, str):
                    record_time = datetime.fromisoformat(record_time.replace('Z', '+00:00'))
                is_stale = record_time < stale_threshold
            
            # Get metadata
            meta = param_meta.get(param_key)
            
            kpis.append(KPIValue(
                parameter_key=param_key,
                display_name=meta.display_name if meta else param_key,
                unit=meta.unit if meta else None,
                value=float(value) if value else 0.0,
                is_stale=is_stale,
            ))
        
        await influx.close()
        return kpis
        
    except Exception as e:
        logger.error(
            "kpi.live_query_failed",
            factory_id=factory_id,
            device_id=device_id,
            error=str(e),
        )
        return []


async def get_kpi_history(
    factory_id: int,
    device_id: int,
    parameter: str,
    start: datetime,
    end: datetime,
    interval: Optional[str] = None,
) -> List[DataPoint]:
    """
    Get KPI history data for charting.
    
    Auto-selects interval if not provided:
    - range < 2h → 1m
    - range < 24h → 5m
    - range < 7d → 1h
    - else → 1d
    """
    # Auto-select interval based on time range
    if not interval:
        duration = end - start
        if duration < timedelta(hours=2):
            interval = "1m"
        elif duration < timedelta(hours=24):
            interval = "5m"
        elif duration < timedelta(days=7):
            interval = "1h"
        else:
            interval = "1d"
    
    # Build Flux query
    flux = f'''
    from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
        |> filter(fn: (r) => r._measurement == "device_metrics")
        |> filter(fn: (r) => r.factory_id == "{factory_id}")
        |> filter(fn: (r) => r.device_id == "{device_id}")
        |> filter(fn: (r) => r.parameter == "{parameter}")
        |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
        |> yield(name: "mean")
    '''
    
    try:
        influx = get_influx_client()
        records = await influx.query(flux)
        
        points = []
        for record in records:
            timestamp = record.values.get("_time")
            value = record.values.get("_value")
            
            if timestamp and value is not None:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                points.append(DataPoint(
                    timestamp=timestamp,
                    value=float(value),
                ))
        
        await influx.close()
        return points
        
    except Exception as e:
        logger.error(
            "kpi.history_query_failed",
            factory_id=factory_id,
            device_id=device_id,
            parameter=parameter,
            error=str(e),
        )
        return []
