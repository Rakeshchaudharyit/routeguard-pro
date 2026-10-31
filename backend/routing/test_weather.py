from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch
from routing.weather import sample_route, assess_routes, nearest_hourly

class WeatherTests(TestCase):
    def setUp(self):
        self.route={'geometry':{'type':'LineString','coordinates':[[-96,32],[-95,32],[-94,32]]},'distance': 200*1609.344,'duration': 14400}
        self.departure=datetime(2026,11,1,12,tzinfo=timezone.utc)
    def test_checkpoint_mileage(self):
        p=sample_route(self.route,50,self.departure)
        self.assertEqual([x['mile'] for x in p],[0,50,100,150,200])
        self.assertEqual(p[-1]['eta'],datetime(2026,11,1,16,tzinfo=timezone.utc).isoformat())
    def test_nearest_hour(self):
        forecast={'hourly':{'time':['2026-11-01T12:00','2026-11-01T13:00'],'wind_gusts_10m':[20,46],'precipitation':[0,.3],'snowfall':[0,2.54]}}
        self.assertEqual(nearest_hourly(forecast,datetime(2026,11,1,13,tzinfo=timezone.utc)),(46,.3,1))
    @patch('routing.weather.fetch_forecasts')
    def test_load_override_and_ranking(self,fetch):
        count=len(sample_route(self.route,50,self.departure))
        fetch.return_value=[{'hourly':{'time':['2026-11-01T12:00','2026-11-01T13:00','2026-11-01T14:00','2026-11-01T15:00','2026-11-01T16:00'],'wind_gusts_10m':[46]*5,'precipitation':[0]*5,'snowfall':[0]*5}} for _ in range(count)]
        result=assess_routes([self.route],self.departure,35000,50)[0]
        self.assertEqual(result['risk_level'],'no_travel')
        self.assertEqual(result['no_travel_miles'],200)
        self.assertEqual(result['weather_status'],'analyzed')
    @patch('routing.weather.fetch_forecasts')
    def test_missing_forecast_never_becomes_low(self, fetch):
        count=len(sample_route(self.route,50,self.departure))
        fetch.return_value=[{'hourly':{'time':['2026-11-01T12:00'], 'wind_gusts_10m':[12], 'precipitation':[0], 'snowfall':[0]}} for _ in range(count)]
        result=assess_routes([self.route],self.departure,35000,50)[0]
        self.assertEqual(result['weather_status'],'incomplete')
        self.assertIsNone(result['rank'])
        self.assertGreater(result['unknown_miles'],0)
        self.assertLess(result['forecast_coverage']['analyzed'],result['forecast_coverage']['total'])
