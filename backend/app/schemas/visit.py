"""Visit tracking request/response schemas."""
from __future__ import annotations

from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict

from app.models.visit import GeoLocation


class VisitIn(BaseModel):
    """Optional context the frontend can attach to a tracked visit."""

    path: str | None = None
    referrer: str | None = None


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PydanticObjectId
    ip: str
    geo: GeoLocation | None = None
    path: str | None = None
    referrer: str | None = None
    userAgent: str | None = None
    createdAt: datetime


class CountryStat(BaseModel):
    countryCode: str | None = None
    country: str | None = None
    count: int
