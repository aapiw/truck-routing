import pytest
from routing_app.services.risk_engine import (
    RiskLevel,
    classify_wind,
    classify_rain,
    classify_snow,
    evaluate_checkpoint_risk,
)


class TestRiskEngine:
    def test_wind_thresholds_standard_load(self):
        standard_load = 20000.0
        assert classify_wind(15.0, standard_load)["level"] == RiskLevel.LOW.value
        assert classify_wind(24.9, standard_load)["level"] == RiskLevel.LOW.value
        assert classify_wind(25.0, standard_load)["level"] == RiskLevel.MODERATE.value
        assert classify_wind(34.9, standard_load)["level"] == RiskLevel.MODERATE.value
        assert classify_wind(35.0, standard_load)["level"] == RiskLevel.HIGH.value
        assert classify_wind(44.9, standard_load)["level"] == RiskLevel.HIGH.value
        assert classify_wind(45.0, standard_load)["level"] == RiskLevel.SEVERE.value
        assert classify_wind(54.9, standard_load)["level"] == RiskLevel.SEVERE.value
        assert classify_wind(55.0, standard_load)["level"] == RiskLevel.NO_TRAVEL.value
        assert classify_wind(70.0, standard_load)["level"] == RiskLevel.NO_TRAVEL.value

    def test_wind_load_escalation_rules(self):
        # 1. >= 55 mph -> No Travel for any load
        assert classify_wind(55.0, 10000)["level"] == RiskLevel.NO_TRAVEL.value
        assert classify_wind(58.0, 50000)["level"] == RiskLevel.NO_TRAVEL.value

        # 2. 45-54 mph + >30,000 lb -> No Travel
        assert classify_wind(48.0, 30000)["level"] == RiskLevel.SEVERE.value
        res_escalated_30k = classify_wind(48.0, 30001)
        assert res_escalated_30k["level"] == RiskLevel.NO_TRAVEL.value
        assert "escalated to No Travel" in (res_escalated_30k["rule_note"] or "")

        # 3. 35-44 mph + >40,000 lb -> Severe
        assert classify_wind(40.0, 40000)["level"] == RiskLevel.HIGH.value
        res_escalated_40k = classify_wind(40.0, 40001)
        assert res_escalated_40k["level"] == RiskLevel.SEVERE.value
        assert "escalated to Severe" in (res_escalated_40k["rule_note"] or "")

    def test_rain_thresholds(self):
        assert classify_rain(0.05)["level"] == RiskLevel.LOW.value
        assert classify_rain(0.099)["level"] == RiskLevel.LOW.value
        assert classify_rain(0.10)["level"] == RiskLevel.MODERATE.value
        assert classify_rain(0.24)["level"] == RiskLevel.MODERATE.value
        assert classify_rain(0.25)["level"] == RiskLevel.HIGH.value
        assert classify_rain(0.49)["level"] == RiskLevel.HIGH.value
        assert classify_rain(0.50)["level"] == RiskLevel.SEVERE.value
        assert classify_rain(0.99)["level"] == RiskLevel.SEVERE.value
        assert classify_rain(1.00)["level"] == RiskLevel.SEVERE.value
        assert classify_rain(1.01)["level"] == RiskLevel.NO_TRAVEL.value

    def test_snow_thresholds(self):
        assert classify_snow(0.2)["level"] == RiskLevel.LOW.value
        assert classify_snow(0.49)["level"] == RiskLevel.LOW.value
        assert classify_snow(0.50)["level"] == RiskLevel.MODERATE.value
        assert classify_snow(0.99)["level"] == RiskLevel.MODERATE.value
        assert classify_snow(1.00)["level"] == RiskLevel.HIGH.value
        assert classify_snow(1.99)["level"] == RiskLevel.HIGH.value
        assert classify_snow(2.00)["level"] == RiskLevel.SEVERE.value
        assert classify_snow(3.00)["level"] == RiskLevel.SEVERE.value
        assert classify_snow(3.01)["level"] == RiskLevel.NO_TRAVEL.value

    def test_checkpoint_evaluation_composite(self):
        # Overall risk must equal the highest severity component
        eval_res = evaluate_checkpoint_risk(
            wind_mph=20.0,       # LOW
            rain_in_per_hr=0.30, # HIGH
            snow_in_per_hr=0.0,  # LOW
            load_weight_lbs=25000,
        )
        assert eval_res["overall_risk"] == RiskLevel.HIGH.value
        assert "Rain" in eval_res["critical_factors"]

        # Severe wind escalation overrides moderate rain
        eval_res2 = evaluate_checkpoint_risk(
            wind_mph=48.0,       # Severe -> escalated to NO_TRAVEL due to 45k lb load
            rain_in_per_hr=0.15, # MODERATE
            snow_in_per_hr=0.0,
            load_weight_lbs=45000,
        )
        assert eval_res2["overall_risk"] == RiskLevel.NO_TRAVEL.value
        assert "Wind" in eval_res2["critical_factors"]
