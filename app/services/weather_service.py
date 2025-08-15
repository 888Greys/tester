"""
OpenMeteo Weather Service for AI Agent.
Provides intelligent weather insights for coffee farming.
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather data structure."""
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    condition: str
    timestamp: datetime
    
    
@dataclass
class WeatherForecast:
    """Weather forecast structure."""
    date: str
    temperature_max: float
    temperature_min: float
    precipitation: float
    precipitation_probability: float
    wind_speed: float
    condition: str


class OpenMeteoWeatherService:
    """OpenMeteo weather service for intelligent farming insights."""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_current_weather(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """Get current weather conditions for a location."""
        try:
            url = f"{self.BASE_URL}/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
                "timezone": "Africa/Nairobi"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            
            return WeatherData(
                temperature=current.get("temperature_2m", 0),
                humidity=current.get("relative_humidity_2m", 0),
                precipitation=current.get("precipitation", 0),
                wind_speed=current.get("wind_speed_10m", 0),
                condition=self._get_weather_condition(current.get("weather_code", 0)),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch current weather: {e}")
            return None
    
    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> List[WeatherForecast]:
        """Get weather forecast for specified days."""
        try:
            url = f"{self.BASE_URL}/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code",
                "timezone": "Africa/Nairobi",
                "forecast_days": days
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily = data.get("daily", {})
            forecasts = []
            
            for i in range(len(daily.get("time", []))):
                forecasts.append(WeatherForecast(
                    date=daily["time"][i],
                    temperature_max=daily["temperature_2m_max"][i],
                    temperature_min=daily["temperature_2m_min"][i],
                    precipitation=daily["precipitation_sum"][i],
                    precipitation_probability=daily["precipitation_probability_max"][i],
                    wind_speed=daily["wind_speed_10m_max"][i],
                    condition=self._get_weather_condition(daily["weather_code"][i])
                ))
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Failed to fetch weather forecast: {e}")
            return []
    
    async def get_farming_insights(
        self, 
        weather_data: WeatherData, 
        forecast: List[WeatherForecast],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate intelligent farming insights based on weather and user profile."""
        insights = {
            "current_conditions": self._analyze_current_conditions(weather_data),
            "farming_recommendations": self._get_farming_recommendations(weather_data, forecast, user_profile),
            "alerts": self._generate_weather_alerts(weather_data, forecast),
            "optimal_activities": self._suggest_optimal_activities(weather_data, forecast, user_profile)
        }
        
        return insights
    
    def _get_weather_condition(self, weather_code: int) -> str:
        """Convert OpenMeteo weather code to readable condition."""
        conditions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return conditions.get(weather_code, "Unknown")
    
    def _analyze_current_conditions(self, weather: WeatherData) -> Dict[str, Any]:
        """Analyze current weather conditions for farming."""
        analysis = {
            "temperature_status": "optimal" if 18 <= weather.temperature <= 24 else "suboptimal",
            "humidity_status": "good" if 60 <= weather.humidity <= 80 else "concerning",
            "precipitation_status": "dry" if weather.precipitation == 0 else "wet",
            "wind_status": "calm" if weather.wind_speed < 10 else "windy"
        }
        
        # Overall assessment
        if analysis["temperature_status"] == "optimal" and analysis["humidity_status"] == "good":
            analysis["overall"] = "excellent"
        elif analysis["temperature_status"] == "optimal" or analysis["humidity_status"] == "good":
            analysis["overall"] = "good"
        else:
            analysis["overall"] = "challenging"
        
        return analysis
    
    def _get_farming_recommendations(
        self, 
        weather: WeatherData, 
        forecast: List[WeatherForecast],
        user_profile: Dict[str, Any]
    ) -> List[str]:
        """Generate farming recommendations based on weather and user profile."""
        recommendations = []
        
        # Coffee variety specific advice
        varieties = user_profile.get("coffee_varieties", [])
        if "SL28" in str(varieties):
            if weather.temperature > 25:
                recommendations.append("SL28 prefers cooler conditions - consider increasing shade cover")
        
        if "SL34" in str(varieties):
            if weather.humidity < 50:
                recommendations.append("SL34 needs good humidity - consider mulching to retain moisture")
        
        # Temperature-based recommendations
        if weather.temperature > 28:
            recommendations.append("High temperatures detected - ensure adequate shade and water supply")
        elif weather.temperature < 15:
            recommendations.append("Cool temperatures - monitor for potential frost damage")
        
        # Precipitation recommendations
        if weather.precipitation > 10:
            recommendations.append("Heavy rain - check for waterlogging and fungal disease signs")
        elif weather.precipitation == 0 and len([f for f in forecast[:3] if f.precipitation == 0]) >= 2:
            recommendations.append("Dry spell continuing - consider irrigation if available")
        
        # Humidity recommendations
        if weather.humidity > 85:
            recommendations.append("High humidity - monitor for coffee leaf rust and berry disease")
        elif weather.humidity < 40:
            recommendations.append("Low humidity - increase mulching and consider shade management")
        
        # Wind recommendations
        if weather.wind_speed > 15:
            recommendations.append("Strong winds - check for branch damage and secure young plants")
        
        return recommendations
    
    def _generate_weather_alerts(
        self, 
        weather: WeatherData, 
        forecast: List[WeatherForecast]
    ) -> List[Dict[str, str]]:
        """Generate weather alerts for farming activities."""
        alerts = []
        
        # Current weather alerts
        if weather.temperature > 30:
            alerts.append({
                "type": "heat_warning",
                "severity": "high",
                "message": "Extreme heat detected - protect plants and ensure adequate water"
            })
        
        if weather.precipitation > 20:
            alerts.append({
                "type": "heavy_rain",
                "severity": "medium",
                "message": "Heavy rainfall - monitor for waterlogging and disease"
            })
        
        # Forecast-based alerts
        for i, day in enumerate(forecast[:3]):
            if day.precipitation_probability > 80 and day.precipitation > 15:
                alerts.append({
                    "type": "rain_forecast",
                    "severity": "medium",
                    "message": f"Heavy rain expected in {i+1} day(s) - prepare drainage and harvest if ready"
                })
            
            if day.temperature_max > 32:
                alerts.append({
                    "type": "heat_forecast",
                    "severity": "high",
                    "message": f"Extreme heat expected in {i+1} day(s) - prepare shade and irrigation"
                })
        
        return alerts
    
    def _suggest_optimal_activities(
        self, 
        weather: WeatherData, 
        forecast: List[WeatherForecast],
        user_profile: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Suggest optimal farming activities based on weather conditions."""
        activities = {
            "today": [],
            "this_week": [],
            "avoid_today": []
        }
        
        # Today's activities based on current weather
        if weather.precipitation == 0 and weather.wind_speed < 10:
            activities["today"].extend([
                "Pruning and maintenance work",
                "Fertilizer application",
                "Pest and disease inspection"
            ])
        
        if weather.precipitation > 0:
            activities["today"].extend([
                "Indoor processing activities",
                "Equipment maintenance",
                "Record keeping and planning"
            ])
            activities["avoid_today"].extend([
                "Spraying pesticides or fungicides",
                "Harvesting (if possible to delay)"
            ])
        
        if 20 <= weather.temperature <= 26 and weather.humidity >= 60:
            activities["today"].append("Ideal conditions for planting new seedlings")
        
        # Weekly planning based on forecast
        dry_days = [f for f in forecast if f.precipitation < 2]
        if len(dry_days) >= 3:
            activities["this_week"].extend([
                "Plan major pruning activities",
                "Soil preparation and fertilization",
                "Infrastructure maintenance"
            ])
        
        rainy_days = [f for f in forecast if f.precipitation > 5]
        if len(rainy_days) >= 2:
            activities["this_week"].extend([
                "Focus on post-harvest processing",
                "Equipment servicing",
                "Disease monitoring preparation"
            ])
        
        return activities
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global weather service instance
weather_service = OpenMeteoWeatherService()