import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from routing.weather import timeline_at_point, TIMELINE_HOURS

class TimelineTests(unittest.TestCase):
    def test_nine_real_forecast_samples(self):
        now = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)
        forecast = {'hourly': {'time': [f'2026-11-{1 + (12+h)//24:02d}T{(12+h)%24:02d}:00' if h >= 12 else f'2026-10-31T{12+h:02d}:00' for h in range(12)]}}
        with patch('routing.weather.forecast_at_hour', return_value=(30, 0, 0)):
            result = timeline_at_point(forecast, now, 28000)
        self.assertEqual([v['hour'] for v in result], TIMELINE_HOURS)
        self.assertTrue(all(v['risk'] == 'moderate' for v in result))

    def test_missing_weather_stays_unknown(self):
        with patch('routing.weather.forecast_at_hour', return_value=None):
            result = timeline_at_point({}, datetime.now(timezone.utc), 35000)
        self.assertTrue(all(v['risk'] == 'unavailable' for v in result))

    def test_heavy_load_wind_override(self):
        with patch('routing.weather.forecast_at_hour', return_value=(48, 0, 0)):
            result = timeline_at_point({}, datetime.now(timezone.utc), 35000)
        self.assertTrue(all(v['risk'] == 'no_travel' for v in result))
