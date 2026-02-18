"""Unit tests for telemetry schema validation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'telemetry'))

import pytest
from datetime import datetime

from schemas import TelemetryPayload, parse_topic


class TestTelemetryPayload:
    """Tests for TelemetryPayload validation."""
    
    def test_valid_payload_parses_correctly(self):
        """Test that valid payload parses correctly."""
        data = {
            "timestamp": "2026-02-18T10:30:00Z",
            "metrics": {
                "voltage": 231.5,
                "current": 3.2,
                "power": 740.8
            }
        }
        
        payload = TelemetryPayload.model_validate(data)
        
        assert payload.timestamp is not None
        assert payload.metrics["voltage"] == 231.5
        assert payload.metrics["current"] == 3.2
        assert payload.metrics["power"] == 740.8
    
    def test_empty_metrics_raises_validation_error(self):
        """Test that empty metrics raises validation error."""
        data = {
            "timestamp": "2026-02-18T10:30:00Z",
            "metrics": {}
        }
        
        with pytest.raises(ValueError, match="metrics cannot be empty"):
            TelemetryPayload.model_validate(data)
    
    def test_non_numeric_metric_raises_validation_error(self):
        """Test that non-numeric metric values raise validation error."""
        data = {
            "metrics": {
                "voltage": "invalid_string"
            }
        }
        
        # Pydantic validates types before custom validator, so we get type validation error
        with pytest.raises(ValueError):
            TelemetryPayload.model_validate(data)
    
    def test_timestamp_defaults_to_none_and_server_provides_fallback(self):
        """Test that missing timestamp defaults to None."""
        data = {
            "metrics": {
                "voltage": 231.5
            }
        }
        
        payload = TelemetryPayload.model_validate(data)
        
        assert payload.timestamp is None
        assert payload.metrics["voltage"] == 231.5
    
    def test_integer_metrics_are_accepted(self):
        """Test that integer metric values are accepted."""
        data = {
            "metrics": {
                "voltage": 231,
                "current": 3
            }
        }
        
        payload = TelemetryPayload.model_validate(data)
        
        assert payload.metrics["voltage"] == 231
        assert payload.metrics["current"] == 3
    
    def test_mixed_numeric_types_accepted(self):
        """Test that mixed int and float metrics are accepted."""
        data = {
            "metrics": {
                "voltage": 231.5,  # float
                "count": 100       # int
            }
        }
        
        payload = TelemetryPayload.model_validate(data)
        
        assert payload.metrics["voltage"] == 231.5
        assert payload.metrics["count"] == 100


class TestParseTopic:
    """Tests for topic parsing."""
    
    def test_parse_topic_valid_input_returns_factory_and_device(self):
        """Test that valid topic is parsed correctly."""
        topic = "factories/vpc/devices/M01/telemetry"
        
        factory_slug, device_key = parse_topic(topic)
        
        assert factory_slug == "vpc"
        assert device_key == "M01"
    
    def test_parse_topic_invalid_format_raises_value_error(self):
        """Test that invalid topic format raises ValueError."""
        topic = "invalid/topic/format"
        
        with pytest.raises(ValueError, match="Invalid topic format"):
            parse_topic(topic)
    
    def test_parse_topic_too_few_segments_raises(self):
        """Test that topic with too few segments raises ValueError."""
        topic = "factories/vpc/devices"
        
        with pytest.raises(ValueError, match="expected 5 segments, got 3"):
            parse_topic(topic)
    
    def test_parse_topic_too_many_segments_raises(self):
        """Test that topic with too many segments raises ValueError."""
        topic = "factories/vpc/devices/M01/extra/telemetry"
        
        with pytest.raises(ValueError, match="expected 5 segments, got 6"):
            parse_topic(topic)
    
    def test_parse_topic_wrong_prefix_raises(self):
        """Test that topic with wrong prefix raises ValueError."""
        topic = "factory/vpc/devices/M01/telemetry"
        
        with pytest.raises(ValueError, match="expected 'factories' prefix"):
            parse_topic(topic)
    
    def test_parse_topic_missing_devices_segment_raises(self):
        """Test that topic without 'devices' segment raises ValueError."""
        topic = "factories/vpc/device/M01/telemetry"
        
        with pytest.raises(ValueError, match="expected 'devices' segment"):
            parse_topic(topic)
    
    def test_parse_topic_wrong_suffix_raises(self):
        """Test that topic with wrong suffix raises ValueError."""
        topic = "factories/vpc/devices/M01/data"
        
        with pytest.raises(ValueError, match="expected 'telemetry' suffix"):
            parse_topic(topic)
    
    def test_parse_topic_different_factory_and_device_values(self):
        """Test parsing with different factory and device values."""
        topic = "factories/chennai-plant/devices/PUMP-05/telemetry"
        
        factory_slug, device_key = parse_topic(topic)
        
        assert factory_slug == "chennai-plant"
        assert device_key == "PUMP-05"
