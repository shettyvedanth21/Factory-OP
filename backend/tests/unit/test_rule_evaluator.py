"""Unit tests for rule condition evaluator."""
import pytest
from datetime import datetime

from app.workers.rule_engine import (
    evaluate_conditions,
    is_rule_scheduled,
    build_alert_message,
    OPERATORS,
)


class TestConditionEvaluator:
    """Tests for evaluate_conditions function."""
    
    # Single condition tests
    def test_single_gt_condition_true(self):
        """Test 'greater than' condition that evaluates to true."""
        metrics = {"voltage": 231.5}
        condition = {"parameter": "voltage", "operator": "gt", "value": 200}
        tree = {"operator": "AND", "conditions": [condition]}
        assert evaluate_conditions(tree, metrics) is True
    
    def test_single_gt_condition_false(self):
        """Test 'greater than' condition that evaluates to false."""
        metrics = {"voltage": 180}
        condition = {"parameter": "voltage", "operator": "gt", "value": 200}
        tree = {"operator": "AND", "conditions": [condition]}
        assert evaluate_conditions(tree, metrics) is False
    
    def test_single_lt_condition_true(self):
        """Test 'less than' condition that evaluates to true."""
        metrics = {"current": 2.5}
        condition = {"parameter": "current", "operator": "lt", "value": 5}
        tree = {"operator": "AND", "conditions": [condition]}
        assert evaluate_conditions(tree, metrics) is True
    
    def test_single_lt_condition_false(self):
        """Test 'less than' condition that evaluates to false."""
        metrics = {"current": 10}
        condition = {"parameter": "current", "operator": "lt", "value": 5}
        tree = {"operator": "AND", "conditions": [condition]}
        assert evaluate_conditions(tree, metrics) is False
    
    def test_single_eq_condition_true(self):
        """Test 'equal' condition that evaluates to true."""
        metrics = {"status": 1}
        condition = {"parameter": "status", "operator": "eq", "value": 1}
        tree = {"operator": "AND", "conditions": [condition]}
        assert evaluate_conditions(tree, metrics) is True
    
    def test_single_neq_condition_true(self):
        """Test 'not equal' condition that evaluates to true."""
        metrics = {"mode": 0}
        condition = {"parameter": "mode", "operator": "neq", "value": 1}
        tree = {"operator": "AND", "conditions": [condition]}
        assert evaluate_conditions(tree, metrics) is True
    
    # Logical operator tests
    def test_and_both_true_returns_true(self):
        """Test AND with both conditions true."""
        metrics = {"voltage": 240, "current": 5}
        conditions = [
            {"parameter": "voltage", "operator": "gt", "value": 200},
            {"parameter": "current", "operator": "gt", "value": 3},
        ]
        tree = {"operator": "AND", "conditions": conditions}
        assert evaluate_conditions(tree, metrics) is True
    
    def test_and_one_false_returns_false(self):
        """Test AND with one false condition."""
        metrics = {"voltage": 240, "current": 2}
        conditions = [
            {"parameter": "voltage", "operator": "gt", "value": 200},
            {"parameter": "current", "operator": "gt", "value": 3},
        ]
        tree = {"operator": "AND", "conditions": conditions}
        assert evaluate_conditions(tree, metrics) is False
    
    def test_or_one_true_returns_true(self):
        """Test OR with one true condition."""
        metrics = {"voltage": 180, "current": 5}
        conditions = [
            {"parameter": "voltage", "operator": "gt", "value": 200},
            {"parameter": "current", "operator": "gt", "value": 3},
        ]
        tree = {"operator": "OR", "conditions": conditions}
        assert evaluate_conditions(tree, metrics) is True
    
    def test_or_both_false_returns_false(self):
        """Test OR with both conditions false."""
        metrics = {"voltage": 180, "current": 2}
        conditions = [
            {"parameter": "voltage", "operator": "gt", "value": 200},
            {"parameter": "current", "operator": "gt", "value": 3},
        ]
        tree = {"operator": "OR", "conditions": conditions}
        assert evaluate_conditions(tree, metrics) is False
    
    # Complex tests
    def test_nested_and_or_complex_tree(self):
        """Test nested AND/OR condition tree."""
        metrics = {"voltage": 240, "current": 4, "frequency": 50}
        # (voltage > 200 AND current > 3) OR frequency > 55
        tree = {
            "operator": "OR",
            "conditions": [
                {
                    "operator": "AND",
                    "conditions": [
                        {"parameter": "voltage", "operator": "gt", "value": 200},
                        {"parameter": "current", "operator": "gt", "value": 3},
                    ]
                },
                {"parameter": "frequency", "operator": "gt", "value": 55},
            ]
        }
        assert evaluate_conditions(tree, metrics) is True
    
    # Error handling tests
    def test_missing_parameter_returns_false_not_exception(self):
        """Test that missing parameter returns False, not exception."""
        metrics = {"current": 5}
        condition = {"parameter": "voltage", "operator": "gt", "value": 200}
        tree = {"operator": "AND", "conditions": [condition]}
        result = evaluate_conditions(tree, metrics)
        assert result is False
    
    def test_unknown_operator_returns_false_not_exception(self):
        """Test that unknown operator returns False, not exception."""
        metrics = {"voltage": 231}
        condition = {"parameter": "voltage", "operator": "unknown", "value": 200}
        tree = {"operator": "AND", "conditions": [condition]}
        result = evaluate_conditions(tree, metrics)
        assert result is False
    
    def test_empty_conditions_list_returns_false(self):
        """Test that empty conditions list returns False."""
        metrics = {"voltage": 231}
        tree = {"operator": "AND", "conditions": []}
        result = evaluate_conditions(tree, metrics)
        assert result is False
    
    def test_invalid_condition_tree_dict_returns_false(self):
        """Test that invalid condition tree returns False gracefully."""
        metrics = {"voltage": 231}
        tree = {"operator": "AND"}  # Missing conditions
        result = evaluate_conditions(tree, metrics)
        assert result is False
    
    def test_deeply_nested_three_levels(self):
        """Test deeply nested three-level condition tree."""
        metrics = {
            "voltage_l1": 230,
            "voltage_l2": 235,
            "voltage_l3": 228,
        }
        # (L1 > 225 OR L2 > 225) AND L3 > 220
        tree = {
            "operator": "AND",
            "conditions": [
                {
                    "operator": "OR",
                    "conditions": [
                        {"parameter": "voltage_l1", "operator": "gt", "value": 225},
                        {"parameter": "voltage_l2", "operator": "gt", "value": 225},
                    ]
                },
                {"parameter": "voltage_l3", "operator": "gt", "value": 220},
            ]
        }
        assert evaluate_conditions(tree, metrics) is True


