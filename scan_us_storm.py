import requests

# Test a broad grid across US
test_cities = [
    ("Miami, FL", 25.7617, -80.1918),
    ("Tampa, FL", 27.9506, -82.4572),
    ("New Orleans, LA", 29.9511, -90.0715),
    ("Houston, TX", 29.7604, -95.3698),
    ("Oklahoma City, OK", 35.4676, -97.5164),
    ("Kansas City, MO", 39.0997, -94.5786),
    ("Minneapolis, MN", 44.9778, -93.2650),
    ("Boston, MA", 42.3601, -71.0589),
    ("Pittsburgh, PA", 40.4406, -79.9959),
    ("Nashville, TN", 36.1627, -86.7816),
    ("Boise, ID", 43.6150, -116.2023),
    ("Spokane, WA", 47.6588, -117.4260),
    ("Reno, NV", 39.5296, -119.8138),
    ("Bakersfield, CA", 35.3733, -119.0187),
    ("Anchorage, AK", 61.2181, -149.9003),
    ("Fairbanks, AK", 64.8378, -147.7164),
    ("Duluth, MN", 46.7867, -92.1005),
    ("Cape Hatteras, NC", 35.2541, -75.5222),
    ("Mount Washington, NH", 44.2705, -71.3033),
]

lats = ",".join(str(c[1]) for c in test_cities)
lons = ",".join(str(c[2]) for c in test_cities)

url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&hourly=wind_speed_10m,wind_gusts_10m,precipitation,rain,snowfall&wind_speed_unit=mph&precipitation_unit=inch&forecast_days=3"
res = requests.get(url).json()

for idx, (name, lat, lon) in enumerate(test_cities):
    hourly = res[idx].get("hourly", {})
    times = hourly.get("time", [])
    winds = hourly.get("wind_speed_10m", [])
    gusts = hourly.get("wind_gusts_10m", [])
    rain = hourly.get("rain", [])
    snow = hourly.get("snowfall", [])
    for t, w, g, r, s in zip(times, winds, gusts, rain, snow):
        # Check if triggers High (w>=35, r>=0.25, s>=1.0), Severe (w>=45, r>=0.5, s>=2.0), or No Travel (w>=55, r>1.0, s>3.0)
        # Or load weight > 30k lb: w>=45 -> No Travel
        # Or load weight > 40k lb: w>=35 -> Severe
        if w >= 30 or r >= 0.25 or s >= 0.5:
            print(f"{name:20s} | {t} | Wind: {w:4.1f} mph (gust {g:4.1f}) | Rain: {r:4.2f} in/hr | Snow: {s:4.2f} in/hr")
