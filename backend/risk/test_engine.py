import unittest
from risk.engine import Risk, classify_weather, rain_risk, snow_risk, route_rank

class RiskTests(unittest.TestCase):
    def test_wind_no_travel(self): self.assertEqual(classify_weather(55, 0, 0, 0), Risk.NO_TRAVEL)
    def test_load_boundary_30000(self): self.assertEqual(classify_weather(45, 0, 0, 30000), Risk.SEVERE)
    def test_load_over_30000(self): self.assertEqual(classify_weather(45, 0, 0, 30001), Risk.NO_TRAVEL)
    def test_load_boundary_40000(self): self.assertEqual(classify_weather(35, 0, 0, 40000), Risk.HIGH)
    def test_load_over_40000(self): self.assertEqual(classify_weather(35, 0, 0, 40001), Risk.SEVERE)
    def test_rain_upper(self): self.assertEqual(rain_risk(1.0), Risk.SEVERE)
    def test_snow_upper(self): self.assertEqual(snow_risk(3.0), Risk.SEVERE)
    def test_route_ranking(self): self.assertLess(route_rank(0, 10, 2, 600), route_rank(1, 0, 0, 500))
    def test_no_travel_gate(self): self.assertGreater(route_rank(0, 0, 0, 100, 1), route_rank(10, 10, 3, 1000))

if __name__ == '__main__': unittest.main()
