"""IP geolocation via ip-api.com.

Free tier: 45 requests/min, HTTP only (no key). We call it server-side, so HTTP
is fine. Private/loopback IPs are skipped (they can't be geolocated).
"""
from __future__ import annotations

import ipaddress
import logging

import httpx

from app.models.visit import GeoLocation

logger = logging.getLogger(__name__)

_FIELDS = "status,country,countryCode,regionName,city,lat,lon,timezone,isp"
_URL = "http://ip-api.com/json/{ip}?fields=" + _FIELDS


def _is_public(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


async def geolocate(ip: str) -> GeoLocation | None:
    """Resolve a public IP to a location. Returns None on private IPs or failure."""
    if not ip or not _is_public(ip):
        return None
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(_URL.format(ip=ip))
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:  # network error / bad JSON
        logger.warning("geolocation failed for %s: %s", ip, exc)
        return None
    if data.get("status") != "success":
        return None
    return GeoLocation(
        country=data.get("country"),
        countryCode=data.get("countryCode"),
        region=data.get("regionName"),
        city=data.get("city"),
        lat=data.get("lat"),
        lon=data.get("lon"),
        timezone=data.get("timezone"),
        isp=data.get("isp"),
    )
