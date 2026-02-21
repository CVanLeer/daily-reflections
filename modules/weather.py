
"""
DOC:START
Fetches local weather data from Open-Meteo API.

Purpose:
- Gets current temperature, conditions, and daily forecast for Chamblee, GA
- Uses WMO weather codes for human-readable condition descriptions
- No API key required (Open-Meteo is free)

Inputs/Outputs:
- Input: Optional lat/long (defaults to Chamblee, GA)
- Output: Dict with 'summary', 'temp', 'condition'

Side effects:
- Network call to api.open-meteo.com

Run: python modules/weather.py
See: modules/modules.md
DOC:END
"""

import requests
from datetime import datetime

def get_weather(lat=33.89, long=-84.29): # Chamblee, GA coordinates
    """
    Fetches weather for Chamblee, GA using Open-Meteo (Free, No Key).
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": long,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "temperature_unit": "fahrenheit",
            "timezone": "America/New_York",
            "forecast_days": 1
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        current = data.get('current', {})
        daily = data.get('daily', {})
        
        # Simple WMO code mapping
        wmo_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with light hail", 99: "Thunderstorm with heavy hail"
        }
        
        weather_desc = wmo_codes.get(current.get('weather_code'), "Variable")
        temp = current.get('temperature_2m')
        
        min_temp = daily.get('temperature_2m_min', [0])[0]
        max_temp = daily.get('temperature_2m_max', [0])[0]
        precip = daily.get('precipitation_probability_max', [0])[0]
        
        return {
            "summary": f"{weather_desc}. Current: {temp}°F. High: {max_temp}°F, Low: {min_temp}°F. Chance of Rain: {precip}%.",
            "temp": temp,
            "condition": weather_desc
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return {"summary": "Weather unavailable", "temp": "N/A", "condition": "N/A"}

if __name__ == "__main__":
    print(get_weather())
