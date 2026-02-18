"""Telemetry payload schemas and topic parsing."""
from datetime import datetime
from typing import Dict, Optional, Union

from pydantic import BaseModel, model_validator


class TelemetryPayload(BaseModel):
    """Schema for telemetry payload from MQTT."""
    timestamp: Optional[datetime] = None
    metrics: Dict[str, Union[float, int]]

    @model_validator(mode='after')
    def validate_metrics(self):
        """Validate that metrics is not empty and all values are numeric."""
        if not self.metrics:
            raise ValueError("metrics cannot be empty")
        
        for key, value in self.metrics.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"metric '{key}' must be numeric, got {type(value).__name__}")
        
        return self


def parse_topic(topic: str) -> tuple[str, str]:
    """
    Parse MQTT topic to extract factory slug and device key.
    
    Input:  "factories/vpc/devices/M01/telemetry"
    Output: ("vpc", "M01")
    
    Raises:
        ValueError: If topic format is invalid
    """
    parts = topic.split("/")
    
    if len(parts) != 5:
        raise ValueError(f"Invalid topic format: expected 5 segments, got {len(parts)}: {topic}")
    
    if parts[0] != "factories":
        raise ValueError(f"Invalid topic format: expected 'factories' prefix, got '{parts[0]}': {topic}")
    
    if parts[2] != "devices":
        raise ValueError(f"Invalid topic format: expected 'devices' segment, got '{parts[2]}': {topic}")
    
    if parts[4] != "telemetry":
        raise ValueError(f"Invalid topic format: expected 'telemetry' suffix, got '{parts[4]}': {topic}")
    
    return parts[1], parts[3]
