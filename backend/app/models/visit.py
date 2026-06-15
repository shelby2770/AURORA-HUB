"""Visit document — one website visit, with geolocation derived from the IP."""
from __future__ import annotations

from datetime import datetime, timezone

import pymongo
from beanie import Document
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GeoLocation(BaseModel):
    """Resolved location for a visitor IP (best-effort; any field may be None)."""

    country: str | None = None
    countryCode: str | None = None
    region: str | None = None
    city: str | None = None
    lat: float | None = None
    lon: float | None = None
    timezone: str | None = None
    isp: str | None = None


class Visit(Document):
    ip: str
    geo: GeoLocation | None = None
    path: str | None = None
    referrer: str | None = None
    userAgent: str | None = None
    createdAt: datetime = Field(default_factory=_utcnow)

    class Settings:
        name = "visits"
        indexes = [
            pymongo.IndexModel([("createdAt", pymongo.DESCENDING)]),
            pymongo.IndexModel([("geo.countryCode", pymongo.ASCENDING)]),
            pymongo.IndexModel([("ip", pymongo.ASCENDING)]),
        ]
