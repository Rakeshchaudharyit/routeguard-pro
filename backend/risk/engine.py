"""Pure, dependency-free weather risk classification for RouteGuard."""
from enum import IntEnum
from math import isfinite

class Risk(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4

def wind_risk(mph: float) -> Risk:
    if not isfinite(mph) or mph < 0: raise ValueError('Wind speed must be finite and nonnegative')
    if mph >= 55: return Risk.NO_TRAVEL
    if mph >= 45: return Risk.SEVERE
    if mph >= 35: return Risk.HIGH
    if mph >= 25: return Risk.MODERATE
    return Risk.LOW

def rain_risk(inches_per_hour: float) -> Risk:
    if not isfinite(inches_per_hour) or inches_per_hour < 0: raise ValueError('Rain must be finite and nonnegative')
    if inches_per_hour > 1.0: return Risk.NO_TRAVEL
    if inches_per_hour >= .5: return Risk.SEVERE
    if inches_per_hour >= .25: return Risk.HIGH
    if inches_per_hour >= .10: return Risk.MODERATE
    return Risk.LOW

def snow_risk(inches_per_hour: float) -> Risk:
    if not isfinite(inches_per_hour) or inches_per_hour < 0: raise ValueError('Snow must be finite and nonnegative')
    if inches_per_hour > 3.0: return Risk.NO_TRAVEL
    if inches_per_hour >= 2.0: return Risk.SEVERE
    if inches_per_hour >= 1.0: return Risk.HIGH
    if inches_per_hour >= .5: return Risk.MODERATE
    return Risk.LOW

def classify_weather(wind_mph: float, rain_in_hr: float, snow_in_hr: float, load_lb: float) -> Risk:
    if not isfinite(load_lb) or load_lb < 0: raise ValueError('Load weight must be finite and nonnegative')
    wind = wind_risk(wind_mph)
    if 45 <= wind_mph < 55 and load_lb > 30000: wind = Risk.NO_TRAVEL
    elif 35 <= wind_mph < 45 and load_lb > 40000: wind = Risk.SEVERE
    return max(wind, rain_risk(rain_in_hr), snow_risk(snow_in_hr))

def route_rank(severe_miles: float, high_miles: float, avg_risk: float, duration_minutes: float, no_travel_miles: float = 0) -> tuple:
    """No-travel is a safety gate; remaining keys follow the PDF's priority order."""
    return (no_travel_miles > 0, severe_miles, high_miles, avg_risk, duration_minutes)
