import requests
import tkinter as tk
from tkinter import messagebox


# --------- Weather Code → Text ---------
WEATHER_CODE_MAP = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫️",
    48: "Depositing Rime Fog 🌫️",
    51: "Light Drizzle 🌦️",
    53: "Moderate Drizzle 🌧️",
    55: "Dense Drizzle 🌧️",
    61: "Slight Rain 🌦️",
    63: "Moderate Rain 🌧️",
    65: "Heavy Rain 🌧️",
    71: "Light Snow ❄️",
    73: "Snow ❄️",
    75: "Heavy Snow ❄️❄️",
    80: "Rain showers 🌦️",
    81: "Rain showers 🌧️",
    82: "Violent Rain 🌧️⚡",
    95: "Thunderstorm ⛈️",
    99: "Hailstorm ⛈️",
}


# --------- API Functions ---------
def get_location(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1}

    r = requests.get(url, params=params)
    data = r.json()

    if "results" not in data:
        return None

    info = data["results"][0]
    return info["latitude"], info["longitude"], info["name"], info["country"]


def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "timezone": "auto"
    }

    r = requests.get(url, params=params)
    return r.json()["current_weather"]


# --------- GUI Logic ---------
def show_weather():
    city = city_entry.get()

    if city.strip() == "":
        messagebox.showwarning("Error", "Enter a city name!")
        return

    try:
        result = get_location(city)
        if not result:
            messagebox.showerror("Error", "City not found!")
            return

        lat, lon, name, country = result
        weather = get_weather(lat, lon)

        temperature = weather["temperature"]
        wind = weather["windspeed"]
        code = weather["weathercode"]

        condition = WEATHER_CODE_MAP.get(code, "Unknown Weather")

        output = f"""
Location: {name}, {country}
Temperature: {temperature}°C
Condition: {condition}
Wind Speed: {wind} km/h
        """

        result_label.config(text=output)

    except Exception as e:
        messagebox.showerror("Error", "Something went wrong!\n" + str(e))


# --------- GUI Window ---------
root = tk.Tk()
root.title("Weather App - Open Meteo")
root.geometry("400x400")
root.config(bg="#EAF6FF")

title_label = tk.Label(root, text="Weather App", font=("Arial", 20, "bold"), bg="#EAF6FF")
title_label.pack(pady=10)

city_entry = tk.Entry(root, font=("Arial", 14))
city_entry.pack(pady=10)

search_button = tk.Button(root, text="Search Weather", font=("Arial", 14),
                          command=show_weather, bg="#4DA8DA", fg="white")
search_button.pack(pady=10)

result_label = tk.Label(root, text="", font=("Arial", 14), bg="#EAF6FF", justify="left")
result_label.pack(pady=20)

root.mainloop()