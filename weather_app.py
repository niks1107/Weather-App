#!/usr/bin/env python3
"""
Single-file Weather App with Tkinter + Open-Meteo
Features:
 - No API key (uses Open-Meteo)
 - Autocomplete (geocoding API)
 - Current weather: temperature, humidity, wind, sunrise/sunset
 - 5-day forecast graph (matplotlib)
 - Dark/Light mode toggle
 - Celsius <-> Fahrenheit toggle
 - Simple generated icons (Pillow) embedded and created at runtime
Save this file and run: python3 weather_app_singlefile.py
Dependencies:
    pip install requests pillow matplotlib
"""

import os
import sys
import io
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageTk, ImageFont
import matplotlib.pyplot as plt
from datetime import datetime
import math

# -------------------- Configuration --------------------
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ICON_SIZE = (120, 120)
ICONS_DIR = os.path.join(os.path.dirname(__file__), "embedded_icons")

# -------------------- Utilities --------------------
def ensure_icons():
    """Create a small set of simple icons using Pillow if not present."""
    os.makedirs(ICONS_DIR, exist_ok=True)
    # Define simple icon drawing functions
    def save(img, name):
        path = os.path.join(ICONS_DIR, name)
        img.save(path, format="PNG")
    # Clear / sun
    sun = Image.new("RGBA", ICON_SIZE, (0,0,0,0))
    d = ImageDraw.Draw(sun)
    cx, cy = ICON_SIZE[0]//2, ICON_SIZE[1]//2
    r = 30
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(255,210,30,255))
    save(sun, "clear.png")
    # Cloud
    cloud = Image.new("RGBA", ICON_SIZE, (0,0,0,0))
    d = ImageDraw.Draw(cloud)
    d.ellipse((30,50,90,90), fill=(220,220,220,255))
    d.ellipse((50,40,110,80), fill=(220,220,220,255))
    d.rectangle((30,70,110,95), fill=(220,220,220,255))
    save(cloud, "clouds.png")
    # Rain
    rain = cloud.copy()
    d = ImageDraw.Draw(rain)
    d.line((50,95,50,110), fill=(60,120,255,255), width=4)
    d.line((70,95,70,110), fill=(60,120,255,255), width=4)
    d.line((90,95,90,110), fill=(60,120,255,255), width=4)
    save(rain, "rain.png")
    # Snow
    snow = cloud.copy()
    d = ImageDraw.Draw(snow)
    d.text((48,92), "*", fill=(255,255,255,255))
    d.text((68,100), "*", fill=(255,255,255,255))
    save(snow, "snow.png")
    # Thunder
    thunder = Image.new("RGBA", ICON_SIZE, (0,0,0,0))
    d = ImageDraw.Draw(thunder)
    d.ellipse((30,30,90,90), fill=(200,200,200,255))
    d.polygon([(60,60),(48,90),(66,74),(58,98)], fill=(255,220,30,255))
    save(thunder, "thunder.png")
    # Fog / mist
    mist = Image.new("RGBA", ICON_SIZE, (0,0,0,0))
    d = ImageDraw.Draw(mist)
    d.rectangle((20,50,100,60), fill=(220,220,220,200))
    d.rectangle((10,70,110,78), fill=(220,220,220,200))
    save(mist, "mist.png")
    # Night clear (moon)
    moon = Image.new("RGBA", ICON_SIZE, (0,0,0,0))
    d = ImageDraw.Draw(moon)
    d.ellipse((60,40,100,80), fill=(255,250,200,255))
    save(moon, "night_clear.png")

def icon_for_code(code):
    """Map Open-Meteo / WMO weather codes to an icon filename."""
    # Basic grouping
    if code in (0, 1):
        return "clear.png"
    if code in (2, 3):
        return "clouds.png"
    if code in (45, 48):
        return "mist.png"
    if code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "rain.png"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow.png"
    if code in (95, 96, 99):
        return "thunder.png"
    return "clouds.png"

def c_to_f(c):
    return c * 9/5 + 32

