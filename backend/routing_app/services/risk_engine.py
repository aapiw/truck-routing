from enum import Enum
from typing import Dict, Any, List, Optional


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"
    NO_TRAVEL = "NO_TRAVEL"


RISK_SEVERITY_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MODERATE: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.SEVERE: 4,
    RiskLevel.NO_TRAVEL: 5,
}

RISK_COLORS = {
    RiskLevel.LOW: "#10b981",
    RiskLevel.MODERATE: "#f59e0b",
    RiskLevel.HIGH: "#f97316",
    RiskLevel.SEVERE: "#ef4444",
    RiskLevel.NO_TRAVEL: "#7f1d1d",
}


def classify_wind(speed_mph: float, load_weight_lbs: float) -> Dict[str, Any]:
    speed = max(0.0, float(speed_mph))
    weight = max(0.0, float(load_weight_lbs))
    rule_note = None

    if speed >= 55.0:
        base_level = RiskLevel.NO_TRAVEL
        final_level = RiskLevel.NO_TRAVEL
        rule_note = "Wind >= 55 mph requires No Travel for any load"
    elif 45.0 <= speed < 55.0:
        base_level = RiskLevel.SEVERE
        if weight > 30000.0:
            final_level = RiskLevel.NO_TRAVEL
            rule_note = f"Wind {speed:.1f} mph + load {weight:,.0f} lb (> 30,000 lb) escalated to No Travel"
        else:
            final_level = RiskLevel.SEVERE
    elif 35.0 <= speed < 45.0:
        base_level = RiskLevel.HIGH
        if weight > 40000.0:
            final_level = RiskLevel.SEVERE
            rule_note = f"Wind {speed:.1f} mph + load {weight:,.0f} lb (> 40,000 lb) escalated to Severe"
        else:
            final_level = RiskLevel.HIGH
    elif 25.0 <= speed < 35.0:
        base_level = RiskLevel.MODERATE
        final_level = RiskLevel.MODERATE
    else:
        base_level = RiskLevel.LOW
        final_level = RiskLevel.LOW

    return {
        "level": final_level.value,
        "base_level": base_level.value,
        "value": round(speed, 1),
        "unit": "mph",
        "rule_note": rule_note,
    }


def classify_rain(precip_rate_in_per_hr: float) -> Dict[str, Any]:
    rate = max(0.0, float(precip_rate_in_per_hr))

    if rate > 1.00:
        level = RiskLevel.NO_TRAVEL
    elif rate >= 0.50:
        level = RiskLevel.SEVERE
    elif rate >= 0.25:
        level = RiskLevel.HIGH
    elif rate >= 0.10:
        level = RiskLevel.MODERATE
    else:
        level = RiskLevel.LOW

    return {
        "level": level.value,
        "value": round(rate, 3),
        "unit": "in/hr",
    }


def classify_snow(snow_rate_in_per_hr: float) -> Dict[str, Any]:
    rate = max(0.0, float(snow_rate_in_per_hr))

    if rate > 3.0:
        level = RiskLevel.NO_TRAVEL
    elif rate >= 2.0:
        level = RiskLevel.SEVERE
    elif rate >= 1.0:
        level = RiskLevel.HIGH
    elif rate >= 0.5:
        level = RiskLevel.MODERATE
    else:
        level = RiskLevel.LOW

    return {
        "level": level.value,
        "value": round(rate, 2),
        "unit": "in/hr",
    }


def evaluate_checkpoint_risk(
    wind_mph: float,
    rain_in_per_hr: float,
    snow_in_per_hr: float,
    load_weight_lbs: float,
) -> Dict[str, Any]:
    wind_res = classify_wind(wind_mph, load_weight_lbs)
    rain_res = classify_rain(rain_in_per_hr)
    snow_res = classify_snow(snow_in_per_hr)

    factors = [
        ("Wind", RiskLevel(wind_res["level"]), wind_res),
        ("Rain", RiskLevel(rain_res["level"]), rain_res),
        ("Snow", RiskLevel(snow_res["level"]), snow_res),
    ]

    highest_level = RiskLevel.LOW
    highest_score = RISK_SEVERITY_ORDER[highest_level]
    critical_factors: List[str] = []

    for name, level, res in factors:
        score = RISK_SEVERITY_ORDER[level]
        if score > highest_score:
            highest_level = level
            highest_score = score
            critical_factors = [name]
        elif score == highest_score and score > 1:
            critical_factors.append(name)

    return {
        "overall_risk": highest_level.value,
        "risk_score": highest_score,
        "color": RISK_COLORS[highest_level],
        "critical_factors": critical_factors,
        "wind": wind_res,
        "rain": rain_res,
        "snow": snow_res,
        "load_rule_note": wind_res.get("rule_note"),
    }
