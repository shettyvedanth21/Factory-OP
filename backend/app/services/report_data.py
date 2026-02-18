"""Report data aggregator service."""
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.influx import get_influx_client
from app.core.logging import get_logger
from app.repositories import device_repo, alert_repo
from app.services.telemetry_fetcher import fetch_as_dataframe

logger = get_logger(__name__)


async def get_report_data(
    db: AsyncSession,
    factory_id: int,
    device_ids: List[int],
    start: datetime,
    end: datetime,
) -> Dict[str, Any]:
    """Aggregate all data needed for a report.
    
    Args:
        db: Database session
        factory_id: Factory ID
        device_ids: List of device IDs to include
        start: Report start date
        end: Report end date
        
    Returns:
        Dict with devices, telemetry summary, alerts, and alert summary
    """
    logger.info(
        "report_data.aggregating",
        factory_id=factory_id,
        device_count=len(device_ids),
        start=start.isoformat(),
        end=end.isoformat(),
    )
    
    # Fetch device metadata
    devices = []
    for device_id in device_ids:
        device = await device_repo.get_by_id(db, factory_id, device_id)
        if device:
            devices.append({
                "id": device.id,
                "device_key": device.device_key,
                "name": device.name,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "region": device.region,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            })
    
    # Fetch telemetry data and calculate summary statistics
    telemetry_summary = {}
    try:
        df = await fetch_as_dataframe(factory_id, device_ids, start, end)
        
        if not df.empty:
            # Group by device and calculate stats per parameter
            for device_id in device_ids:
                device_df = df[df["device_id"] == device_id]
                if device_df.empty:
                    continue
                
                device_stats = {}
                # Get numeric columns (exclude timestamp and device_id)
                numeric_cols = device_df.select_dtypes(include=["number"]).columns.tolist()
                parameter_cols = [c for c in numeric_cols if c not in ["device_id"]]
                
                for param in parameter_cols:
                    values = device_df[param].dropna()
                    if len(values) > 0:
                        device_stats[param] = {
                            "min": round(float(values.min()), 2),
                            "max": round(float(values.max()), 2),
                            "avg": round(float(values.mean()), 2),
                            "count": int(len(values)),
                        }
                
                telemetry_summary[f"device_{device_id}"] = device_stats
    except Exception as e:
        logger.error("report_data.telemetry_error", error=str(e))
        telemetry_summary = {}
    
    # Fetch alerts in date range
    alerts = []
    alert_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    try:
        alerts_list, _ = await alert_repo.get_all(
            db=db,
            factory_id=factory_id,
            start=start,
            end=end,
            per_page=1000,  # Get all alerts in range
        )
        
        for alert in alerts_list:
            if alert.device_id in device_ids:
                alert_data = {
                    "id": alert.id,
                    "rule_id": alert.rule_id,
                    "device_id": alert.device_id,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "severity": alert.severity,
                    "message": alert.message,
                }
                alerts.append(alert_data)
                
                # Update summary counts
                severity = alert.severity.lower()
                if severity in alert_summary:
                    alert_summary[severity] += 1
    except Exception as e:
        logger.error("report_data.alerts_error", error=str(e))
    
    total_alerts = sum(alert_summary.values())
    
    result = {
        "devices": devices,
        "telemetry_summary": telemetry_summary,
        "alerts": alerts,
        "alert_summary": {
            **alert_summary,
            "total": total_alerts,
        },
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "date_range_start": start.isoformat(),
            "date_range_end": end.isoformat(),
            "factory_id": factory_id,
            "device_count": len(devices),
        },
    }
    
    logger.info(
        "report_data.complete",
        factory_id=factory_id,
        device_count=len(devices),
        alert_count=total_alerts,
    )
    
    return result
