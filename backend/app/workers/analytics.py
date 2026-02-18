"""Analytics worker with ML models for anomaly detection, forecasting, and failure prediction."""
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from prophet import Prophet

from app.core.logging import get_logger

logger = get_logger(__name__)


def run_anomaly_detection(df: pd.DataFrame) -> Dict[str, Any]:
    """Run Isolation Forest anomaly detection on telemetry data.
    
    Args:
        df: DataFrame with telemetry data (wide format)
        
    Returns:
        Dict with anomaly_count, anomaly_score, anomalies list, and summary
    """
    if df.empty or len(df) < 10:
        logger.warning("anomaly.insufficient_data", rows=len(df))
        return {"error": "Insufficient data for anomaly detection (minimum 10 rows required)"}
    
    # Get numeric columns only (exclude timestamp and device_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c not in ["device_id"]]
    
    if not feature_cols:
        logger.warning("anomaly.no_numeric_features")
        return {"error": "No numeric features available for anomaly detection"}
    
    # Fill NaN values with column medians
    X = df[feature_cols].fillna(df[feature_cols].median())
    
    # Run Isolation Forest
    model = IsolationForest(
        contamination=0.05,  # Expect 5% anomalies
        random_state=42,
        n_estimators=100,
    )
    
    try:
        scores = model.fit_predict(X)
        anomaly_mask = scores == -1  # -1 indicates anomaly
        
        # Build anomalies list
        anomalies = []
        for idx in df[anomaly_mask].index:
            row = df.iloc[idx]
            # Get anomaly score (higher = more anomalous)
            score_samples = model.score_samples(X.iloc[[idx]])
            anomaly_score = float(abs(score_samples[0]))
            
            anomalies.append({
                "device_id": int(row.get("device_id", 0)),
                "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], 'isoformat') else str(row["timestamp"]),
                "score": anomaly_score,
                "affected_parameters": feature_cols,
            })
        
        # Sort by score descending, limit to top 50
        anomalies = sorted(anomalies, key=lambda x: x["score"], reverse=True)[:50]
        
        result = {
            "anomaly_count": int(anomaly_mask.sum()),
            "anomaly_score": float(anomaly_mask.mean()),
            "anomalies": anomalies,
            "summary": f"{int(anomaly_mask.sum())} anomalies detected in {len(df)} data points",
            "parameters_analyzed": feature_cols,
        }
        
        logger.info(
            "anomaly.complete",
            anomaly_count=result["anomaly_count"],
            total_rows=len(df),
        )
        
        return result
        
    except Exception as e:
        logger.error("anomaly.error", error=str(e), error_type=type(e).__name__)
        return {"error": f"Anomaly detection failed: {str(e)}"}


def run_energy_forecast(df: pd.DataFrame, horizon_days: int = 7) -> Dict[str, Any]:
    """Run Prophet energy forecasting on power consumption data.
    
    Args:
        df: DataFrame with telemetry data
        horizon_days: Number of days to forecast ahead (default: 7)
        
    Returns:
        Dict with forecast data and summary
    """
    if "power" not in df.columns:
        logger.warning("forecast.no_power_column", available_columns=list(df.columns))
        return {"error": "No power parameter available for forecasting"}
    
    # Prepare time series data for Prophet
    ts_df = df[["timestamp", "power"]].dropna()
    
    if len(ts_df) < 24:
        logger.warning("forecast.insufficient_data", rows=len(ts_df))
        return {"error": "Insufficient data for forecasting (minimum 24 data points required)"}
    
    # Prophet requires 'ds' (datetime) and 'y' (value) columns
    ts_df = ts_df.copy()
    ts_df.columns = ["ds", "y"]
    
    # Remove timezone info (Prophet doesn't support timezones well)
    ts_df["ds"] = pd.to_datetime(ts_df["ds"]).dt.tz_localize(None)
    
    try:
        # Initialize and fit Prophet model
        model = Prophet(
            daily_seasonality=True,
            yearly_seasonality=False,
            weekly_seasonality=True,
        )
        
        model.fit(ts_df)
        
        # Create future dataframe for forecasting
        future = model.make_future_dataframe(periods=horizon_days * 24, freq="H")
        
        # Generate forecast
        forecast = model.predict(future)
        
        # Extract only future predictions
        future_only = forecast[forecast["ds"] > ts_df["ds"].max()]
        
        # Build forecast results
        forecast_data = []
        for _, row in future_only.iterrows():
            forecast_data.append({
                "timestamp": row["ds"].isoformat(),
                "yhat": float(row["yhat"]),
                "yhat_lower": float(row["yhat_lower"]),
                "yhat_upper": float(row["yhat_upper"]),
            })
        
        result = {
            "horizon_days": horizon_days,
            "forecast": forecast_data,
            "summary": f"Energy forecast for next {horizon_days} days generated",
            "total_data_points": len(ts_df),
            "forecast_points": len(forecast_data),
        }
        
        logger.info(
            "forecast.complete",
            horizon_days=horizon_days,
            forecast_points=len(forecast_data),
        )
        
        return result
        
    except Exception as e:
        logger.error("forecast.error", error=str(e), error_type=type(e).__name__)
        return {"error": f"Energy forecast failed: {str(e)}"}


