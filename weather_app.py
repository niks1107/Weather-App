import requests
from datetime import datetime

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def c_to_f(c):
    return c * 9/5 + 32


def geocode_first(place):
    try:
        r = requests.get(GEOCODE_URL, params={"name": place, "count": 1}, timeout=10)
        r.raise_for_status()
        j = r.json()

        if "results" not in j or len(j["results"]) == 0:
            return None

        r0 = j["results"][0]
        return float(r0["latitude"]), float(r0["longitude"]), r0.get("name",""), r0.get("country","")
    except:
        return None


def fetch_weather(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "relativehumidity_2m",
        "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
        "timezone": "auto"
    }
    r = requests.get(FORECAST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def show_current_weather(data, name, country, use_f):
    cw = data.get("current_weather", {})

    temp_c = cw.get("temperature")
    wind = cw.get("windspeed", "--")
    code = cw.get("weathercode")
    time_iso = cw.get("time", "")

    # humidity
    humidity = "--"
    try:
        now_iso = cw.get("time")
        times = data["hourly"]["time"]
        hums = data["hourly"]["relativehumidity_2m"]
        if now_iso in times:
            i = times.index(now_iso)
            humidity = hums[i]
    except:
        pass

    sunrise = data.get("daily", {}).get("sunrise", ["--"])[0].split("T")[-1]
    sunset = data.get("daily", {}).get("sunset", ["--"])[0].split("T")[-1]

    if temp_c is None:
        temp = "--"
    else:
        temp = f"{c_to_f(temp_c):.1f}°F" if use_f else f"{temp_c:.1f}°C"

    print("\n========== CURRENT WEATHER ==========")
    print(f"Location: {name}, {country}")
    print(f"Local Time: {time_iso}")
    print(f"Temperature: {temp}")
    print(f"Weather Code: {code}")
    print(f"Humidity: {humidity}%")
    print(f"Wind: {wind} km/h")
    print(f"Sunrise: {sunrise}   Sunset: {sunset}")
    print("=====================================\n")


def show_forecast(data, name, country, use_f):
    daily = data.get("daily", {})
    days = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])

    print("\n========== 5-DAY FORECAST ==========")
    print(f"Location: {name}, {country}\n")

    for i, day in enumerate(days[:5]):
        d = day.split("T")[0]
        if i < len(tmax) and i < len(tmin):
            hi = tmax[i]
            lo = tmin[i]

            if use_f:
                hi = c_to_f(hi)
                lo = c_to_f(lo)
                unit = "°F"
            else:
                unit = "°C"

            print(f"{d}: High {hi:.1f}{unit} | Low {lo:.1f}{unit}")

    print("=====================================\n")


def main():
    use_f = False  # default Celsius

    print("=== SIMPLE WEATHER CLI ===")
    print("Default units: Celsius")
    print("Type 'unit' to toggle C ↔ F")
    print("Type 'quit' to exit\n")

    while True:
        place = input("Enter location: ").strip()

        if place.lower() == "quit":
            break

        if place.lower() == "unit":
            use_f = not use_f
            print(f"Units changed to: {'°F' if use_f else '°C'}\n")
            continue

        if not place:
            continue

        print("Resolving location...")

        loc = geocode_first(place)
        if not loc:
            print("❌ Location not found.\n")
            continue

        lat, lon, name, country = loc

        print(f"Fetching weather for {name}, {country}...")
        data = fetch_weather(lat, lon)

        show_current_weather(data, name, country, use_f)

        # ask for forecast
        cmd = input("View 5-day forecast? (y/n): ").lower()
        if cmd == "y":
            show_forecast(data, name, country, use_f)


if __name__ == "__main__":
    main()