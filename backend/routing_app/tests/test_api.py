from rest_framework.test import APITestCase
from rest_framework import status


class ApiEndpointsTestCase(APITestCase):
    def test_health_check(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("status"), "healthy")

    def test_geocode_endpoint(self):
        response = self.client.get("/api/geocode/?q=Denver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_analyze_routes_endpoint_validation(self):
        # Missing coordinates should return 400
        response = self.client.post("/api/routes/analyze/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analyze_routes_endpoint_success(self):
        payload = {
            "origin": {"lat": 39.7392, "lon": -104.9903, "label": "Denver, CO"},
            "destination": {"lat": 40.7608, "lon": -111.8910, "label": "Salt Lake City, UT"},
            "departure_time": "2026-10-21T08:00:00Z",
            "load_weight": 42000,
            "sampling_interval_miles": 50,
        }
        response = self.client.post("/api/routes/analyze/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn("routes", data)
        self.assertEqual(len(data["routes"]), 3)
        self.assertIn("recommended_route_id", data)
        self.assertIn("corridor_grid", data)

        # Check structure of the recommended route
        rec_id = data["recommended_route_id"]
        rec_route = next(r for r in data["routes"] if r["id"] == rec_id)
        self.assertTrue(rec_route["is_recommended"])
        self.assertIn("checkpoints", rec_route)
        self.assertIn("risk_summary", rec_route)
        self.assertIn("colored_segments", rec_route)
        self.assertGreater(len(rec_route["checkpoints"]), 2)
