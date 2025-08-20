"""
Predictive Analytics Service for Coffee Farming
Provides weather-based recommendations, seasonal predictions, and farming insights.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import math

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityType(Enum):
    PLANTING = "planting"
    FERTILIZING = "fertilizing"
    PRUNING = "pruning"
    PEST_CONTROL = "pest_control"
    HARVESTING = "harvesting"
    IRRIGATION = "irrigation"
    DISEASE_PREVENTION = "disease_prevention"


@dataclass
class PredictionResult:
    confidence: float
    timeframe: str
    description: str
    recommendation: str
    risk_level: RiskLevel
    supporting_data: Dict[str, Any]


@dataclass
class WeatherPrediction:
    date: str
    temperature_range: Tuple[float, float]
    rainfall_probability: float
    rainfall_amount: float
    humidity: float
    conditions: str
    farming_impact: str


@dataclass
class SeasonalPrediction:
    season: str
    start_date: str
    end_date: str
    key_activities: List[str]
    expected_weather: str
    recommendations: List[str]
    risk_factors: List[str]


class PredictiveAnalyticsService:
    """Service for predictive analytics and farming recommendations."""
    
    def __init__(self):
        """Initialize the predictive analytics service."""
        self.weather_service = None
        self.memory_service = None
        
        # Kenya coffee farming calendar
        self.coffee_calendar = {
            "long_rains": {"start": "03-15", "end": "05-31", "activities": ["fertilizing", "disease_prevention", "pruning"]},
            "dry_season_1": {"start": "06-01", "end": "09-30", "activities": ["pest_control", "irrigation", "harvesting"]},
            "short_rains": {"start": "10-01", "end": "12-31", "activities": ["planting", "fertilizing", "soil_preparation"]},
            "dry_season_2": {"start": "01-01", "end": "03-14", "activities": ["harvesting", "processing", "maintenance"]}
        }
        
        # Disease and pest risk factors
        self.risk_factors = {
            "coffee_berry_disease": {
                "temperature_range": (15, 25),
                "humidity_threshold": 80,
                "rainfall_threshold": 100,
                "season_risk": ["long_rains", "short_rains"]
            },
            "coffee_leaf_rust": {
                "temperature_range": (18, 28),
                "humidity_threshold": 85,
                "rainfall_threshold": 150,
                "season_risk": ["long_rains"]
            },
            "coffee_berry_borer": {
                "temperature_range": (20, 30),
                "humidity_threshold": 70,
                "rainfall_threshold": 50,
                "season_risk": ["dry_season_1", "dry_season_2"]
            }
        }
        
    async def initialize(self):
        """Initialize dependencies."""
        try:
            from app.services.weather_service import weather_service
            from app.services.memory_intelligence import memory_intelligence_service
            self.weather_service = weather_service
            self.memory_service = memory_intelligence_service
            logger.info("Predictive analytics service initialized")
        except Exception as e:
            logger.error(f"Error initializing predictive analytics: {str(e)}")
    
    async def get_farming_predictions(
        self, 
        latitude: float, 
        longitude: float, 
        user_id: Optional[str] = None,
        days_ahead: int = 14
    ) -> Dict[str, Any]:
        """
        Get comprehensive farming predictions for a location.
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            user_id: User ID for personalized predictions
            days_ahead: Number of days to predict ahead
            
        Returns:
            Comprehensive prediction results
        """
        try:
            # Get weather forecast
            weather_forecast = await self._get_weather_predictions(latitude, longitude, days_ahead)
            
            # Get seasonal predictions
            seasonal_predictions = await self._get_seasonal_predictions()
            
            # Get disease/pest risk predictions
            risk_predictions = await self._predict_disease_pest_risks(weather_forecast)
            
            # Get activity recommendations
            activity_recommendations = await self._get_activity_recommendations(
                weather_forecast, seasonal_predictions, user_id
            )
            
            # Get yield predictions
            yield_predictions = await self._predict_yield_impacts(weather_forecast, user_id)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "location": {"latitude": latitude, "longitude": longitude},
                "prediction_period": f"{days_ahead} days",
                "weather_predictions": weather_forecast,
                "seasonal_predictions": seasonal_predictions,
                "risk_predictions": risk_predictions,
                "activity_recommendations": activity_recommendations,
                "yield_predictions": yield_predictions,
                "confidence_score": self._calculate_overall_confidence(weather_forecast)
            }
            
        except Exception as e:
            logger.error(f"Error getting farming predictions: {str(e)}")
            return {"error": str(e)}
    
    async def _get_weather_predictions(self, latitude: float, longitude: float, days: int) -> List[WeatherPrediction]:
        """Get weather predictions for farming decisions."""
        try:
            if not self.weather_service:
                return []
            
            # Get weather forecast
            forecast = await self.weather_service.get_forecast(latitude, longitude, days)
            
            predictions = []
            for day in forecast:
                farming_impact = self._analyze_farming_impact(day)
                
                prediction = WeatherPrediction(
                    date=day.date,
                    temperature_range=(day.temperature_min, day.temperature_max),
                    rainfall_probability=day.precipitation_probability,
                    rainfall_amount=day.precipitation,
                    humidity=getattr(day, 'humidity', 70),  # Default if not available
                    conditions=day.description,
                    farming_impact=farming_impact
                )
                predictions.append(prediction)
            
            return [pred.__dict__ for pred in predictions]
            
        except Exception as e:
            logger.error(f"Error getting weather predictions: {str(e)}")
            return []
    
    def _analyze_farming_impact(self, weather_day) -> str:
        """Analyze the farming impact of weather conditions."""
        temp_avg = (weather_day.temperature_min + weather_day.temperature_max) / 2
        rainfall = weather_day.precipitation
        
        impacts = []
        
        # Temperature analysis
        if temp_avg < 15:
            impacts.append("Cold stress risk for coffee plants")
        elif temp_avg > 30:
            impacts.append("Heat stress possible, consider shade/irrigation")
        elif 18 <= temp_avg <= 25:
            impacts.append("Optimal temperature for coffee growth")
        
        # Rainfall analysis
        if rainfall > 100:
            impacts.append("Heavy rain - disease risk increased, avoid spraying")
        elif rainfall > 50:
            impacts.append("Good conditions for plant growth")
        elif rainfall < 10:
            impacts.append("Dry conditions - irrigation may be needed")
        
        # Activity recommendations
        if rainfall < 5 and temp_avg < 25:
            impacts.append("Good day for field activities")
        elif rainfall > 20:
            impacts.append("Avoid field work, focus on indoor tasks")
        
        return "; ".join(impacts) if impacts else "Normal farming conditions expected"
    
    async def _get_seasonal_predictions(self) -> Dict[str, Any]:
        """Get seasonal farming predictions."""
        try:
            current_date = datetime.now()
            current_season = self._get_current_season(current_date)
            next_season = self._get_next_season(current_date)
            
            return {
                "current_season": {
                    "name": current_season,
                    "details": self.coffee_calendar[current_season],
                    "days_remaining": self._days_until_season_end(current_date, current_season)
                },
                "next_season": {
                    "name": next_season,
                    "details": self.coffee_calendar[next_season],
                    "days_until_start": self._days_until_season_start(current_date, next_season)
                },
                "yearly_timeline": self._get_yearly_timeline()
            }
            
        except Exception as e:
            logger.error(f"Error getting seasonal predictions: {str(e)}")
            return {}
    
    def _get_current_season(self, date: datetime) -> str:
        """Determine current farming season."""
        month_day = date.strftime("%m-%d")
        
        for season, details in self.coffee_calendar.items():
            start = details["start"]
            end = details["end"]
            
            # Handle year boundary
            if start <= end:  # Same year
                if start <= month_day <= end:
                    return season
            else:  # Crosses year boundary
                if month_day >= start or month_day <= end:
                    return season
        
        return "transition_period"
    
    def _get_next_season(self, date: datetime) -> str:
        """Get the next farming season."""
        current = self._get_current_season(date)
        seasons = list(self.coffee_calendar.keys())
        
        try:
            current_index = seasons.index(current)
            next_index = (current_index + 1) % len(seasons)
            return seasons[next_index]
        except ValueError:
            return seasons[0]
    
    async def _predict_disease_pest_risks(self, weather_forecast: List[Dict]) -> Dict[str, Any]:
        """Predict disease and pest risks based on weather."""
        try:
            risk_predictions = {}
            
            for disease, factors in self.risk_factors.items():
                risk_score = 0
                risk_days = 0
                
                for day in weather_forecast:
                    day_risk = 0
                    
                    # Temperature risk
                    temp_avg = (day["temperature_range"][0] + day["temperature_range"][1]) / 2
                    if factors["temperature_range"][0] <= temp_avg <= factors["temperature_range"][1]:
                        day_risk += 0.3
                    
                    # Humidity risk (using rainfall as proxy)
                    if day["rainfall_amount"] > factors["rainfall_threshold"] / 10:  # Scale down
                        day_risk += 0.4
                    
                    # Rainfall risk
                    if day["rainfall_amount"] > factors["rainfall_threshold"] / 30:  # Scale down
                        day_risk += 0.3
                    
                    if day_risk > 0.5:
                        risk_days += 1
                        risk_score += day_risk
                
                # Calculate risk level
                avg_risk = risk_score / len(weather_forecast) if weather_forecast else 0
                risk_level = self._calculate_risk_level(avg_risk, risk_days)
                
                risk_predictions[disease] = {
                    "risk_level": risk_level.value,
                    "risk_score": round(avg_risk, 2),
                    "high_risk_days": risk_days,
                    "prevention_advice": self._get_prevention_advice(disease, risk_level),
                    "monitoring_advice": f"Monitor plants closely for {disease.replace('_', ' ')} symptoms"
                }
            
            return risk_predictions
            
        except Exception as e:
            logger.error(f"Error predicting disease/pest risks: {str(e)}")
            return {}
    
    def _calculate_risk_level(self, avg_risk: float, risk_days: int) -> RiskLevel:
        """Calculate overall risk level."""
        if avg_risk > 0.7 or risk_days > 10:
            return RiskLevel.CRITICAL
        elif avg_risk > 0.5 or risk_days > 7:
            return RiskLevel.HIGH
        elif avg_risk > 0.3 or risk_days > 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _get_prevention_advice(self, disease: str, risk_level: RiskLevel) -> str:
        """Get prevention advice for diseases/pests."""
        advice_map = {
            "coffee_berry_disease": {
                RiskLevel.LOW: "Continue regular monitoring",
                RiskLevel.MEDIUM: "Apply preventive copper-based fungicide",
                RiskLevel.HIGH: "Increase spray frequency, improve drainage",
                RiskLevel.CRITICAL: "Emergency fungicide application, remove affected berries"
            },
            "coffee_leaf_rust": {
                RiskLevel.LOW: "Monitor lower leaves weekly",
                RiskLevel.MEDIUM: "Apply preventive fungicide, improve air circulation",
                RiskLevel.HIGH: "Systemic fungicide treatment, increase nutrition",
                RiskLevel.CRITICAL: "Emergency treatment protocol, consider resistant varieties"
            },
            "coffee_berry_borer": {
                RiskLevel.LOW: "Regular berry inspection",
                RiskLevel.MEDIUM: "Set up monitoring traps, harvest ripe berries promptly",
                RiskLevel.HIGH: "Apply biocontrol agents, intensive monitoring",
                RiskLevel.CRITICAL: "Emergency insecticide treatment, mass trapping"
            }
        }
        
        return advice_map.get(disease, {}).get(risk_level, "Monitor and maintain good farm hygiene")
    
    async def _get_activity_recommendations(
        self, 
        weather_forecast: List[Dict], 
        seasonal_predictions: Dict,
        user_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get farming activity recommendations."""
        try:
            recommendations = []
            
            # Get user's farming history if available
            user_context = await self._get_user_farming_context(user_id) if user_id else {}
            
            # Current season activities
            current_season = seasonal_predictions.get("current_season", {})
            if current_season:
                for activity in current_season.get("details", {}).get("activities", []):
                    rec = await self._generate_activity_recommendation(
                        activity, weather_forecast, user_context
                    )
                    if rec:
                        recommendations.append(rec)
            
            # Weather-specific recommendations
            for i, day in enumerate(weather_forecast[:7]):  # Next 7 days
                day_recommendations = self._get_daily_recommendations(day, i)
                recommendations.extend(day_recommendations)
            
            # Sort by priority
            recommendations.sort(key=lambda x: x.get("priority", 5))
            
            return recommendations[:10]  # Top 10 recommendations
            
        except Exception as e:
            logger.error(f"Error getting activity recommendations: {str(e)}")
            return []
    
    async def _generate_activity_recommendation(
        self, 
        activity: str, 
        weather_forecast: List[Dict],
        user_context: Dict
    ) -> Optional[Dict[str, Any]]:
        """Generate specific activity recommendation."""
        try:
            activity_templates = {
                "fertilizing": {
                    "title": "Fertilizer Application",
                    "description": "Apply balanced fertilizer during optimal weather conditions",
                    "optimal_conditions": {"max_rain": 10, "min_temp": 15, "max_temp": 28},
                    "priority": 2
                },
                "pest_control": {
                    "title": "Pest Control Spray",
                    "description": "Apply pest control treatments when weather permits",
                    "optimal_conditions": {"max_rain": 5, "max_wind": 15},
                    "priority": 1
                },
                "pruning": {
                    "title": "Pruning Activities",
                    "description": "Conduct pruning during dry weather to prevent disease",
                    "optimal_conditions": {"max_rain": 2, "min_temp": 10},
                    "priority": 3
                }
            }
            
            template = activity_templates.get(activity)
            if not template:
                return None
            
            # Find optimal days
            optimal_days = []
            for i, day in enumerate(weather_forecast):
                if self._is_optimal_day(day, template["optimal_conditions"]):
                    optimal_days.append(i)
            
            if not optimal_days:
                return None
            
            return {
                "activity": activity,
                "title": template["title"],
                "description": template["description"],
                "recommended_days": optimal_days[:3],  # Top 3 days
                "priority": template["priority"],
                "weather_dependent": True
            }
            
        except Exception as e:
            logger.error(f"Error generating activity recommendation: {str(e)}")
            return None
    
    def _is_optimal_day(self, day: Dict, conditions: Dict) -> bool:
        """Check if day meets optimal conditions for activity."""
        if day["rainfall_amount"] > conditions.get("max_rain", 50):
            return False
        
        temp_avg = (day["temperature_range"][0] + day["temperature_range"][1]) / 2
        if temp_avg < conditions.get("min_temp", 0) or temp_avg > conditions.get("max_temp", 50):
            return False
        
        return True
    
    def _get_daily_recommendations(self, day: Dict, day_index: int) -> List[Dict[str, Any]]:
        """Get recommendations for a specific day."""
        recommendations = []
        
        rainfall = day["rainfall_amount"]
        temp_avg = (day["temperature_range"][0] + day["temperature_range"][1]) / 2
        
        # High rainfall day
        if rainfall > 20:
            recommendations.append({
                "title": "Indoor Activities",
                "description": "Focus on record keeping, equipment maintenance, or planning",
                "day": day_index,
                "priority": 4,
                "reason": f"Heavy rain expected ({rainfall:.1f}mm)"
            })
        
        # Hot day
        elif temp_avg > 28:
            recommendations.append({
                "title": "Early Morning Work",
                "description": "Schedule field activities for early morning to avoid heat stress",
                "day": day_index,
                "priority": 3,
                "reason": f"High temperature expected ({temp_avg:.1f}°C)"
            })
        
        # Ideal working day
        elif rainfall < 5 and 18 <= temp_avg <= 25:
            recommendations.append({
                "title": "Optimal Field Work Day",
                "description": "Excellent conditions for most farming activities",
                "day": day_index,
                "priority": 1,
                "reason": "Ideal weather conditions"
            })
        
        return recommendations
    
    async def _predict_yield_impacts(self, weather_forecast: List[Dict], user_id: Optional[str]) -> Dict[str, Any]:
        """Predict yield impacts based on weather and farming practices."""
        try:
            # Simple yield impact model
            impact_score = 0
            factors = []
            
            # Analyze weather patterns
            total_rainfall = sum(day["rainfall_amount"] for day in weather_forecast)
            avg_temp = sum((day["temperature_range"][0] + day["temperature_range"][1]) / 2 for day in weather_forecast) / len(weather_forecast)
            
            # Rainfall impact
            if 200 <= total_rainfall <= 400:  # Optimal range for 2 weeks
                impact_score += 0.2
                factors.append("Optimal rainfall pattern")
            elif total_rainfall < 100:
                impact_score -= 0.1
                factors.append("Insufficient rainfall - irrigation recommended")
            elif total_rainfall > 500:
                impact_score -= 0.15
                factors.append("Excessive rainfall - drainage concerns")
            
            # Temperature impact
            if 18 <= avg_temp <= 25:
                impact_score += 0.15
                factors.append("Optimal temperature range")
            elif avg_temp > 30:
                impact_score -= 0.1
                factors.append("High temperatures may stress plants")
            elif avg_temp < 15:
                impact_score -= 0.05
                factors.append("Cool temperatures may slow growth")
            
            # Convert to percentage impact
            yield_impact_percent = impact_score * 100
            
            return {
                "predicted_impact": f"{yield_impact_percent:+.1f}%",
                "impact_category": self._categorize_yield_impact(yield_impact_percent),
                "contributing_factors": factors,
                "confidence": 0.7,  # Medium confidence for short-term predictions
                "recommendations": self._get_yield_optimization_advice(yield_impact_percent)
            }
            
        except Exception as e:
            logger.error(f"Error predicting yield impacts: {str(e)}")
            return {}
    
    def _categorize_yield_impact(self, impact_percent: float) -> str:
        """Categorize yield impact."""
        if impact_percent > 10:
            return "Very Positive"
        elif impact_percent > 5:
            return "Positive"
        elif impact_percent > -5:
            return "Neutral"
        elif impact_percent > -10:
            return "Negative"
        else:
            return "Very Negative"
    
    def _get_yield_optimization_advice(self, impact_percent: float) -> List[str]:
        """Get advice for yield optimization."""
        if impact_percent > 5:
            return [
                "Excellent conditions - maintain current practices",
                "Consider increasing fertilizer application to maximize potential",
                "Monitor for optimal harvest timing"
            ]
        elif impact_percent < -5:
            return [
                "Implement mitigation strategies",
                "Ensure adequate irrigation during dry spells",
                "Apply foliar fertilizers to support stressed plants",
                "Monitor for disease/pest pressure"
            ]
        else:
            return [
                "Maintain standard farming practices",
                "Monitor weather changes closely",
                "Be ready to adjust irrigation and nutrition"
            ]
    
    async def _get_user_farming_context(self, user_id: str) -> Dict[str, Any]:
        """Get user's farming context from memory."""
        try:
            if not self.memory_service:
                return {}
            
            # Get user's farming-related conversations
            context = await self.memory_service.get_intelligent_memory_context(
                query="farming practices fertilizer pest management",
                user_id=user_id,
                max_memories=10
            )
            
            # Extract farming practices and preferences
            farming_context = {
                "experience_level": "intermediate",  # Default
                "preferred_practices": [],
                "farm_size": None,
                "location": None
            }
            
            # Analyze memories for farming context
            memories = context.get("relevant_memories", [])
            for memory in memories:
                content = memory.get("content", "").lower()
                
                # Extract farm size
                if "hectare" in content or "ha" in content:
                    # Simple extraction - could be improved
                    try:
                        import re
                        numbers = re.findall(r'\d+\.?\d*', content)
                        if numbers:
                            farming_context["farm_size"] = float(numbers[0])
                    except:
                        pass
                
                # Extract practices
                if "organic" in content:
                    farming_context["preferred_practices"].append("organic")
                if "irrigation" in content:
                    farming_context["preferred_practices"].append("irrigation")
            
            return farming_context
            
        except Exception as e:
            logger.error(f"Error getting user farming context: {str(e)}")
            return {}
    
    def _calculate_overall_confidence(self, weather_forecast: List[Dict]) -> float:
        """Calculate overall confidence in predictions."""
        # Base confidence decreases with time
        base_confidence = 0.9
        
        # Reduce confidence for longer forecasts
        days = len(weather_forecast)
        time_decay = max(0.5, 1 - (days - 1) * 0.05)
        
        return round(base_confidence * time_decay, 2)
    
    def _get_yearly_timeline(self) -> List[Dict[str, Any]]:
        """Get yearly farming timeline."""
        timeline = []
        for season, details in self.coffee_calendar.items():
            timeline.append({
                "season": season,
                "period": f"{details['start']} to {details['end']}",
                "key_activities": details["activities"],
                "description": self._get_season_description(season)
            })
        return timeline
    
    def _get_season_description(self, season: str) -> str:
        """Get description for farming season."""
        descriptions = {
            "long_rains": "Main growing season with heavy rainfall and active plant growth",
            "dry_season_1": "First dry period, focus on pest control and early harvest",
            "short_rains": "Second growing season with moderate rainfall, good for planting",
            "dry_season_2": "Main harvest and processing season"
        }
        return descriptions.get(season, "Farming season")
    
    def _days_until_season_end(self, current_date: datetime, season: str) -> int:
        """Calculate days until current season ends."""
        try:
            end_date_str = self.coffee_calendar[season]["end"]
            end_month, end_day = map(int, end_date_str.split("-"))
            
            # Handle year boundary
            end_date = current_date.replace(month=end_month, day=end_day)
            if end_date < current_date:
                end_date = end_date.replace(year=end_date.year + 1)
            
            return (end_date - current_date).days
        except:
            return 0
    
    def _days_until_season_start(self, current_date: datetime, season: str) -> int:
        """Calculate days until next season starts."""
        try:
            start_date_str = self.coffee_calendar[season]["start"]
            start_month, start_day = map(int, start_date_str.split("-"))
            
            start_date = current_date.replace(month=start_month, day=start_day)
            if start_date < current_date:
                start_date = start_date.replace(year=start_date.year + 1)
            
            return (start_date - current_date).days
        except:
            return 0


# Global service instance
predictive_analytics_service = PredictiveAnalyticsService()
