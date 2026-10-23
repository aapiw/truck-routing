import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in miles."""
    r = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def interpolate_coordinate(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    fraction: float,
) -> Tuple[float, float]:
    """Linearly interpolates between two [lat, lon] coordinates."""
    lat = p1[0] + (p2[0] - p1[0]) * fraction
    lon = p1[1] + (p2[1] - p1[1]) * fraction
    return (lat, lon)


def sample_route_checkpoints(
    coordinates: List[List[float]],
    total_distance_miles: float,
    total_duration_seconds: float,
    departure_time: datetime,
    interval_miles: int = 25,
) -> List[Dict[str, Any]]:
    """
    Samples checkpoints along a route polyline at specified distance intervals (10, 25, 50 miles).
    Calculates truck ETA and segment mileage attribution for each checkpoint.
    """
    if not coordinates or len(coordinates) < 2:
        return []

    # Calculate cumulative distances along all polyline vertices
    cum_distances = [0.0]
    total_polyline_dist = 0.0

    for i in range(len(coordinates) - 1):
        p1 = coordinates[i]
        p2 = coordinates[i + 1]
        dist = haversine_miles(p1[0], p1[1], p2[0], p2[1])
        total_polyline_dist += dist
        cum_distances.append(total_polyline_dist)

    # Use the official route total_distance_miles for scaling if provided and non-zero
    scale_factor = 1.0
    if total_polyline_dist > 0 and total_distance_miles > 0:
        scale_factor = total_distance_miles / total_polyline_dist

    effective_total_miles = total_distance_miles if total_distance_miles > 0 else total_polyline_dist

    # Determine sample targets: 0, interval, 2*interval, ..., end
    interval = max(5, int(interval_miles))
    target_distances: List[float] = [0.0]
    curr = float(interval)
    while curr < effective_total_miles - (interval * 0.25):  # avoid tiny redundant stub at end
        target_distances.append(curr)
        curr += float(interval)
    if target_distances[-1] < effective_total_miles:
        target_distances.append(effective_total_miles)

    checkpoints: List[Dict[str, Any]] = []
    num_targets = len(target_distances)

    for idx, target_dist in enumerate(target_distances):
        # Map target_dist back to unscaled polyline distance
        unscaled_target = target_dist / scale_factor if scale_factor > 0 else target_dist

        # Locate vertex segment
        lat, lon = coordinates[-1][0], coordinates[-1][1]
        for i in range(len(cum_distances) - 1):
            d_start = cum_distances[i]
            d_end = cum_distances[i + 1]
            if d_start <= unscaled_target <= d_end:
                seg_len = d_end - d_start
                frac = (unscaled_target - d_start) / seg_len if seg_len > 0 else 0.0
                lat, lon = interpolate_coordinate(
                    (coordinates[i][0], coordinates[i][1]),
                    (coordinates[i + 1][0], coordinates[i + 1][1]),
                    frac,
                )
                break

        # Calculate estimated arrival time
        time_fraction = target_dist / effective_total_miles if effective_total_miles > 0 else 0.0
        elapsed_seconds = time_fraction * total_duration_seconds
        eta = departure_time + timedelta(seconds=elapsed_seconds)

        # Calculate segment miles attributed to this checkpoint
        if num_targets == 1:
            segment_miles = effective_total_miles
        elif idx == 0:
            segment_miles = (target_distances[1] - target_distances[0]) / 2.0
        elif idx == num_targets - 1:
            segment_miles = (target_distances[-1] - target_distances[-2]) / 2.0
        else:
            prev_mid = (target_distances[idx] + target_distances[idx - 1]) / 2.0
            next_mid = (target_distances[idx + 1] + target_distances[idx]) / 2.0
            segment_miles = next_mid - prev_mid

        checkpoints.append({
            "index": idx,
            "is_origin": idx == 0,
            "is_destination": idx == (num_targets - 1),
            "distance_from_origin_miles": round(target_dist, 1),
            "segment_miles": round(segment_miles, 2),
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "eta_iso": eta.isoformat(),
            "eta_formatted": eta.strftime("%b %d, %H:%M"),
            "eta_epoch": int(eta.timestamp()),
            "elapsed_seconds": int(elapsed_seconds),
        })

    return checkpoints