class TestScheduleValidator:
    """Tests for is_rule_scheduled function."""
    
    def test_always_schedule_returns_true(self):
        """Test 'always' schedule always returns True."""
        rule = {"schedule_type": "always"}
        now = datetime.now()
        assert is_rule_scheduled(rule, now) is True
    
    def test_time_window_within_hours_returns_true(self):
        """Test time window within range returns True."""
        rule = {
            "schedule_type": "time_window",
            "schedule_config": {
                "start_time": "09:00",
                "end_time": "17:00",
                "days": [1, 2, 3, 4, 5],  # Mon-Fri
            }
        }
        now = datetime(2024, 1, 15, 12, 0, 0)  # Monday 12:00
        assert is_rule_scheduled(rule, now) is True
    
    def test_time_window_outside_hours_returns_false(self):
        """Test time window outside range returns False."""
        rule = {
            "schedule_type": "time_window",
            "schedule_config": {
                "start_time": "09:00",
                "end_time": "17:00",
                "days": [1, 2, 3, 4, 5],
            }
        }
        now = datetime(2024, 1, 15, 20, 0, 0)  # Monday 20:00
        assert is_rule_scheduled(rule, now) is False
    
    def test_time_window_wrong_day_returns_false(self):
        """Test time window on wrong day returns False."""
        rule = {
            "schedule_type": "time_window",
            "schedule_config": {
                "start_time": "09:00",
                "end_time": "17:00",
                "days": [1, 2, 3, 4, 5],  # Mon-Fri only
            }
        }
        now = datetime(2024, 1, 14, 12, 0, 0)  # Sunday 12:00
        assert is_rule_scheduled(rule, now) is False
    
    def test_date_range_within_range_returns_true(self):
        """Test date range within range returns True."""
        rule = {
            "schedule_type": "date_range",
            "schedule_config": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        }
        now = datetime(2024, 1, 15)
        assert is_rule_scheduled(rule, now) is True
    
    def test_date_range_outside_range_returns_false(self):
        """Test date range outside range returns False."""
        rule = {
            "schedule_type": "date_range",
            "schedule_config": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        }
        now = datetime(2024, 2, 15)
        assert is_rule_scheduled(rule, now) is False


class TestAlertMessageBuilder:
    """Tests for build_alert_message function."""
    
    def test_build_simple_message(self):
        """Test building simple alert message."""
        rule_name = "Voltage Alert"
        conditions = {
            "operator": "AND",
            "conditions": [
                {"parameter": "voltage", "operator": "gt", "value": 240},
            ]
        }
        metrics = {"voltage": 245.2}
        
        message = build_alert_message(rule_name, conditions, metrics)
        
        assert "Voltage Alert" in message
        assert "voltage (245.2) gt 240" in message
    
    def test_build_multiple_conditions(self):
        """Test building message with multiple conditions."""
        rule_name = "Overvoltage + Overcurrent"
        conditions = {
            "operator": "AND",
            "conditions": [
                {"parameter": "voltage", "operator": "gt", "value": 240},
                {"parameter": "current", "operator": "gt", "value": 10},
            ]
        }
        metrics = {"voltage": 245.2, "current": 12.5}
        
        message = build_alert_message(rule_name, conditions, metrics)
        
        assert "Overvoltage + Overcurrent" in message
        assert "voltage (245.2) gt 240" in message
        assert "current (12.5) gt 10" in message
    
    def test_build_nested_conditions(self):
        """Test building message with nested conditions."""
        rule_name = "Complex Rule"
        conditions = {
            "operator": "OR",
            "conditions": [
                {
                    "operator": "AND",
                    "conditions": [
                        {"parameter": "voltage", "operator": "gt", "value": 240},
                        {"parameter": "current", "operator": "gt", "value": 10},
                    ]
                },
                {"parameter": "frequency", "operator": "lt", "value": 48},
            ]
        }
        metrics = {"voltage": 245.2, "current": 12.5, "frequency": 49}
        
        message = build_alert_message(rule_name, conditions, metrics)
        
        assert "Complex Rule" in message
        assert "voltage (245.2) gt 240" in message
        assert "current (12.5) gt 10" in message
        assert "frequency (49) lt 48" in message
