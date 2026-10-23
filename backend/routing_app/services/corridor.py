import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
import requests
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


def generate_corridor_weather_grid(
    routes: List[Dict[str, Any]],
    departure_time: datetime,
    max_hours: int = 48,
    grid_density: int = 45,
) -> Dict[str, Any]:
    """
    Generates a spatial corridor grid enclosing the routes and extracts 0-48h hourly forecast data.
    Supplies the dynamic timeline heatmap slider on the map.
    """
    all_coords = []
    for r in routes:
        all_coords.extend(r.get("coordinates", []))

    if not all_coords:
        return {"hours": list(range(max_hours + 1)), "timestamps": [], "grid": []}

    # Extract bounding box with padding
    lats = [c[0] for c in all_coords]
    lons = [c[1] for c in all_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Pad corridor by ~0.3 degrees (~20 miles)
    pad = 0.3
    min_lat -= pad
    max_lat += pad
    min_lon -= pad
    max_lon += pad

    # Sample representative grid points along the corridor envelope
    grid_coords: List[Tuple[float, float]] = []

    # First, sample evenly along route paths (highest relevance)
    step = max(1, len(all_coords) // 30)
    for i in range(0, len(all_coords), step):
        c = all_coords[i]
        grid_coords.append((round(c[0], 4), round(c[1], 4)))

    # Second, add a few lateral perimeter points for spatial contouring
    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    rows, cols = 4, 5
    for r in range(rows):
        for c in range(cols):
            glat = round(min_lat + (r / max(1, rows - 1)) * lat_span, 4)
            glon = round(min_lon + (c / max(1, cols - 1)) * lon_span, 4)
            # Only include if within reasonable distance of at least one route point
            if any(abs(glat - pt[0]) < 0.8 and abs(glon - pt[1]) < 0.8 for pt in grid_coords[:20]):
                grid_coords.append((glat, glon))

    # Deduplicate and cap
    unique_points = []
    seen = set()
    for pt in grid_coords:
        key = (round(pt[0], 2), round(pt[1], 2))
        if key not in seen:
            seen.add(key)
            unique_points.append(pt)
        if len(unique_points) >= grid_density:
            break

    # Build hourly timestamps
    base_time = departure_time.replace(minute=0, second=0, microsecond=0)
    timestamps = [(base_time + timedelta(hours=h)).isoformat() for h in range(max_hours + 1)]

    # Fetch weather for unique points
    grid_data = _fetch_corridor_forecast(unique_points, base_time, max_hours)

    return {
        "hours": list(range(max_hours + 1)),
        "timestamps": timestamps,
        "grid": grid_data,
    }


def _fetch_corridor_forecast(
    points: List[Tuple[float, float]],
    base_time: datetime,
    max_hours: int,
) -> List[Dict[str, Any]]:
    if not points:
        return []

    lats_str = ",".join(str(p[0]) for p in points)
    lons_str = ",".join(str(p[1]) for p in points)

    params = {
        "latitude": lats_str,
        "longitude": lons_str,
        "hourly": "temperature_2m,precipitation,rain,snowfall,wind_speed_10m",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "temperature_unit": "fahrenheit",
        "forecast_days": 3,
        "timezone": "UTC",
    }

    try:
        resp = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        forecast_list = [data] if isinstance(data, dict) else data

        grid_output = []
        for idx, pt in enumerate(points):
            pt_dict: Dict[str, Any] = {
                "lat": pt[0],
                "lon": pt[1],
                "hourly": [],
            }

            forecast = forecast_list[idx] if idx < len(forecast_list) else {}
            hourly = forecast.get("hourly", {})
            times = hourly.get("time", [])

            start_idx = 0
            if times:
                base_iso = base_time.strftime("%Y-%m-%dT%H:00")
                for t_idx, t in enumerate(times):
                    if t >= base_iso:
                        start_idx = t_idx
                        break

            winds = hourly.get("wind_speed_10m", [])
            rains = hourly.get("rain", [])
            snows = hourly.get("snowfall", [])
            temps = hourly.get("temperature_2m", [])

            for h in range(max_hours + 1):
                cur_idx = start_idx + h
                w_val = float(winds[cur_idx] if cur_idx < len(winds) and winds[cur_idx] is not None else 8.0)
                r_val = float(rains[cur_idx] if cur_idx < len(rains) and rains[cur_idx] is not None else 0.0)
                s_val = float(snows[cur_idx] if cur_idx < len(snows) and snows[cur_idx] is not None else 0.0)
                t_val = float(temps[cur_idx] if cur_idx < len(temps) and temps[cur_idx] is not None else 65.0)

                # Normalized risk score for heatmap intensity (0.0 to 1.0)
                risk_intensity = min(1.0, max(0.05, (w_val / 60.0) * 0.4 + (r_val / 0.8) * 0.3 + (s_val / 2.5) * 0.3))

                pt_dict["hourly"].append({
                    "hour": h,
                    "wind_mph": round(w_val, 1),
                    "rain_in": round(r_val, 3),
                    "snow_in": round(s_val, 2),
                    "temp_f": round(t_val, 1),
                    "risk_intensity": round(risk_intensity, 3),
                })

            grid_output.append(pt_dict)

        return grid_output

    except Exception as exc:
        logger.warning(f"Error fetching corridor grid forecast: {exc}")
        # Synthetic baseline fallback
        return [
            {
                "lat": p[0],
                "lon": p[1],
                "hourly": [
                    {
                        "hour": h,
                        "wind_mph": 12.0,
                        "rain_in": 0.0,
                        "snow_in": 0.0,
                        "temp_f": 65.0,
                        "risk_intensity": 0.1,
                    }
                    for h in range(max_hours + 1)
                ],
            }
            for p in points
        ]