# -------------------- Networking --------------------
def geocode_query(prefix, limit=5):
    """Return a list of matching place names (simple 'autocomplete')."""
    try:
        resp = requests.get(GEOCODE_URL, params={"name": prefix, "count": limit}, timeout=8)
        resp.raise_for_status()
        j = resp.json()
        if "results" not in j:
            return []
        # Return "name, admin1, country" strings where available
        out = []
        for r in j["results"]:
            parts = [r.get("name")]
            if r.get("admin1"):
                parts.append(r.get("admin1"))
            if r.get("country"):
                parts.append(r.get("country"))
            out.append(", ".join(p for p in parts if p))
        return out
    except Exception:
        return []

def geocode_first(place):
    """Return (lat, lon, name, country) for the first matching place."""
    r = requests.get(GEOCODE_URL, params={"name": place, "count": 1}, timeout=10)
    r.raise_for_status()
    j = r.json()
    if "results" not in j or len(j["results"])==0:
        return None
    r0 = j["results"][0]
    return float(r0["latitude"]), float(r0["longitude"]), r0.get("name",""), r0.get("country","")

def fetch_weather(lat, lon):
    """Return forecast JSON including current_weather and daily arrays."""
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

# -------------------- GUI --------------------
class WeatherApp:
    def __init__(self, root):
        self.root = root
        root.title("All-in-One Weather App")
        root.geometry("520x680")
        root.resizable(False, False)
        self.is_fahrenheit = False
        self.dark_mode = True
        self.current_latlon = None
        ensure_icons()
        self.load_icon_images()

        # Styles / Colors
        self.LIGHT_BG = "#F6FBFF"
        self.LIGHT_FG = "#111111"
        self.DARK_BG = "#1f2430"
        self.DARK_FG = "#FFFFFF"

        self.build_ui()
        self.apply_theme()

    def load_icon_images(self):
        self.icon_cache = {}
        for fname in ["clear.png","clouds.png","rain.png","snow.png","thunder.png","mist.png","night_clear.png"]:
            path = os.path.join(ICONS_DIR, fname)
            try:
                im = Image.open(path).resize(ICON_SIZE, Image.LANCZOS)
                self.icon_cache[fname] = ImageTk.PhotoImage(im)
            except Exception:
                # fallback to blank
                im = Image.new("RGBA", ICON_SIZE, (200,200,200,255))
                self.icon_cache[fname] = ImageTk.PhotoImage(im)

    def build_ui(self):
        # Top frame (search + toggles)
        top = tk.Frame(self.root, height=110)
        top.pack(fill="x", pady=8)

        title = tk.Label(top, text="Weather", font=("Segoe UI", 22, "bold"))
        title.grid(row=0, column=0, columnspan=3, padx=12, sticky="w")

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, font=("Segoe UI", 14), width=26)
        self.search_entry.grid(row=1, column=0, padx=12, pady=6, sticky="w")
        self.search_entry.bind("<KeyRelease>", self.on_key)

        self.search_btn = ttk.Button(top, text="Search", command=self.on_search)
        self.search_btn.grid(row=1, column=1, padx=6)

        self.unit_btn = ttk.Button(top, text="°F", command=self.toggle_units)
        self.unit_btn.grid(row=1, column=2, padx=6)

        self.theme_btn = ttk.Button(top, text="Theme", command=self.toggle_theme)
        self.theme_btn.grid(row=0, column=3, padx=8)

        # Autocomplete listbox
        self.sugg_box = tk.Listbox(self.root, height=5)
        self.sugg_box.place(x=14, y=120, width=420)
        self.sugg_box.bind("<<ListboxSelect>>", self.on_sugg_select)
        self.sugg_box.lower()  # hide initially

        # Main info frame
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=10)

        self.icon_label = tk.Label(info_frame, image=self.icon_cache.get("clear.png"))
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=10, pady=6)

        self.temp_label = tk.Label(info_frame, text="--°C", font=("Segoe UI", 36, "bold"))
        self.temp_label.grid(row=0, column=1, sticky="w")

        self.cond_label = tk.Label(info_frame, text="Condition", font=("Segoe UI", 13))
        self.cond_label.grid(row=1, column=1, sticky="w")

        # Additional details
        details = tk.Frame(self.root)
        details.pack(pady=6)

        self.humidity_label = tk.Label(details, text="Humidity: --%", font=("Segoe UI", 12))
        self.humidity_label.grid(row=0, column=0, padx=8, pady=2)

        self.wind_label = tk.Label(details, text="Wind: -- km/h", font=("Segoe UI", 12))
        self.wind_label.grid(row=0, column=1, padx=8, pady=2)

        self.sunrise_label = tk.Label(details, text="Sunrise: --", font=("Segoe UI", 12))
        self.sunrise_label.grid(row=1, column=0, padx=8, pady=2)

        self.sunset_label = tk.Label(details, text="Sunset: --", font=("Segoe UI", 12))
        self.sunset_label.grid(row=1, column=1, padx=8, pady=2)

        # Forecast buttons
        btns = tk.Frame(self.root)
        btns.pack(pady=10)

        self.forecast_btn = ttk.Button(btns, text="Show 5-Day Forecast", command=self.show_forecast)
        self.forecast_btn.grid(row=0, column=0, padx=6)

        self.copy_btn = ttk.Button(btns, text="Copy Location", command=self.copy_location)
        self.copy_btn.grid(row=0, column=1, padx=6)

        # Result area (multiline)
        self.result_text = tk.Text(self.root, height=6, width=58, wrap="word", font=("Segoe UI", 11))
        self.result_text.pack(pady=6)
        self.result_text.config(state="disabled")

        # Footer / status
        self.status_label = tk.Label(self.root, text="Ready", anchor="w")
        self.status_label.pack(fill="x", padx=8, pady=6)

    # ---------------- UI interactions ----------------
    def on_key(self, event):
        txt = self.search_var.get().strip()
        if len(txt) < 2:
            self.sugg_box.lower()
            return
        self.status_label.config(text="Searching suggestions...")
        # perform simple autocomplete request
        suggestions = geocode_query(txt, limit=6)
        self.sugg_box.delete(0, tk.END)
        for s in suggestions:
            self.sugg_box.insert(tk.END, s)
        if suggestions:
            self.sugg_box.lift()
        else:
            self.sugg_box.lower()
        self.status_label.config(text="Ready")

    def on_sugg_select(self, event):
        sel = self.sugg_box.curselection()
        if not sel:
            return
        text = self.sugg_box.get(sel[0])
        self.search_var.set(text)
        self.sugg_box.lower()
        # auto-search upon select
        self.on_search()

    def on_search(self):
        place = self.search_var.get().strip()
        if not place:
            messagebox.showwarning("Input", "Enter a city or place name.")
            return
        self.status_label.config(text="Resolving location...")
        try:
            loc = geocode_first(place)
            if not loc:
                messagebox.showerror("Not found", "Location not found.")
                self.status_label.config(text="Ready")
                return
            lat, lon, name, country = loc
            self.current_latlon = (lat, lon, name, country)
            self.status_label.config(text=f"Fetching weather for {name}, {country}...")
            data = fetch_weather(lat, lon)
            self.update_ui_from_weather(data, name, country)
            self.status_label.config(text="Ready")
        except requests.HTTPError as e:
            messagebox.showerror("Network", f"HTTP error: {e}")
            self.status_label.config(text="Ready")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Ready")

    def update_ui_from_weather(self, data, name, country):
        cw = data.get("current_weather", {})
        # humidity provided in hourly (we asked for hourly relativehumidity_2m),
        # attempt to read nearest hour humidity from hourly arrays
        humidity = "--"
        try:
            # find hourly index for current hour
            now_iso = cw.get("time")
            if now_iso and "hourly" in data and "time" in data["hourly"]:
                times = data["hourly"]["time"]
                if now_iso in times:
                    idx = times.index(now_iso)
                    humidity = data["hourly"].get("relativehumidity_2m", ["--"]*len(times))[idx]
                else:
                    # fallback: pick first hourly humidity
                    humidity = data["hourly"].get("relativehumidity_2m", ["--"])[0]
        except Exception:
            humidity = "--"

        temp_c = cw.get("temperature", None)
        wind = cw.get("windspeed", "--")
        code = cw.get("weathercode", None)
        time_iso = cw.get("time", "")

        # daily sunrise/sunset
        sunrise = "--"
        sunset = "--"
        try:
            daily = data.get("daily", {})
            sunrise = daily.get("sunrise", ["--"])[0].split("T")[-1]
            sunset = daily.get("sunset", ["--"])[0].split("T")[-1]
        except Exception:
            pass

        # condition text
        cond_text = f"Weather code {code}" if code is not None else "Unknown"

        # apply unit conversion
        if temp_c is None:
            temp_display = "--"
        else:
            if self.is_fahrenheit:
                temp_display = f"{c_to_f(temp_c):.1f}°F"
            else:
                temp_display = f"{temp_c:.1f}°C"

        # update icon
        icon_name = icon_for_code(code) if code is not None else "clouds.png"
        ik = self.icon_cache.get(icon_name) or self.icon_cache.get("clouds.png")
        self.icon_label.config(image=ik)
        self.icon_label.image = ik

        # update labels
        self.temp_label.config(text=temp_display)
        self.cond_label.config(text=cond_text + f" — {name}, {country}")
        self.humidity_label.config(text=f"Humidity: {humidity}%")
        self.wind_label.config(text=f"Wind: {wind} km/h")
        self.sunrise_label.config(text=f"Sunrise: {sunrise}")
        self.sunset_label.config(text=f"Sunset: {sunset}")

        # show summary text
        txt = f"Location: {name}, {country}\nLocal time: {time_iso}\nTemperature: {temp_display}\nCondition: {cond_text}\nHumidity: {humidity}%\nWind: {wind} km/h\nSunrise: {sunrise}   Sunset: {sunset}"
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, txt)
        self.result_text.config(state="disabled")

    def toggle_units(self):
        self.is_fahrenheit = not self.is_fahrenheit
        self.unit_btn.config(text="°C" if self.is_fahrenheit else "°F")
        # refresh displayed temp if data available
        if self.current_latlon:
            # trigger re-fetch to accurately convert using fresh value
            lat, lon, name, country = self.current_latlon
            try:
                data = fetch_weather(lat, lon)
                self.update_ui_from_weather(data, name, country)
            except Exception:
                pass

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            bg = self.DARK_BG; fg = self.DARK_FG
        else:
            bg = self.LIGHT_BG; fg = self.LIGHT_FG
        self.root.configure(bg=bg)
        for w in self.root.winfo_children():
            try:
                w.configure(bg=bg)
            except Exception:
                pass
        # configure text elements explicitly
        for lbl in [self.temp_label, self.cond_label, self.humidity_label,
                    self.wind_label, self.sunrise_label, self.sunset_label,
                    self.status_label, self.result_text]:
            try:
                lbl.configure(bg=bg, fg=fg)
            except Exception:
                pass

    def show_forecast(self):
        if not self.current_latlon:
            messagebox.showinfo("Info", "Search for a city first.")
            return
        lat, lon, name, country = self.current_latlon
        try:
            data = fetch_weather(lat, lon)
            daily = data.get("daily", {})
            days = daily.get("time", [])
            tmax = daily.get("temperature_2m_max", [])
            tmin = daily.get("temperature_2m_min", [])
            if not days:
                messagebox.showinfo("No data", "No forecast data available.")
                return
            # plot with matplotlib (simple)
            plt.figure(figsize=(8,4))
            plt.plot(days, tmax, label="Max Temp")
            plt.plot(days, tmin, label="Min Temp")
            plt.xlabel("Date")
            plt.ylabel("Temperature")
            plt.title(f"5-Day Forecast — {name}")
            plt.legend()
            plt.xticks(rotation=30)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_location(self):
        if not self.current_latlon:
            return
        lat, lon, name, country = self.current_latlon
        s = f"{name}, {country} ({lat:.4f}, {lon:.4f})"
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(s)
            messagebox.showinfo("Copied", "Location copied to clipboard.")
        except Exception:
            pass

def main():
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()