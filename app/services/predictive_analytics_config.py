"""
Predictive Analytics API Configuration
Settings and configuration for predictive analytics features.
"""

from typing import Dict, Any


class PredictiveAnalyticsConfig:
    """Configuration for predictive analytics service."""
    
    # Default prediction settings
    DEFAULT_PREDICTION_DAYS = 14
    MAX_PREDICTION_DAYS = 30
    MIN_PREDICTION_DAYS = 3
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.6
    LOW_CONFIDENCE_THRESHOLD = 0.4
    
    # Risk assessment weights
    RISK_WEIGHTS = {
        "temperature": 0.25,
        "humidity": 0.30,
        "rainfall": 0.35,
        "seasonal": 0.10
    }
    
    # Default locations (Kenya coffee regions)
    DEFAULT_LOCATIONS = {
        "nyeri": {"latitude": -0.4167, "longitude": 36.95, "name": "Nyeri"},
        "kiambu": {"latitude": -1.1719, "longitude": 36.8356, "name": "Kiambu"},
        "muranga": {"latitude": -0.7167, "longitude": 37.1500, "name": "Murang'a"},
        "kirinyaga": {"latitude": -0.6667, "longitude": 37.3167, "name": "Kirinyaga"},
        "embu": {"latitude": -0.5396, "longitude": 37.4503, "name": "Embu"}
    }
    
    # Activity priority levels
    ACTIVITY_PRIORITIES = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
        "optional": 5
    }
    
    # Weather impact thresholds
    WEATHER_THRESHOLDS = {
        "optimal_temperature_range": (18, 25),
        "stress_temperature_high": 30,
        "stress_temperature_low": 15,
        "optimal_rainfall_daily": (2, 15),
        "drought_threshold": 5,
        "flood_threshold": 50,
        "high_humidity_threshold": 85,
        "low_humidity_threshold": 40
    }
    
    @classmethod
    def get_location_by_name(cls, location_name: str) -> Dict[str, Any]:
        """Get location coordinates by name."""
        return cls.DEFAULT_LOCATIONS.get(location_name.lower(), {})
    
    @classmethod
    def validate_prediction_days(cls, days: int) -> int:
        """Validate and normalize prediction days."""
        return max(cls.MIN_PREDICTION_DAYS, min(days, cls.MAX_PREDICTION_DAYS))
    
    @classmethod
    def get_risk_category(cls, risk_score: float) -> str:
        """Get risk category based on score."""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
