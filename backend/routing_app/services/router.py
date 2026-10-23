import logging
import math
from typing import List, Dict, Any, Tuple, Optional
import requests

logger = logging.getLogger(__name__)

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"


def get_routes(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
) -> List[Dict[str, Any]]:
    lat1, lon1 = origin
    lat2, lon2 = destination

    routes_collected: List[Dict[str, Any]] = []

    # 1. Primary OSRM call with alternatives=3
    url = f"{OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "alternatives": "3",
        "steps": "true",
    }

    try:
        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") == "Ok" and "routes" in data:
            for idx, r in enumerate(data["routes"]):
                parsed = _parse_osrm_route(r, idx)
                if parsed and parsed not in routes_collected:
                    routes_collected.append(parsed)
    except Exception as exc:
        logger.warning(f"Error querying OSRM primary routes: {exc}")

    # 2. If fewer than 3 routes found, generate alternative waypoints (North/South or East/West bypass)
    if len(routes_collected) < 3:
        offsets = [0.45, -0.45, 0.90, -0.90]
        for offset in offsets:
            if len(routes_collected) >= 3:
                break
            waypoint = _calculate_lateral_waypoint(lat1, lon1, lat2, lon2, offset)
            alt_route = _fetch_route_via_waypoint(origin, waypoint, destination, len(routes_collected))
            if alt_route and not _is_duplicate_route(alt_route, routes_collected):
                routes_collected.append(alt_route)

    # 3. Final safety net: if still fewer than 3, synthesize corridor lines
    if len(routes_collected) < 3:
        fallback_routes = _generate_synthetic_routes(origin, destination, len(routes_collected))
        routes_collected.extend(fallback_routes)

    result_routes = routes_collected[:3]
    labels = ["Route A (Fastest / Primary)", "Route B (Northern / Alternate)", "Route C (Southern / Scenic)"]
    for i, r in enumerate(result_routes):
        r["id"] = i
        if not r.get("name") or "Route" not in r["name"]:
            r["name"] = labels[i]

    return result_routes


def _parse_osrm_route(route_obj: Dict[str, Any], index: int) -> Dict[str, Any]:
    legs = route_obj.get("legs", [])
    distance_meters = float(route_obj.get("distance", 0.0))
    duration_seconds = float(route_obj.get("duration", 0.0))

    distance_miles = round(distance_meters * 0.000621371, 1)

    corridor_names = []
    for leg in legs:
        for step in leg.get("steps", []):
            name = step.get("name", "").strip()
            ref = step.get("ref", "").strip()
            highway = ref if ref else name
            if highway and highway not in corridor_names and len(highway) < 25:
                corridor_names.append(highway)

    via_str = f"via {', '.join(corridor_names[:2])}" if corridor_names else "Main Highway"
    route_name = f"Route {chr(65 + index)} ({via_str})"

    raw_coords = route_obj.get("geometry", {}).get("coordinates", [])
    leaflet_coords = [[round(pt[1], 5), round(pt[0], 5)] for pt in raw_coords]

    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    duration_formatted = f"{hours}h {minutes:02d}m" if hours > 0 else f"{minutes}m"

    return {
        "id": index,
        "name": route_name,
        "summary": via_str,
        "distance_miles": distance_miles,
        "duration_seconds": round(duration_seconds, 1),
        "duration_formatted": duration_formatted,
        "coordinates": leaflet_coords,
    }


def _calculate_lateral_waypoint(
    lat1: float, lon1: float, lat2: float, lon2: float, lateral_offset: float
) -> Tuple[float, float]:
    mid_lat = (lat1 + lat2) / 2.0
    mid_lon = (lon1 + lon2) / 2.0

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    dist = math.sqrt(d_lat**2 + d_lon**2) or 1.0

    perp_lat = -d_lon / dist
    perp_lon = d_lat / dist

    way_lat = mid_lat + (perp_lat * lateral_offset)
    way_lon = mid_lon + (perp_lon * lateral_offset)
    return (way_lat, way_lon)


def _fetch_route_via_waypoint(
    origin: Tuple[float, float],
    waypoint: Tuple[float, float],
    destination: Tuple[float, float],
    index: int,
) -> Optional[Dict[str, Any]]:
    lat1, lon1 = origin
    wlat, wlon = waypoint
    lat2, lon2 = destination

    url = f"{OSRM_BASE_URL}/{lon1},{lat1};{wlon},{wlat};{lon2},{lat2}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == "Ok" and data.get("routes"):
            route = _parse_osrm_route(data["routes"][0], index)
            route["name"] = f"Route {chr(65 + index)} (Alternate Bypass)"
            return route
    except Exception as exc:
        logger.warning(f"Error fetching route via waypoint: {exc}")

    return None


def _is_duplicate_route(new_route: Dict[str, Any], existing_routes: List[Dict[str, Any]]) -> bool:
    for existing in existing_routes:
        diff_miles = abs(existing["distance_miles"] - new_route["distance_miles"])
        diff_dur = abs(existing["duration_seconds"] - new_route["duration_seconds"])
        if diff_miles < 5.0 and diff_dur < 300:
            return True
    return False


def _generate_synthetic_routes(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    start_index: int,
) -> List[Dict[str, Any]]:
    lat1, lon1 = origin
    lat2, lon2 = destination
    routes = []

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    approx_miles = math.sqrt((d_lat * 69.0)**2 + (d_lon * 54.0)**2) * 1.25

    offsets = [0.0, 0.4, -0.4]
    for i in range(start_index, 3):
        offset = offsets[i % len(offsets)]
        coords = []
        steps = 40
        for step in range(steps + 1):
            t = step / float(steps)
            arc = 4.0 * t * (1.0 - t) * offset
            lat = lat1 + t * d_lat + (arc * -d_lon / (math.sqrt(d_lat**2 + d_lon**2) or 1))
            lon = lon1 + t * d_lon + (arc * d_lat / (math.sqrt(d_lat**2 + d_lon**2) or 1))
            coords.append([round(lat, 5), round(lon, 5)])

        dur_secs = (approx_miles / 55.0) * 3600.0 * (1.0 + abs(offset) * 0.15)
        hours = int(dur_secs // 3600)
        mins = int((dur_secs % 3600) // 60)

        routes.append({
            "id": i,
            "name": f"Route {chr(65 + i)} (Estimated Corridor)",
            "summary": "Direct Highway Corridor",
            "distance_miles": round(approx_miles * (1.0 + abs(offset) * 0.1), 1),
            "duration_seconds": round(dur_secs, 1),
            "duration_formatted": f"{hours}h {mins:02d}m",
            "coordinates": coords,
        })

    return routes
