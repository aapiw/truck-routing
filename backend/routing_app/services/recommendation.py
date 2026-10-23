from typing import List, Dict, Any
import math
from dataclasses import dataclass
from routing_app.services.risk_engine import RiskLevel, RISK_SEVERITY_ORDER


@dataclass
class FleetPolicy:
    """Configurable fleet routing policy for risk/duration tradeoffs."""
    # Hierarchical weights (100 ≫ 10 ≫ 1 ≫ 0.1 ≫ 0.001 ensures safety-first lexicographic behavior)
    weight_severe_no_travel: float = 100.0
    weight_high: float = 10.0
    weight_moderate: float = 1.0
    weight_avg_risk: float = 0.1
    weight_duration_seconds: float = 0.001
    # Load amplification exponent for wind risk
    wind_load_exponent: float = 1.5
    # Reference load for normalization (40,000 lb = standard loaded)
    reference_load_lbs: float = 40000.0

    @classmethod
    def conservative(cls) -> "FleetPolicy":
        """Ultra-conservative: heavy penalty on any elevated risk."""
        return cls(
            weight_severe_no_travel=1000.0,
            weight_high=100.0,
            weight_moderate=10.0,
            weight_avg_risk=1.0,
            weight_duration_seconds=0.0001,
        )

    @classmethod
    def balanced(cls) -> "FleetPolicy":
        """Balanced: allows moderate risk for significant time savings."""
        return cls(
            weight_severe_no_travel=100.0,
            weight_high=15.0,
            weight_moderate=2.0,
            weight_avg_risk=0.2,
            weight_duration_seconds=0.002,
        )

    @classmethod
    def expedited(cls) -> "FleetPolicy":
        """Time-critical: minimizes duration while avoiding NO_TRAVEL."""
        return cls(
            weight_severe_no_travel=500.0,
            weight_high=5.0,
            weight_moderate=1.0,
            weight_avg_risk=0.05,
            weight_duration_seconds=0.01,
        )


DEFAULT_POLICY = FleetPolicy()


def _cargo_adjusted_wind_penalty(max_wind_mph: float, load_weight_lbs: float, policy: FleetPolicy) -> float:
    """Exponential wind penalty scaled by load weight."""
    if max_wind_mph < 25.0:
        return 0.0
    load_factor = max(1.0, load_weight_lbs / policy.reference_load_lbs)
    return max_wind_mph * (load_factor ** policy.wind_load_exponent)


def _composite_score(route: Dict[str, Any], policy: FleetPolicy, load_weight_lbs: float) -> float:
    """Weighted composite score with cargo-aware wind amplification."""
    stats = route.get("risk_summary", {})
    severe_plus_no_travel = stats.get("severe_miles", 0.0) + stats.get("no_travel_miles", 0.0)
    high_miles = stats.get("high_miles", 0.0)
    moderate_miles = stats.get("moderate_miles", 0.0)
    avg_risk = stats.get("average_risk_score", 1.0)
    max_wind = stats.get("max_wind_mph", 0.0)
    duration = route.get("duration_seconds", 0.0)

    wind_penalty = _cargo_adjusted_wind_penalty(max_wind, load_weight_lbs, policy)

    return (
        policy.weight_severe_no_travel * severe_plus_no_travel +
        policy.weight_high * high_miles +
        policy.weight_moderate * moderate_miles +
        policy.weight_avg_risk * avg_risk +
        policy.weight_duration_seconds * duration +
        0.01 * wind_penalty
    )


def rank_and_recommend_routes(
    routes_with_analysis: List[Dict[str, Any]],
    policy: FleetPolicy = None,
    load_weight_lbs: float = 35000.0,
) -> List[Dict[str, Any]]:
    """
    Ranks routes according to configurable safety-first criteria.
    Default policy maintains original lexicographic hierarchy via hierarchical weights.
    """
    if not routes_with_analysis:
        return []

    policy = policy or DEFAULT_POLICY

    # Sort by composite score
    def sort_key(r: Dict[str, Any]):
        return _composite_score(r, policy, load_weight_lbs)

    ranked = sorted(routes_with_analysis, key=sort_key)

    # Annotate rankings and generate recommendation explanations
    for rank_idx, r in enumerate(ranked):
        r["rank"] = rank_idx + 1
        r["is_recommended"] = (rank_idx == 0)

        stats = r.get("risk_summary", {})
        has_no_travel = stats.get("no_travel_miles", 0.0) > 0
        severe_miles = stats.get("severe_miles", 0.0) + stats.get("no_travel_miles", 0.0)
        high_miles = stats.get("high_miles", 0.0)
        avg_score = stats.get("average_risk_score", 1.0)

        if rank_idx == 0:
            if severe_miles == 0 and high_miles == 0:
                reason = "Safest corridor: 0 severe/high risk miles with optimal weather conditions throughout."
            elif severe_miles == 0:
                reason = f"Recommended: avoids all severe weather zones ({high_miles:.1f} mi high risk, lowest aggregate hazard)."
            else:
                reason = f"Best viable option: minimizes severe weather exposure to {severe_miles:.1f} miles."
        else:
            best_stats = ranked[0].get("risk_summary", {})
            diff_severe = severe_miles - (best_stats.get("severe_miles", 0.0) + best_stats.get("no_travel_miles", 0.0))

            if has_no_travel:
                reason = f"Contains {stats.get('no_travel_miles', 0):.1f} miles with No-Travel conditions (high wind/precip)."
            elif diff_severe > 0:
                reason = f"Deprioritized: exposes driver to {diff_severe:.1f} more severe weather miles than the recommended route."
            elif high_miles > best_stats.get("high_miles", 0.0):
                reason = f"Higher risk exposure: {high_miles:.1f} miles in High-risk conditions."
            else:
                diff_mins = int((r.get("duration_seconds", 0) - ranked[0].get("duration_seconds", 0)) / 60)
                reason = f"Similar risk profile but adds {diff_mins} minutes travel time."

        r["recommendation_reason"] = reason

    return ranked
