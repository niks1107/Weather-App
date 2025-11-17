#!/usr/bin/env python3
"""
Simple Weather App using Open-Meteo (no API key).
Features:
 - City -> geocode -> current weather
 - Basic error handling
 - Maps weather_code to human text
"""

import requests
import sys
from datetime import datetime

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Small mapping for common Open-Meteo / WMO weather codes to text.
# This is not exhaustive — see Open-Meteo docs for full WMO codes.
WEATHER_CODE_MAP = {
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
    80: "Rain showers (slight)",
    81: "Rain showers (moderate)",
    82: "Rain showers (violent)",
    95: "Thunderstorm",
    99: "Heavy hail with thunder",
}

def geocode(city_name, limit=1):
    params = {"name": city_name, "count": limit}
    r = requests.get(GEOCODE_URL, params=params, timeout=10)
    r.raise_for_status()
    j = r.json()
    if "results" not in j or len(j["results"]) == 0:
        return None
    return j["results"][0]  # first match

def get_current_weather(lat, lon, timezone="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "timezone": timezone
    }
    r = requests.get(FORECAST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def weather_code_to_text(code):
    return WEATHER_CODE_MAP.get(code, f"Weather code {code}")

def main():
    if len(sys.argv) > 1:
        city = " ".join(sys.argv[1:])
    else:
        city = input("Enter city name (e.g. Delhi, London): ").strip()
    if not city:
        print("No city provided. Exiting.")
        return

    try:
        place = geocode(city)
    except requests.RequestException as e:
        print("Network error during geocoding:", e)
        return

    if not place:
        print(f"City '{city}' not found (geocoding returned no results).")
        return

    name = place.get("name")
    country = place.get("country")
    admin = place.get("admin1") or place.get("admin2") or ""
    lat = place.get("latitude")
    lon = place.get("longitude")

    print(f"\nLocation found: {name}, {admin} {country} (lat={lat}, lon={lon})")

    try:
        weather_json = get_current_weather(lat, lon)
    except requests.RequestException as e:
        print("Network error fetching weather:", e)
        return

    current = weather_json.get("current_weather")
    if not current:
        print("No current weather available for this location.")
        return

    # current_weather includes: temperature, windspeed, winddirection, weathercode, time
    temp = current.get("temperature")
    windspeed = current.get("windspeed")
    winddir = current.get("winddirection")
    code = current.get("weathercode")
    time_iso = current.get("time")

    readable = weather_code_to_text(code)

    # format time nicely
    try:
        time_obj = datetime.fromisoformat(time_iso)
        time_str = time_obj.strftime("%Y-%m-%d %H:%M")
    except Exception:
        time_str = time_iso or "unknown"

    print(f"\nCurrent weather at {name} ({time_str} local):")
    print(f" • Temperature: {temp} °C")
    print(f" • Condition: {readable}")
    print(f" • Weather code: {code}")
    print(f" • Wind: {windspeed} km/h at {winddir}°")

if __name__ == "__main__":
    main()