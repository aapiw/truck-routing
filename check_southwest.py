import requests

url = "https://api.open-meteo.com/v1/forecast?latitude=35.1983,33.4484,35.0844,36.1699&longitude=-111.6513,-112.0740,-106.6504,-115.1398&hourly=wind_speed_10m,wind_gusts_10m,precipitation,rain,snowfall&wind_speed_unit=mph&precipitation_unit=inch&forecast_days=3"
res = requests.get(url).json()

names = ["Flagstaff, AZ", "Phoenix, AZ", "Albuquerque, NM", "Las Vegas, NV"]
for idx, name in enumerate(names):
    hourly = res[idx].get("hourly", {})
    times = hourly.get("time", [])
    rain = hourly.get("rain", [])
    winds = hourly.get("wind_speed_10m", [])
    print(f"\n--- {name} ---")
    found = 0
    for t, r, w in zip(times, rain, winds):
        if r > 0.25 or w >= 25:
            found += 1
            print(f"Time: {t} | Rain: {r:.2f} in/hr | Wind: {w:.1f} mph")
    if found == 0:
        print("No severe/high conditions detected in next 72h.")
