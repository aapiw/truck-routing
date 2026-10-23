import logging
from typing import List, Dict, Any
import requests

logger = logging.getLogger(__name__)

# Lightweight in-memory cache for recent geocoding queries
_GEOCODE_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def search_locations(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """
    Geocodes addresses or cities into coordinates using Photon (Komoot/OSM)
    with fallback to OSM Nominatim.
    """
    q = (query or "").strip()
    if len(q) < 2:
        return []

    cache_key = f"{q.lower()}_{limit}"
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    results = _search_photon(q, limit)
    if not results:
        results = _search_nominatim(q, limit)

    if results:
        _GEOCODE_CACHE[cache_key] = results

    return results


def _search_photon(query: str, limit: int) -> List[Dict[str, Any]]:
    url = "https://photon.komoot.io/api/"
    params = {"q": query, "limit": limit}

    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for feat in data.get("features", []):
            coords = feat.get("geometry", {}).get("coordinates", [])
            props = feat.get("properties", {})
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                name = props.get("name", "")
                city = props.get("city", "")
                state = props.get("state", "")
                country = props.get("country", "")

                parts = [p for p in [name, city, state, country] if p]
                # Remove duplicates while preserving order
                clean_parts = []
                for p in parts:
                    if p not in clean_parts:
                        clean_parts.append(p)
                label = ", ".join(clean_parts) if clean_parts else f"{lat:.3f}, {lon:.3f}"

                items.append({
                    "label": label,
                    "name": name or label,
                    "city": city,
                    "state": state,
                    "country": country,
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                })
        return items
    except Exception as exc:
        logger.warning(f"Photon geocoding error: {exc}")
        return []


def _search_nominatim(query: str, limit: int) -> List[Dict[str, Any]]:
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "TruckWeatherRouter/1.0 (logistics-platform)"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for item in data:
            lat = float(item.get("lat", 0.0))
            lon = float(item.get("lon", 0.0))
            display_name = item.get("display_name", "")
            address = item.get("address", {})

            name = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("county")
                or display_name.split(",")[0]
            )
            state = address.get("state", "")
            country = address.get("country", "")

            items.append({
                "label": display_name,
                "name": name,
                "city": address.get("city", ""),
                "state": state,
                "country": country,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
            })
        return items
    except Exception as exc:
        logger.warning(f"Nominatim geocoding error: {exc}")
        return []
