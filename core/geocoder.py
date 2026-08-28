"""
Geocoder & Distance Utilities
=============================
Uses OpenStreetMap Nominatim (free, no API key) to geocode city names,
computes haversine great-circle distance, and converts km to transit days.
Results are cached in-memory so repeated lookups are instant.
"""
from __future__ import annotations

import math
import logging
from typing import Optional, Tuple
from functools import lru_cache

import urllib.request
import urllib.parse
import json

logger = logging.getLogger("geocoder")

# In-memory cache: city -> (lat, long) or None
_city_cache: dict[str, Optional[Tuple[float, float]]] = {}

# Transit speed constant (km/day) — ~25 km/hr effective over a full day
_TRANSIT_SPEED_KM_PER_DAY: float = 500.0

# Nominatim rate-limit: 1 request/second
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode(city: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a city name to (latitude, longitude) using Nominatim.
    Returns (lat, long) tuple or None if geocoding fails.
    Results are cached in-memory.
    """
    if not city or not city.strip():
        return None

    city_key = city.strip().lower()
    if city_key in _city_cache:
        return _city_cache[city_key]

    params = urllib.parse.urlencode({
        "q": f"{city.strip()}, India",
        "format": "json",
        "limit": 1,
    })
    url = f"{_NOMINATIM_URL}?{params}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AutoSCM-Hackathon/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            coords = (lat, lon)
            _city_cache[city_key] = coords
            logger.info("[GEOCODER] Geocoded '%s' -> (%.4f, %.4f)", city, lat, lon)
            return coords
        else:
            logger.warning("[GEOCODER] No results for '%s'", city)
            _city_cache[city_key] = None
            return None
    except Exception as e:
        logger.warning("[GEOCODER] Failed to geocode '%s': %s", city, e)
        _city_cache[city_key] = None
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great-circle distance in km between two points
    using the Haversine formula.
    """
    R = 6371.0  # Earth's radius in km

    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 1)


def distance_km_to_transit_days(km: float) -> float:
    """
    Convert distance in km to estimated transit days.
    Uses a simple rate: ~500 km/day effective road speed.
    Returns 0 for trivially close distances.
    """
    if km <= 0:
        return 0.0
    days = km / _TRANSIT_SPEED_KM_PER_DAY
    # Minimum 0.1 day (~2.4 hours) for any non-zero distance
    return round(max(0.1, days), 1)


def distance_km_to_shipping_cost(km: float) -> float:
    """
    Estimate a distance-based last-mile shipping cost in USD.
    Flat handling fee plus a per-km freight rate. The nearest leg is most
    expensive per km (last-mile), then it flattens out for long hauls.
    Returns 0 for trivially close destinations (local hub dispatch).
    """
    if km <= 0:
        return 0.0
    # Last-mile handling fee for any dispatched shipment
    base_handling = 25.0
    # Freight: first 100km at $1.2/km, next 400km at $0.6/km, then $0.3/km
    rate = 0.0
    remaining = km
    for (width, cost) in ((100.0, 1.2), (400.0, 0.6), (1e9, 0.3)):
        leg = min(remaining, width)
        rate += leg * cost
        remaining -= leg
        if remaining <= 0:
            break
    return round(base_handling + rate, 2)


# Regional operating-cost multiplier per warehouse city (tier-1 metros cost
# more to operate out of than tier-3 hubs). Higher = more expensive warehouse.
_CITY_COST_MULTIPLIER: dict[str, float] = {
    "Mumbai": 1.35, "New Delhi": 1.30, "Bengaluru": 1.28, "Delhi": 1.30,
    "Chennai": 1.22, "Kolkata": 1.20, "Hyderabad": 1.18, "Pune": 1.15,
    "Ahmedabad": 1.10, "Jaipur": 1.05, "Lucknow": 1.03, "Nagpur": 1.02,
    "Indore": 1.00, "Coimbatore": 1.02, "Bhubaneswar": 1.00, "Guwahati": 1.06,
}


def regional_price_multiplier(city: str) -> float:
    """
    Return a stable per-warehouse price multiplier for a given city.
    Tier-1 metros are costlier to operate out of (higher multiplier);
    tier-3 hubs are cheaper. Falls back to 1.0 for unknown cities.
    """
    if not city:
        return 1.0
    norm = city.strip().title()
    # Match the base city name (e.g. "New Delhi" in "New Delhi Warehouse")
    for key, mult in _CITY_COST_MULTIPLIER.items():
        if key in norm or norm in key:
            return mult
    return 1.0


def reset_cache():
    """Clear the geocoding cache (useful for tests)."""
    _city_cache.clear()
