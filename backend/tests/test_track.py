"""Visitor tracking endpoints: record a visit, list it, aggregate by country.

Geolocation is monkeypatched so tests don't hit the network and IPs resolve
deterministically.
"""
from __future__ import annotations

import pytest

from app.models.visit import GeoLocation


@pytest.fixture(autouse=True)
def _fake_geo(monkeypatch):
    async def fake_geolocate(ip: str):
        return GeoLocation(country="Bangladesh", countryCode="BD", city="Dhaka")

    monkeypatch.setattr("app.api.track.geolocate", fake_geolocate)


async def test_record_visit_uses_forwarded_ip(client):
    resp = await client.post(
        "/track/visit",
        json={"path": "/quiz"},
        headers={"x-forwarded-for": "203.0.113.7, 10.0.0.1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ip"] == "203.0.113.7"  # first hop, not the proxy
    assert body["path"] == "/quiz"
    assert body["geo"]["countryCode"] == "BD"


async def test_visits_and_stats(client):
    for ip in ("203.0.113.7", "203.0.113.8"):
        await client.post("/track/visit", headers={"x-forwarded-for": ip})

    visits = (await client.get("/track/visits")).json()
    assert len(visits) == 2

    stats = (await client.get("/track/stats")).json()
    assert stats == [{"countryCode": "BD", "country": "Bangladesh", "count": 2}]


async def test_read_endpoints_require_password_when_configured(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "admin_password", "s3cret")

    assert (await client.get("/track/visits")).status_code == 401
    assert (await client.get("/track/stats")).status_code == 401
    assert (
        await client.get("/track/visits", headers={"x-admin-password": "wrong"})
    ).status_code == 401

    ok = await client.get("/track/stats", headers={"x-admin-password": "s3cret"})
    assert ok.status_code == 200

    # Recording a visit stays open (no password needed).
    assert (await client.post("/track/visit")).status_code == 200
