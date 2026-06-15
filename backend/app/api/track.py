"""Visitor tracking endpoints (analytics plane).

`POST /track/visit` records one visit (the frontend calls this on page load);
the real client IP is taken from `X-Forwarded-For` since the app runs behind a
proxy (Render). `GET /track/visits` and `GET /track/stats` read it back.
"""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.core.config import settings
from app.models.visit import Visit
from app.schemas.visit import CountryStat, VisitIn, VisitOut
from app.services.geo import geolocate

router = APIRouter(prefix="/track", tags=["track"])


def require_admin(x_admin_password: str | None = Header(default=None)) -> None:
    """Gate the read endpoints. If ADMIN_PASSWORD is unset, access is open (dev)."""
    expected = settings.admin_password
    if not expected:
        return
    if not x_admin_password or not secrets.compare_digest(
        x_admin_password, expected
    ):
        raise HTTPException(status_code=401, detail="Invalid admin password")


def _client_ip(request: Request) -> str:
    """First hop in X-Forwarded-For is the real client; fall back to peer addr."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/visit", response_model=VisitOut)
async def record_visit(request: Request, body: VisitIn | None = None) -> VisitOut:
    ip = _client_ip(request)
    geo = await geolocate(ip)
    visit = Visit(
        ip=ip,
        geo=geo,
        path=body.path if body else None,
        referrer=(body.referrer if body else None) or request.headers.get("referer"),
        userAgent=request.headers.get("user-agent"),
    )
    await visit.insert()
    return VisitOut.model_validate(visit)


@router.get(
    "/visits", response_model=list[VisitOut], dependencies=[Depends(require_admin)]
)
async def list_visits(limit: int = Query(100, ge=1, le=1000)) -> list[VisitOut]:
    docs = await Visit.find_all().sort("-createdAt").limit(limit).to_list()
    return [VisitOut.model_validate(d) for d in docs]


@router.get(
    "/stats", response_model=list[CountryStat], dependencies=[Depends(require_admin)]
)
async def country_stats() -> list[CountryStat]:
    """Visit counts grouped by country, most-visited first."""
    pipeline = [
        {
            "$group": {
                "_id": {"code": "$geo.countryCode", "name": "$geo.country"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]
    rows = await Visit.aggregate(pipeline).to_list()
    return [
        CountryStat(
            countryCode=r["_id"].get("code"),
            country=r["_id"].get("name"),
            count=r["count"],
        )
        for r in rows
    ]
