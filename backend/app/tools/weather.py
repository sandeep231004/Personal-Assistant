"""
Weather Tool using Open-Meteo API (free, no API key needed).
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import httpx
import logging

logger = logging.getLogger(__name__)


class WeatherInput(BaseModel):
    """Input schema for weather tool."""
    location: str = Field(description="City name or location to get weather for")


class WeatherTool(BaseTool):
    """
    Tool for getting current weather information.

    Uses Open-Meteo API (free, no API key required).

    Use this when:
    - User asks about weather
    - User wants temperature, conditions
    - User asks "what's the weather like"
    """

    name: str = "get_weather"
    description: str = (
        "Get current weather information for a specific location. "
        "ONLY use when user explicitly asks about WEATHER, temperature, or conditions. "
        "Provides temperature, weather conditions, wind speed, and humidity. "
        "Input should be a city name."
    )
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, location: str) -> str:
        """
        Get weather for a location.

        Args:
            location: City name or location

        Returns:
            Weather information or error message
        """
        try:
            logger.info(f"Getting weather for: {location}")

            # Step 1: Geocode the location (get coordinates)
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            geocode_params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }

            with httpx.Client(timeout=10.0) as client:
                geo_response = client.get(geocode_url, params=geocode_params)
                geo_data = geo_response.json()

                if "results" not in geo_data or not geo_data["results"]:
                    return f"❌ Could not find location: {location}. Please try a different city name."

                # Get coordinates
                result = geo_data["results"][0]
                latitude = result["latitude"]
                longitude = result["longitude"]
                city_name = result["name"]
                country = result.get("country", "")

                # Step 2: Get weather data
                weather_url = "https://api.open-meteo.com/v1/forecast"
                weather_params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                    "timezone": "auto"
                }

                weather_response = client.get(weather_url, params=weather_params)
                weather_data = weather_response.json()

                if "current" not in weather_data:
                    return "❌ Could not retrieve weather data. Please try again."

                current = weather_data["current"]

                # Map weather codes to descriptions
                weather_code = current.get("weather_code", 0)
                condition = self._get_weather_condition(weather_code)

                # Format response
                temp_c = current.get("temperature_2m", "N/A")
                feels_like_c = current.get("apparent_temperature", "N/A")
                humidity = current.get("relative_humidity_2m", "N/A")
                wind_speed = current.get("wind_speed_10m", "N/A")
                precipitation = current.get("precipitation", 0)

                # Convert to Fahrenheit
                temp_f = round((temp_c * 9/5) + 32, 1) if temp_c != "N/A" else "N/A"
                feels_like_f = round((feels_like_c * 9/5) + 32, 1) if feels_like_c != "N/A" else "N/A"

                response = f"""🌤️ Weather for {city_name}, {country}

📍 Location: {latitude}°N, {longitude}°E

🌡️ Temperature: {temp_c}°C ({temp_f}°F)
🤔 Feels like: {feels_like_c}°C ({feels_like_f}°F)
☁️ Conditions: {condition}
💧 Humidity: {humidity}%
💨 Wind Speed: {wind_speed} km/h
🌧️ Precipitation: {precipitation} mm
"""

                logger.info(f"Successfully retrieved weather for {city_name}")
                return response

        except httpx.TimeoutException:
            return "❌ Weather service timed out. Please try again."
        except Exception as e:
            error_msg = f"Error getting weather: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"

    def _get_weather_condition(self, code: int) -> str:
        """
        Map WMO weather code to description.

        Args:
            code: WMO weather code

        Returns:
            Weather condition description
        """
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
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
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }

        return weather_codes.get(code, f"Unknown (code: {code})")

    async def _arun(self, location: str) -> str:
        """Async version (falls back to sync)."""
        return self._run(location)


def get_weather_tool() -> WeatherTool:
    """Factory function to create weather tool instance."""
    return WeatherTool()
