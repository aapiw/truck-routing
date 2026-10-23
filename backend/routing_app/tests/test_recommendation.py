import pytest
from routing_app.services.recommendation import rank_and_recommend_routes


class TestRecommendationService:
    def test_prefers_fewest_severe_miles(self):
        # Route 1: 50 severe miles, 3 hours
        # Route 2: 0 severe miles, 4 hours
        routes = [
            {
                "id": 1,
                "duration_seconds": 10800,
                "risk_summary": {"severe_miles": 50.0, "high_miles": 0.0, "average_risk_score": 2.5},
            },
            {
                "id": 2,
                "duration_seconds": 14400,
                "risk_summary": {"severe_miles": 0.0, "high_miles": 20.0, "average_risk_score": 1.8},
            },
        ]
        ranked = rank_and_recommend_routes(routes)
        assert ranked[0]["id"] == 2
        assert ranked[0]["is_recommended"] is True

    def test_prefers_fewest_high_miles_when_severe_tied(self):
        # Both 0 severe miles; Route A has 30 high miles, Route B has 10 high miles
        routes = [
            {
                "id": "A",
                "duration_seconds": 10000,
                "risk_summary": {"severe_miles": 0.0, "high_miles": 30.0, "average_risk_score": 2.0},
            },
            {
                "id": "B",
                "duration_seconds": 11000,
                "risk_summary": {"severe_miles": 0.0, "high_miles": 10.0, "average_risk_score": 1.7},
            },
        ]
        ranked = rank_and_recommend_routes(routes)
        assert ranked[0]["id"] == "B"

    def test_prefers_lowest_average_risk_when_high_and_severe_tied(self):
        routes = [
            {
                "id": "A",
                "duration_seconds": 10000,
                "risk_summary": {"severe_miles": 0.0, "high_miles": 0.0, "average_risk_score": 1.6},
            },
            {
                "id": "B",
                "duration_seconds": 10000,
                "risk_summary": {"severe_miles": 0.0, "high_miles": 0.0, "average_risk_score": 1.2},
            },
        ]
        ranked = rank_and_recommend_routes(routes)
        assert ranked[0]["id"] == "B"

    def test_prefers_shortest_time_when_all_risk_tied(self):
        routes = [
            {
                "id": "Slow",
                "duration_seconds": 15000,
                "risk_summary": {"severe_miles": 0.0, "high_miles": 0.0, "average_risk_score": 1.2},
            },
            {
                "id": "Fast",
                "duration_seconds": 12000,
                "risk_summary": {"severe_miles": 0.0, "high_miles": 0.0, "average_risk_score": 1.2},
            },
        ]
        ranked = rank_and_recommend_routes(routes)
        assert ranked[0]["id"] == "Fast"
