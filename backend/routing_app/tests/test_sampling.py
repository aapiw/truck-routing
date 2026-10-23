from datetime import datetime, timezone
import pytest
from routing_app.services.sampling import sample_route_checkpoints, haversine_miles


class TestSamplingService:
    def test_haversine_distance(self):
        # Distance between NYC (40.7128, -74.0060) and Philadelphia (39.9526, -75.1652) is ~80 miles
        dist = haversine_miles(40.7128, -74.0060, 39.9526, -75.1652)
        assert 75.0 < dist < 85.0

    def test_sample_route_checkpoints_25_miles(self):
        coords = [
            [40.0, -80.0],
            [40.0, -81.0],
            [40.0, -82.0],
        ]
        dep_time = datetime(2026, 10, 20, 8, 0, tzinfo=timezone.utc)
        total_dist = 100.0  # miles
        total_duration = 7200.0  # 2 hours

        cps = sample_route_checkpoints(
            coordinates=coords,
            total_distance_miles=total_dist,
            total_duration_seconds=total_duration,
            departure_time=dep_time,
            interval_miles=25,
        )

        assert len(cps) == 5
        assert cps[0]["is_origin"] is True
        assert cps[0]["distance_from_origin_miles"] == 0.0
        assert cps[0]["elapsed_seconds"] == 0

        assert cps[-1]["is_destination"] is True
        assert cps[-1]["distance_from_origin_miles"] == 100.0
        assert cps[-1]["elapsed_seconds"] == 7200

        # Verify total segment miles sum up to total distance
        total_segment_miles = sum(cp["segment_miles"] for cp in cps)
        assert abs(total_segment_miles - total_dist) < 0.1

    def test_sampling_intervals_10_and_50(self):
        coords = [
            [35.0, -90.0],
            [35.0, -92.0],
        ]
        dep_time = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)
        total_dist = 100.0
        total_dur = 6000.0

        cps_10 = sample_route_checkpoints(coords, total_dist, total_dur, dep_time, interval_miles=10)
        cps_50 = sample_route_checkpoints(coords, total_dist, total_dur, dep_time, interval_miles=50)

        assert len(cps_10) > len(cps_50)
        assert abs(sum(c["segment_miles"] for c in cps_10) - total_dist) < 0.1
        assert abs(sum(c["segment_miles"] for c in cps_50) - total_dist) < 0.1
