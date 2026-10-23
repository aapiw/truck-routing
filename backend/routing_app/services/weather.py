import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes
WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_weather_description(code: int) -> str:
    return WMO_CODE_MAP.get(int(code), "Overcast / Variable")


def fetch_weather_for_checkpoints(checkpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fetches hourly weather from Open-Meteo for each checkpoint at its estimated arrival time (ETA).
    Batches API requests up to 40 checkpoints per HTTP call.
    """
    if not checkpoints:
        return []

    results = []
    chunk_size = 35

    for i in range(0, len(checkpoints), chunk_size):
        chunk = checkpoints[i : i + chunk_size]
        chunk_results = _fetch_batch_chunk(chunk)
        results.extend(chunk_results)

    return results


def _fetch_batch_chunk(chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lats = ",".join(str(c["lat"]) for c in chunk)
    lons = ",".join(str(c["lon"]) for c in chunk)

    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": "temperature_2m,precipitation,rain,snowfall,wind_speed_10m,wind_gusts_10m,weather_code",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "temperature_unit": "fahrenheit",
        "forecast_days": 7,
        "timezone": "UTC",
    }

    try:
        resp = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # If single location was queried, Open-Meteo returns a single dict instead of a list
        if isinstance(data, dict):
            forecast_list = [data]
        else:
            forecast_list = data

        enriched_chunk = []
        for idx, cp in enumerate(chunk):
            if idx < len(forecast_list):
                forecast = forecast_list[idx]
                weather_at_eta = _extract_weather_at_time(forecast, cp["eta_iso"])
            else:
                weather_at_eta = _generate_fallback_weather(cp["lat"], cp["lon"])

            enriched_cp = dict(cp)
            enriched_cp["weather"] = weather_at_eta
            enriched_chunk.append(enriched_cp)

        return enriched_chunk

    except Exception as exc:
        logger.warning(f"Open-Meteo API query error: {exc}. Using fallback meteorological model.")
        return [_attach_fallback_weather(cp) for cp in chunk]


def _extract_weather_at_time(forecast_data: Dict[str, Any], eta_iso: str) -> Dict[str, Any]:
    hourly = forecast_data.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        return _generate_fallback_weather(0.0, 0.0)

    try:
        eta_dt = date_parser.parse(eta_iso)
        if eta_dt.tzinfo is None:
            eta_dt = eta_dt.replace(tzinfo=timezone.utc)
        eta_epoch = eta_dt.timestamp()

        # Find closest hourly index
        best_idx = 0
        min_diff = float("inf")

        for idx, t_str in enumerate(times):
            # Open-Meteo returns '2026-10-20T14:00'
            t_dt = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
            diff = abs(t_dt.timestamp() - eta_epoch)
            if diff < min_diff:
                min_diff = diff
                best_idx = idx

        temp_f = float(hourly.get("temperature_2m", [65.0])[best_idx] or 65.0)
        wind_speed = float(hourly.get("wind_speed_10m", [10.0])[best_idx] or 0.0)
        wind_gusts = float(hourly.get("wind_gusts_10m", [wind_speed * 1.3])[best_idx] or wind_speed)
        rain_rate = float(hourly.get("rain", [0.0])[best_idx] or 0.0)
        snow_rate = float(hourly.get("snowfall", [0.0])[best_idx] or 0.0)
        precip = float(hourly.get("precipitation", [0.0])[best_idx] or 0.0)
        weather_code = int(hourly.get("weather_code", [0])[best_idx] or 0)

        return {
            "temperature_f": round(temp_f, 1),
            "wind_speed_mph": round(wind_speed, 1),
            "wind_gusts_mph": round(wind_gusts, 1),
            "rain_in_per_hr": round(rain_rate, 3),
            "snow_in_per_hr": round(snow_rate, 2),
            "precip_in": round(precip, 3),
            "weather_code": weather_code,
            "description": get_weather_description(weather_code),
        }

    except Exception as exc:
        logger.warning(f"Error parsing hourly forecast at {eta_iso}: {exc}")
        return _generate_fallback_weather(0.0, 0.0)


def _generate_fallback_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Generates standard baseline weather when external API is unreachable."""
    return {
        "temperature_f": 62.0,
        "wind_speed_mph": 12.0,
        "wind_gusts_mph": 16.0,
        "rain_in_per_hr": 0.0,
        "snow_in_per_hr": 0.0,
        "precip_in": 0.0,
        "weather_code": 1,
        "description": "Mainly clear",
    }


def generate_demo_weather_for_risk(risk_level: str, checkpoint_index: int, total_checkpoints: int) -> Dict[str, Any]:
    """
    Generates deterministic demo weather data for a specific risk level.
    Used for demonstration when real weather doesn't show the desired risk tier.
    """
    # Distribute risk across checkpoints for variety
    position = checkpoint_index / max(1, total_checkpoints - 1)
    
    if risk_level == "LOW":
        return {
            "temperature_f": 65.0,
            "wind_speed_mph": 12.0,
            "wind_gusts_mph": 16.0,
            "rain_in_per_hr": 0.0,
            "snow_in_per_hr": 0.0,
            "precip_in": 0.0,
            "weather_code": 0,
            "description": "Clear sky",
        }
    elif risk_level == "MODERATE":
        # Wind 25-34 mph, or rain 0.10-0.25, or snow 0.5-1.0
        if position < 0.5:
            return {
                "temperature_f": 52.0,
                "wind_speed_mph": 28.0,
                "wind_gusts_mph": 35.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
                "precip_in": 0.0,
                "weather_code": 1,
                "description": "Mainly clear",
            }
        else:
            return {
                "temperature_f": 48.0,
                "wind_speed_mph": 15.0,
                "wind_gusts_mph": 20.0,
                "rain_in_per_hr": 0.15,
                "snow_in_per_hr": 0.0,
                "precip_in": 0.15,
                "weather_code": 61,
                "description": "Slight rain",
            }
    elif risk_level == "HIGH":
        # Wind 35-44 mph, or rain 0.25-0.50, or snow 1.0-2.0
        if position < 0.33:
            return {
                "temperature_f": 38.0,
                "wind_speed_mph": 38.0,
                "wind_gusts_mph": 48.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
                "precip_in": 0.0,
                "weather_code": 3,
                "description": "Overcast",
            }
        elif position < 0.66:
            return {
                "temperature_f": 42.0,
                "wind_speed_mph": 18.0,
                "wind_gusts_mph": 25.0,
                "rain_in_per_hr": 0.35,
                "snow_in_per_hr": 0.0,
                "precip_in": 0.35,
                "weather_code": 63,
                "description": "Moderate rain",
            }
        else:
            return {
                "temperature_f": 28.0,
                "wind_speed_mph": 22.0,
                "wind_gusts_mph": 30.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 1.5,
                "precip_in": 1.5,
                "weather_code": 73,
                "description": "Moderate snow fall",
            }
    elif risk_level == "SEVERE":
        # Wind 45-54 mph, or rain 0.50-1.00, or snow 2.0-3.0
        if position < 0.5:
            return {
                "temperature_f": 35.0,
                "wind_speed_mph": 48.0,
                "wind_gusts_mph": 58.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
                "precip_in": 0.0,
                "weather_code": 3,
                "description": "Overcast",
            }
        else:
            return {
                "temperature_f": 30.0,
                "wind_speed_mph": 25.0,
                "wind_gusts_mph": 35.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 2.5,
                "precip_in": 2.5,
                "weather_code": 75,
                "description": "Heavy snow fall",
            }
    elif risk_level == "NO_TRAVEL":
        # Wind >= 55 mph, or rain > 1.00, or snow > 3.0
        if position < 0.5:
            return {
                "temperature_f": 45.0,
                "wind_speed_mph": 60.0,
                "wind_gusts_mph": 75.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 0.0,
                "precip_in": 0.0,
                "weather_code": 95,
                "description": "Thunderstorm",
            }
        else:
            return {
                "temperature_f": 25.0,
                "wind_speed_mph": 35.0,
                "wind_gusts_mph": 45.0,
                "rain_in_per_hr": 0.0,
                "snow_in_per_hr": 4.0,
                "precip_in": 4.0,
                "weather_code": 75,
                "description": "Heavy snow fall",
            }
    return _generate_fallback_weather(lat, lon)


def _attach_fallback_weather(cp: Dict[str, Any]) -> Dict[str, Any]:
    cp_copy = dict(cp)
    cp_copy["weather"] = _generate_fallback_weather(cp["lat"], cp["lon"])
    return cp_copy
