import os

import httpx
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get current weather (temperature, condition, humidity) for a city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        return f"{city}: {temp}°C, {condition}, humidity {humidity}%"
    except Exception as e:
        return f"Weather lookup failed: {e}"
