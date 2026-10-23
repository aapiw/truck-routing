import requests

cities = [
    ("Cheyenne, WY", 41.1399, -104.8202),
    ("Denver, CO", 39.7392, -104.9903),
    ("Salt Lake City, UT", 40.7608, -111.8910),
    ("Great Falls, MT", 47.5053, -111.3008),
    ("Casper, WY", 42.8501, -106.3252),
    ("Amarillo, TX", 35.2220, -101.8313),
    ("Buffalo, NY", 42.8864, -78.8784),
    ("Duluth, MN", 46.7867, -92.1005),
    ("Seattle, WA", 47.6062, -122.3321),
    ("Portland, OR", 45.5152, -122.6784),
    ("Chicago, IL", 41.8781, -87.6298),
    ("Rapid City, SD", 44.0805, -103.2310),
    ("Fargo, ND", 46.8772, -96.7898),
    ("Bismarck, ND", 46.8083, -100.7837),
    ("Helena, MT", 46.5958, -112.0361),
    ("Pocatello, ID", 42.8713, -112.4455),
    ("Flagstaff, AZ", 35.1983, -111.6513),
]

lats = ",".join(str(c[1]) for c in cities)
lons = ",".join(str(c[2]) for c in cities)

url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&hourly=wind_speed_10m,wind_gusts_10m,precipitation,rain,snowfall&wind_speed_unit=mph&precipitation_unit=inch&forecast_days=3"

res = requests.get(url).json()
print(f"{'City':20s} | {'Max Wind':10s} | {'Gusts':10s} | {'Rain':10s} | {'Snow':10s}")
print("-" * 70)
for idx, (name, lat, lon) in enumerate(cities):
    hourly = res[idx].get("hourly", {})
    winds = hourly.get("wind_speed_10m", [])
    gusts = hourly.get("wind_gusts_10m", [])
    rain = hourly.get("rain", [])
    snow = hourly.get("snowfall", [])
    max_w = max(winds) if winds else 0
    max_g = max(gusts) if gusts else 0
    max_r = max(rain) if rain else 0
    max_s = max(snow) if snow else 0
    print(f"{name:20s} | {max_w:4.1f} mph   | {max_g:4.1f} mph   | {max_r:4.2f} in/hr | {max_s:4.2f} in/hr")
