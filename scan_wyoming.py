import requests

wyoming_points = [
    ("Arlington, WY", 41.5936, -106.2131),
    ("Elk Mountain, WY", 41.6883, -106.4172),
    ("Laramie, WY", 41.3114, -105.5911),
    ("Rawlins, WY", 41.7911, -107.2387),
    ("Wamsutter, WY", 41.6694, -107.9754),
    ("Rock Springs, WY", 41.5875, -109.2029),
    ("Evanston, WY", 41.2683, -110.9632),
    ("Livingston, MT", 45.6624, -110.5613),
    ("Bozeman, MT", 45.6770, -111.0429),
    ("Cut Bank, MT", 48.6331, -112.3259),
    ("Pueblo, CO", 38.2544, -104.6091),
    ("Lubbock, TX", 33.5779, -101.8552),
    ("Barrow, AK", 71.2906, -156.7886),
    ("Deadhorse, AK", 70.2002, -148.4597),
]

lats = ",".join(str(c[1]) for c in wyoming_points)
lons = ",".join(str(c[2]) for c in wyoming_points)

url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&hourly=wind_speed_10m,wind_gusts_10m,precipitation,rain,snowfall&wind_speed_unit=mph&precipitation_unit=inch&forecast_days=3"
res = requests.get(url).json()

for idx, (name, lat, lon) in enumerate(wyoming_points):
    hourly = res[idx].get("hourly", {})
    times = hourly.get("time", [])
    winds = hourly.get("wind_speed_10m", [])
    gusts = hourly.get("wind_gusts_10m", [])
    rain = hourly.get("rain", [])
    snow = hourly.get("snowfall", [])
    for t, w, g, r, s in zip(times, winds, gusts, rain, snow):
        if w >= 25 or r >= 0.25 or s >= 0.5:
            print(f"{name:18s} | {t} | Wind: {w:4.1f} mph (gust {g:4.1f}) | Rain: {r:4.2f} in/hr | Snow: {s:4.2f} in/hr")
