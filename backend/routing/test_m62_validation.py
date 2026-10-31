"""M6.2 regression tests for forecast integrity and route risk."""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from routing.weather import nearest_hourly, assess_routes, WeatherUnavailable, sample_route
from risk.engine import classify_weather, Risk, route_rank


class ForecastIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.when = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)

    def test_missing_or_stale_hour_is_unavailable(self):
        data = {'hourly': {'time': ['2026-11-01T09:00'], 'wind_gusts_10m': [10], 'precipitation': [0], 'snowfall': [0]}}
        self.assertIsNone(nearest_hourly(data, self.when))

    def test_nonfinite_or_negative_provider_metrics_are_unavailable(self):
        for wind, rain, snow in [(float('nan'), 0, 0), (float('inf'), 0, 0), (10, -1, 0), (10, 0, -1)]:
            data = {'hourly': {'time': ['2026-11-01T12:00'], 'wind_gusts_10m': [wind], 'precipitation': [rain], 'snowfall': [snow]}}
            with self.subTest(metrics=(wind, rain, snow)):
                self.assertIsNone(nearest_hourly(data, self.when))

    def test_timezone_offset_forecast_timestamp(self):
        data = {'hourly': {'time': ['2026-11-01T13:00+01:00'], 'wind_gusts_10m': [10], 'precipitation': [0], 'snowfall': [2.54]}}
        self.assertEqual(nearest_hourly(data, self.when), (10, 0, 1))

    def test_risk_boundaries_and_load_override(self):
        self.assertEqual(classify_weather(25, 0, 0, 28000), Risk.MODERATE)
        self.assertEqual(classify_weather(35, 0, 0, 28000), Risk.HIGH)
        self.assertEqual(classify_weather(46, 0, 0, 35000), Risk.NO_TRAVEL)
        self.assertEqual(classify_weather(36, 0, 0, 45000), Risk.SEVERE)
        self.assertEqual(classify_weather(10, .25, 0, 28000), Risk.HIGH)
        self.assertEqual(classify_weather(10, 0, 1, 28000), Risk.HIGH)
        for bad in [float('nan'), float('inf'), -1]:
            with self.assertRaises(ValueError):
                classify_weather(bad, 0, 0, 28000)

    def test_route_rank_safety_priority(self):
        self.assertLess(route_rank(0, 0, .5, 100), route_rank(1, 0, 0, 60))
        self.assertLess(route_rank(0, 0, 1, 100), route_rank(0, 1, 0, 60))
        self.assertLess(route_rank(0, 0, .2, 200), route_rank(0, 0, .3, 100))

    @patch('routing.weather.fetch_forecasts', return_value=[])
    def test_mismatched_forecast_count_is_not_silently_truncated(self, _fetch):
        route = {'geometry': {'coordinates': [[-96, 32], [-95, 32]]}, 'distance': 100*1609.344, 'duration': 7200}
        with self.assertRaises(WeatherUnavailable):
            assess_routes([route], self.when, 28000, 50)


if __name__ == '__main__':
    unittest.main()
