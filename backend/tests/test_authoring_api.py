"""Phase 5: async authoring endpoint (mock providers via dependency override)."""
from __future__ import annotations

import json
import uuid

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from app.api.authoring import get_authoring_providers
from app.core.config import settings
from app.llm.mock import MockProvider
from app.models.course import Course, Subtopic
from app.scripts.seed import seed_database


def _candidate_array():
    return json.dumps(
        [
            {
                "questionText": "Trace this loop output",
                "options": ["0", "1", "2", "3"],
                "correctIndex": 2,
                "explanation": "x",
                "distractorRationales": ["", "", "", ""],
                "computable": True,
                "verificationCode": "correct_index = 2",
            }
        ]
    )


@pytest_asyncio.fixture
async def authoring_client(mongo_uri, monkeypatch):
    db_name = f"aurora_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(settings, "mongodb_uri", mongo_uri)
    monkeypatch.setattr(settings, "mongodb_db", db_name)

    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_authoring_providers] = lambda: (
        MockProvider(responses=[_candidate_array()]),  # generator
        MockProvider(),  # verifier (unused for computable)
        MockProvider(),  # embedder
    )
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    cleanup = AsyncMongoClient(mongo_uri)
    await cleanup.drop_database(db_name)
    await cleanup.close()


async def _seeded_subtopic_id() -> str:
    await seed_database()
    course = await Course.find_one(Course.slug == "operating-systems")
    sub = await Subtopic.find_one(Subtopic.courseId == course.id)
    return str(sub.id)


async def test_generate_runs_job_and_reports(authoring_client):
    sub_id = await _seeded_subtopic_id()
    resp = await authoring_client.post(
        "/authoring/generate",
        json={"subtopicId": sub_id, "difficulty": "medium", "n": 1},
    )
    assert resp.status_code == 202
    job_id = resp.json()["jobId"]

    status = await authoring_client.get(f"/authoring/jobs/{job_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "done"
    assert body["report"]["accepted"] == 1


async def test_generate_unknown_subtopic_404(authoring_client):
    await seed_database()
    resp = await authoring_client.post(
        "/authoring/generate",
        json={"subtopicId": "0123456789abcdef01234567", "difficulty": "easy", "n": 1},
    )
    assert resp.status_code == 404


async def test_generate_rejects_out_of_range_n(authoring_client):
    sub_id = await _seeded_subtopic_id()
    resp = await authoring_client.post(
        "/authoring/generate",
        json={"subtopicId": sub_id, "difficulty": "easy", "n": 99},
    )
    assert resp.status_code == 422