def run_failure_prediction(df: pd.DataFrame) -> Dict[str, Any]:
    """Run failure prediction analysis on telemetry data.
    
    Uses Isolation Forest on rolling statistics as a proxy for failure risk assessment.
    
    Args:
        df: DataFrame with telemetry data
        
    Returns:
        Dict with failure probability, risk level, and summary
    """
    if df.empty or len(df) < 20:
        logger.warning("failure.insufficient_data", rows=len(df))
        return {"error": "Insufficient data for failure prediction (minimum 20 rows required)"}
    
    # Get numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c not in ["device_id"]]
    
    if not feature_cols:
        logger.warning("failure.no_numeric_features")
        return {"error": "No numeric features available for failure prediction"}
    
    # Fill NaN values
    X = df[feature_cols].fillna(df[feature_cols].median())
    
    try:
        # Feature engineering: rolling statistics as anomaly proxy
        X_feat = pd.DataFrame(index=X.index)
        
        for col in feature_cols:
            # Rolling mean (window of 10)
            X_feat[f"{col}_mean"] = X[col].rolling(window=10, min_periods=1).mean()
            # Rolling std (window of 10)
            X_feat[f"{col}_std"] = X[col].rolling(window=10, min_periods=1).std().fillna(0)
        
        # Use IsolationForest as proxy for failure risk
        model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies (higher = more sensitive)
            random_state=42,
            n_estimators=100,
        )
        
        scores = model.fit_predict(X_feat)
        
        # Calculate failure probability (% of anomalous samples)
        failure_prob = float((scores == -1).mean())
        
        # Determine risk level
        if failure_prob < 0.1:
            risk_level = "low"
        elif failure_prob < 0.25:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        result = {
            "failure_probability": round(failure_prob, 4),
            "risk_level": risk_level,
            "summary": f"Failure risk assessed as {risk_level} ({failure_prob*100:.1f}%)",
            "data_points_analyzed": len(df),
            "features_used": len(feature_cols),
        }
        
        logger.info(
            "failure.complete",
            failure_prob=failure_prob,
            risk_level=risk_level,
        )
        
        return result
        
    except Exception as e:
        logger.error("failure.error", error=str(e), error_type=type(e).__name__)
        return {"error": f"Failure prediction failed: {str(e)}"}


def run_ai_copilot(df: pd.DataFrame) -> Dict[str, Any]:
    """Run AI Copilot mode - automatically selects and runs appropriate models.
    
    Args:
        df: DataFrame with telemetry data
        
    Returns:
        Dict with results from multiple models and combined summary
    """
    logger.info("copilot.start", data_rows=len(df))
    
    results = {}
    
    # Run anomaly detection if sufficient data
    if not df.empty and len(df) >= 10:
        results["anomaly"] = run_anomaly_detection(df)
    
    # Run energy forecast if power column exists and sufficient data
    if "power" in df.columns and len(df) >= 24:
        results["forecast"] = run_energy_forecast(df)
    
    # Always run failure prediction if sufficient data
    if not df.empty and len(df) >= 20:
        results["failure"] = run_failure_prediction(df)
    
    # Build combined summary
    summary_parts = []
    for model_name, model_result in results.items():
        if "summary" in model_result:
            summary_parts.append(model_result["summary"])
        elif "error" in model_result:
            summary_parts.append(f"{model_name}: {model_result['error']}")
    
    result = {
        "mode": "ai_copilot",
        "models_used": list(results.keys()),
        "results": results,
        "summary": " | ".join(summary_parts) if summary_parts else "No models could be run on this dataset",
        "data_points": len(df),
    }
    
    logger.info(
        "copilot.complete",
        models_used=result["models_used"],
        data_points=len(df),
    )
    
    return result
