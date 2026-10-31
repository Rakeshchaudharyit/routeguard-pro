from datetime import datetime,timezone
from unittest.mock import patch
from routing.services import analyze_trip
@patch('routing.services.fetch_routes')
@patch('routing.services.geocode_location')
def test_real_geometry_and_no_fake_weather(geo,routes):
 geo.side_effect=[{'label':'A','lat':1,'lon':2},{'label':'B','lat':3,'lon':4}]
 geometry={'type':'LineString','coordinates':[[2,1],[4,3]]}
 routes.return_value=[{'distance':160934.4,'duration':7200,'geometry':geometry}]
 result=analyze_trip('Start','End',datetime(2026,11,1,tzinfo=timezone.utc),30000,25)
 assert result['routes'][0]['distance_miles']==100
 assert result['routes'][0]['geometry']==geometry
 assert result['recommendation'] is None
 assert not result['weather_analyzed']
 assert len(result['routes'])==1
