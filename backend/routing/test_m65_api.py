"""M6.5: deterministic API regression tests; no external provider requests."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from django.test import SimpleTestCase
from rest_framework.test import APIClient
from routing.services import ProviderError
from routing.weather import WeatherUnavailable


class AnalyzeEndpointRegressionTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {'origin': 'Dallas, TX', 'destination': 'Atlanta, GA',
                        'departure_at': (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                        'load_weight_lb': 28000, 'checkpoint_interval_miles': 50}

    def test_rejects_invalid_inputs_without_contacting_providers(self):
        cases = [
            {'load_weight_lb': -1}, {'load_weight_lb': 'nan'},
            {'load_weight_lb': 200001}, {'checkpoint_interval_miles': 7},
            {'departure_at': '2026-10-31T12:00:00'}, {'departure_at': 'not-a-date'},
            {'origin': []}, {'destination': None},
        ]
        with patch('routing.views.analyze_trip') as provider:
            for change in cases:
                with self.subTest(change=change):
                    response = self.client.post('/api/routes/analyze/', {**self.payload, **change}, format='json')
                    self.assertEqual(response.status_code, 400)
            provider.assert_not_called()

    def test_routing_provider_failure_returns_503(self):
        with patch('routing.views.analyze_trip', side_effect=ProviderError('Routing unavailable')):
            response = self.client.post('/api/routes/analyze/', self.payload, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertIn('error', response.json())

    def test_weather_outage_keeps_routes_but_never_certifies_safe(self):
        route = {'id': 'route-1', 'name': 'Route A', 'distance_miles': 100,
                 'duration_seconds': 7200, 'geometry': {'type': 'LineString', 'coordinates': [[-96, 32], [-95, 33]]},
                 'recommended': False, 'risk_level': None, 'weather_status': 'not_analyzed'}
        result = {'origin': {'label': 'Dallas', 'lat': 32, 'lon': -96},
                  'destination': {'label': 'Atlanta', 'lat': 33, 'lon': -95},
                  'routes': [route], 'warnings': [], 'weather_analyzed': False, 'recommendation': None}
        with patch('routing.views.analyze_trip', return_value=result), \
             patch('routing.views.assess_routes', side_effect=WeatherUnavailable('Forecast unavailable')):
            response = self.client.post('/api/routes/analyze/', self.payload, format='json')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body['weather_analyzed'])
        self.assertIsNone(body['recommendation'])
        self.assertFalse(body['routes'][0]['recommended'])
        self.assertTrue(any('no route is certified safe' in w for w in body['warnings']))

    def test_complete_weather_assessment_recommends_lower_risk_route(self):
        def route(id):
            return {'id': id, 'distance_miles': 100, 'duration_seconds': 7200,
                    'geometry': {'type': 'LineString', 'coordinates': [[-96, 32], [-95, 33]]},
                    'recommended': False}
        result = {'origin': {'label': 'Dallas', 'lat': 32, 'lon': -96},
                  'destination': {'label': 'Atlanta', 'lat': 33, 'lon': -95},
                  'routes': [route('route-1'), route('route-2')], 'warnings': [],
                  'weather_analyzed': False, 'recommendation': None}
        assessments = [{'rank': (0, 0, 0.5, 100), 'no_travel_miles': 0, 'risk_level': 'moderate'},
                       {'rank': (0, 0, 0.1, 100), 'no_travel_miles': 0, 'risk_level': 'low'}]
        with patch('routing.views.analyze_trip', return_value=result), \
             patch('routing.views.assess_routes', return_value=assessments):
            response = self.client.post('/api/routes/analyze/', self.payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['recommendation'], 'route-2')
        self.assertTrue(response.json()['weather_analyzed'])
