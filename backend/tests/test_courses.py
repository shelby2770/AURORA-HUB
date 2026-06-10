"""Phase 2: course + subtopic listing endpoints."""
from __future__ import annotations

from app.scripts.seed import seed_database
from app.scripts.seed_data import SEED


async def test_list_courses(client):
    await seed_database()
    resp = await client.get("/courses")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == len(SEED)
    sample = body[0]
    assert {"id", "name", "slug", "isActive"} <= sample.keys()
    assert all(c["isActive"] for c in body)


async def test_list_subtopics(client):
    await seed_database()
    resp = await client.get("/courses/operating-systems/subtopics")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == len(SEED["Operating Systems"])
    assert all(s["courseId"] for s in body)


async def test_subtopics_unknown_course_404(client):
    await seed_database()
    resp = await client.get("/courses/not-a-course/subtopics")
    assert resp.status_code == 404
