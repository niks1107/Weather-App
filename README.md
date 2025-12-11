# Weather App

A simple command-line weather application that provides current weather conditions and 5-day forecasts for any location worldwide.

## Features

- 🌍 Search weather by location name (city, country, etc.)
- 🌡️ View current temperature, humidity, wind speed, and weather conditions
- 📅 Get 5-day weather forecasts with high/low temperatures
- 🌅 See sunrise and sunset times
- 🔄 Toggle between Celsius and Fahrenheit
- 🚀 Uses the Open-Meteo API (no API key required)

## Requirements

- Python 3.6+
- `requests` library

## Installation

1. Clone or download this repository

2. Install the required dependency:
```bash
pip install requests
```

Alternatively, if using a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install requests
```

## Usage

Run the application:
```bash
python weather_app.py
```

### Commands

- Enter any location name (e.g., "London", "New York", "Tokyo")
- Type `unit` to toggle between Celsius and Fahrenheit
- Type `quit` to exit the application

### Example Session

```
=== SIMPLE WEATHER CLI ===
Default units: Celsius
Type 'unit' to toggle C ↔ F
Type 'quit' to exit

Enter location: London
Resolving location...
Fetching weather for London, United Kingdom...

========== CURRENT WEATHER ==========
Location: London, United Kingdom
Local Time: 2024-11-17T18:00
Temperature: 12.5°C
Weather Code: 3
Humidity: 85%
Wind: 15 km/h
Sunrise: 07:15   Sunset: 16:30
=====================================

View 5-day forecast? (y/n): y

========== 5-DAY FORECAST ==========
Location: London, United Kingdom

2024-11-17: High 13.0°C | Low 8.0°C
2024-11-18: High 12.0°C | Low 7.5°C
2024-11-19: High 11.5°C | Low 6.0°C
2024-11-20: High 10.0°C | Low 5.5°C
2024-11-21: High 9.5°C | Low 4.0°C
=====================================
```
## 📸 Screenshots

### **App**
[![](https://i.postimg.cc/xTk9fD1T/weather-app-cropped.jpg)](https://postimg.cc/4mTDP0cr)
## How It Works

The application uses two Open-Meteo APIs:
1. **Geocoding API** - Converts location names to coordinates (latitude/longitude)
2. **Weather Forecast API** - Retrieves weather data for the given coordinates

## License

This project is open source and available for personal and educational use.

## Credits

Weather data provided by [Open-Meteo](https://open-meteo.com/)
