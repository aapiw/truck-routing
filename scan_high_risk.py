import requests

places = [
    ("Vail Pass, CO", 39.5297, -106.2197),
    ("Eisenhower Tunnel, CO", 39.6797, -105.9228),
    ("Donner Pass, CA", 39.3157, -120.3277),
    ("Tehachapi, CA", 35.1322, -118.4490),
    ("Columbia River Gorge, OR", 45.7118, -121.5197),
    ("Snoqualmie Pass, WA", 47.4243, -121.4136),
    ("Browning, MT", 48.5569, -113.0139),
    ("Deadhorse, AK", 70.2002, -148.4597),
    ("Utqiagvik, AK", 71.2906, -156.7886),
    ("Mount Washington, NH", 44.2705, -71.3033),
    ("Key West, FL", 24.5551, -81.7800),
    ("Hatteras, NC", 35.2193, -75.6918),
    ("Duluth, MN", 46.7867, -92.1005),
    ("Minot, ND", 48.2325, -101.2963),
    ("Williston, ND", 48.1470, -103.6180),
]

lats = ",".join(str(c[1]) for c in places)
lons = ",".join(str(c[2]) for c in places)

url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&hourly=wind_speed_10m,wind_gusts_10m,precipitation,rain,snowfall&wind_speed_unit=mph&precipitation_unit=inch&forecast_days=3"
res = requests.get(url).json()

for idx, (name, lat, lon) in enumerate(places):
    hourly = res[idx].get("hourly", {})
    times = hourly.get("time", [])
    winds = hourly.get("wind_speed_10m", [])
    gusts = hourly.get("wind_gusts_10m", [])
    rain = hourly.get("rain", [])
    snow = hourly.get("snowfall", [])
    for t, w, g, r, s in zip(times, winds, gusts, rain, snow):
        if w >= 25 or g >= 45 or r >= 0.25 or s >= 0.5:
            print(f"{name:24s} | {t} | Wind: {w:4.1f} (gust {g:4.1f}) | Rain: {r:4.2f} | Snow: {s:4.2f}")
