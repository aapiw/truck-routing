import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from dateutil import parser as date_parser

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from routing_app.services.geocoding import search_locations
from routing_app.services.router import get_routes
from routing_app.services.sampling import sample_route_checkpoints
from routing_app.services.weather import fetch_weather_for_checkpoints, generate_demo_weather_for_risk
from routing_app.services.risk_engine import evaluate_checkpoint_risk, RISK_COLORS, RiskLevel
from routing_app.services.recommendation import rank_and_recommend_routes, FleetPolicy
from routing_app.services.corridor import generate_corridor_weather_grid

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})


class GeocodeView(APIView):
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 6))
        results = search_locations(query, limit=limit)
        return Response(results)


class AnalyzeRoutesView(APIView):
    """
    Main endpoint:
    - Generates 3 route options
    - Samples checkpoints every 10 / 25 / 50 miles
    - Fetches weather at truck ETA
    - Applies risk & load rules
    - Ranks and recommends the optimal route
    - Attaches 0-48h corridor heatmap grid
    """

    def post(self, request):
        data = request.data or {}

        origin_data = data.get("origin")
        dest_data = data.get("destination")

        if not origin_data or not dest_data:
            return Response(
                {"error": "Both 'origin' and 'destination' objects with lat and lon are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            orig_lat = float(origin_data.get("lat"))
            orig_lon = float(origin_data.get("lon"))
            dest_lat = float(dest_data.get("lat"))
            dest_lon = float(dest_data.get("lon"))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid coordinates in origin or destination."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse departure time
        dep_str = data.get("departure_time")
        if dep_str:
            try:
                departure_time = date_parser.parse(dep_str)
                if departure_time.tzinfo is None:
                    departure_time = departure_time.replace(tzinfo=timezone.utc)
            except Exception:
                departure_time = datetime.now(timezone.utc)
        else:
            departure_time = datetime.now(timezone.utc)

        # Parse load weight
        try:
            load_weight = float(data.get("load_weight", 35000.0))
        except (ValueError, TypeError):
            load_weight = 35000.0

# Parse sampling interval (10, 25, 50 miles)
        try:
            sampling_interval = int(data.get("sampling_interval_miles", 25))
            if sampling_interval not in (10, 25, 50):
                sampling_interval = 25
        except (ValueError, TypeError):
            sampling_interval = 25

        # Parse demo mode - if set, simulates specific risk levels per route
        demo_mode = data.get("demo_mode", None)

        # 1. Generate 3 routes
        routes = get_routes((orig_lat, orig_lon), (dest_lat, dest_lon))
        if not routes:
            return Response(
                {"error": "Failed to generate routing options between coordinates."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        analyzed_routes: List[Dict[str, Any]] = []

# 2. Process each route
        risk_levels = ["LOW", "MODERATE", "HIGH", "SEVERE", "NO_TRAVEL"]
        for idx, r in enumerate(routes):
            raw_checkpoints = sample_route_checkpoints(
                coordinates=r.get("coordinates", []),
                total_distance_miles=r.get("distance_miles", 0.0),
                total_duration_seconds=r.get("duration_seconds", 0.0),
                departure_time=departure_time,
                interval_miles=sampling_interval,
            )

            # Enrich checkpoints with weather at ETA
            if demo_mode:
                # Use demo weather: assign a risk level to each route
                risk_for_route = risk_levels[min(idx, len(risk_levels) - 1)]
                enriched_checkpoints = []
                for cp_idx, cp in enumerate(raw_checkpoints):
                    demo_weather = generate_demo_weather_for_risk(
                        risk_for_route, cp_idx, len(raw_checkpoints)
                    )
                    enriched_cp = dict(cp)
                    enriched_cp["weather"] = demo_weather
                    enriched_checkpoints.append(enriched_cp)
                r["demo_risk_level"] = risk_for_route
            else:
                enriched_checkpoints = fetch_weather_for_checkpoints(raw_checkpoints)

            # Evaluate risk at each checkpoint
            evaluated_checkpoints = []
            low_miles = 0.0
            mod_miles = 0.0
            high_miles = 0.0
            severe_miles = 0.0
            no_travel_miles = 0.0
            total_weighted_risk = 0.0
            max_wind = 0.0
            max_rain = 0.0
            max_snow = 0.0
            load_alerts = []

            for cp in enriched_checkpoints:
                w = cp.get("weather", {})
                w_wind = float(w.get("wind_speed_mph", 0.0))
                w_rain = float(w.get("rain_in_per_hr", 0.0))
                w_snow = float(w.get("snow_in_per_hr", 0.0))

                max_wind = max(max_wind, w_wind)
                max_rain = max(max_rain, w_rain)
                max_snow = max(max_snow, w_snow)

                risk_eval = evaluate_checkpoint_risk(
                    wind_mph=w_wind,
                    rain_in_per_hr=w_rain,
                    snow_in_per_hr=w_snow,
                    load_weight_lbs=load_weight,
                )

                cp_dict = dict(cp)
                cp_dict["risk"] = risk_eval
                evaluated_checkpoints.append(cp_dict)

                # Aggregate mileages
                seg_mi = float(cp.get("segment_miles", 0.0))
                lvl = risk_eval["overall_risk"]

                if lvl == RiskLevel.NO_TRAVEL.value:
                    no_travel_miles += seg_mi
                elif lvl == RiskLevel.SEVERE.value:
                    severe_miles += seg_mi
                elif lvl == RiskLevel.HIGH.value:
                    high_miles += seg_mi
                elif lvl == RiskLevel.MODERATE.value:
                    mod_miles += seg_mi
                else:
                    low_miles += seg_mi

                total_weighted_risk += risk_eval["risk_score"] * seg_mi

                if risk_eval.get("load_rule_note"):
                    load_alerts.append({
                        "checkpoint_index": cp["index"],
                        "distance_miles": cp["distance_from_origin_miles"],
                        "eta": cp["eta_formatted"],
                        "note": risk_eval["load_rule_note"],
                    })

            tot_dist = r.get("distance_miles", 0.0) or 1.0
            avg_risk_score = round(total_weighted_risk / tot_dist, 2)

            risk_summary = {
                "low_miles": round(low_miles, 1),
                "moderate_miles": round(mod_miles, 1),
                "high_miles": round(high_miles, 1),
                "severe_miles": round(severe_miles, 1),
                "no_travel_miles": round(no_travel_miles, 1),
                "total_miles": round(tot_dist, 1),
                "average_risk_score": avg_risk_score,
                "max_wind_mph": round(max_wind, 1),
                "max_rain_in_per_hr": round(max_rain, 3),
                "max_snow_in_per_hr": round(max_snow, 2),
                "load_alerts": load_alerts,
            }

            # Generate color-coded polyline segments for interactive map rendering
            colored_segments = _build_colored_route_segments(r.get("coordinates", []), evaluated_checkpoints)

            analyzed_route = dict(r)
            analyzed_route["checkpoints"] = evaluated_checkpoints
            analyzed_route["risk_summary"] = risk_summary
            analyzed_route["colored_segments"] = colored_segments
            analyzed_routes.append(analyzed_route)

# 3. Rank and recommend
        # Parse fleet policy from request (default: standard)
        policy_name = data.get("fleet_policy", "standard")
        if policy_name == "conservative":
            policy = FleetPolicy.conservative()
        elif policy_name == "expedited":
            policy = FleetPolicy.expedited()
        elif policy_name == "balanced":
            policy = FleetPolicy.balanced()
        else:
            policy = FleetPolicy()

        ranked_routes = rank_and_recommend_routes(analyzed_routes, policy=policy, load_weight_lbs=load_weight)
        recommended_route = next((r for r in ranked_routes if r.get("is_recommended")), ranked_routes[0])

        # 4. Generate 0-48h corridor heatmap grid
        corridor_grid = generate_corridor_weather_grid(ranked_routes, departure_time, max_hours=48)

        response_payload = {
            "origin": origin_data,
            "destination": dest_data,
            "departure_time": departure_time.isoformat(),
            "load_weight": load_weight,
            "sampling_interval_miles": sampling_interval,
            "recommended_route_id": recommended_route["id"],
            "routes": ranked_routes,
            "corridor_grid": corridor_grid,
        }

        return Response(response_payload)


def _build_colored_route_segments(
    coordinates: List[List[float]],
    checkpoints: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Slices the route polyline into contiguous colored segments matching the checkpoint risks.
    """
    if not coordinates:
        return []
    if not checkpoints or len(checkpoints) == 1:
        color = checkpoints[0]["risk"]["color"] if checkpoints else "#10b981"
        return [{"coordinates": coordinates, "color": color, "risk_level": "LOW"}]

    segments = []
    num_cps = len(checkpoints)
    total_pts = len(coordinates)

    for i in range(num_cps):
        # Determine coordinate slice for checkpoint i
        idx_start = int((i / num_cps) * total_pts)
        idx_end = int(((i + 1) / num_cps) * total_pts)
        if i == num_cps - 1:
            idx_end = total_pts

        seg_coords = coordinates[idx_start : max(idx_start + 2, idx_end + 1)]
        if seg_coords:
            segments.append({
                "coordinates": seg_coords,
                "color": checkpoints[i]["risk"]["color"],
                "risk_level": checkpoints[i]["risk"]["overall_risk"],
            })

    return segments
