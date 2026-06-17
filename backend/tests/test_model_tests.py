"""Model Test serving plane: seeding, answer withholding, scoring, pass/fail."""
from __future__ import annotations

from app.models.model_test import ModelTest
from app.scripts.seed_model_tests import seed_model_tests

ANSWER_KEYS = {"correctIndex", "explanation"}


async def _seed() -> None:
    created, _ = await seed_model_tests()
    # Sample model test + Model Test 1..5 from data/model_tests.
    assert created == 6


# ── listing ──────────────────────────────────────────────────────────────────
async def test_list_returns_all_tests_sample_first(client):
    await _seed()
    resp = await client.get("/model-tests")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    assert data[0]["slug"] == "sample-model-test"  # ordered first
    for t in data:
        assert t["totalQuestions"] == 50
        assert t["fullMarks"] == 150
        assert t["passMarks"] == 60
        assert t["marksPerQuestion"] == 3
        assert "slug" in t and "title" in t


# ── start withholds the answer key ───────────────────────────────────────────
async def test_start_withholds_answers_and_sets_duration(client):
    await _seed()
    slug = (await client.get("/model-tests")).json()[0]["slug"]
    resp = await client.post(f"/model-tests/{slug}/start")
    assert resp.status_code == 200
    data = resp.json()
    assert data["durationSeconds"] == 90 * 60  # 90-minute exam
    assert len(data["questions"]) == 50
    for q in data["questions"]:
        assert ANSWER_KEYS.isdisjoint(q.keys()), "start must not leak the answer key"
        assert len(q["options"]) == 4
        assert "subject" in q


async def test_start_unknown_slug_404(client):
    await _seed()
    resp = await client.post("/model-tests/does-not-exist/start")
    assert resp.status_code == 404


# ── scoring + pass/fail + subject breakdown ──────────────────────────────────
async def test_submit_all_correct_passes(client):
    await _seed()
    slug = (await client.get("/model-tests")).json()[0]["slug"]
    session_id = (await client.post(f"/model-tests/{slug}/start")).json()["sessionId"]

    test = await ModelTest.find_one(ModelTest.slug == slug)
    answers = [q.correctIndex for q in test.questions]

    resp = await client.post(
        f"/model-tests/sessions/{session_id}/submit", json={"answers": answers}
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["score"] == 50
    assert result["total"] == 50
    assert result["marks"] == 150
    assert result["passed"] is True
    # Review re-includes the answer key + correctness flags.
    assert all(ANSWER_KEYS <= q.keys() for q in result["questions"])
    assert all(q["isCorrect"] for q in result["questions"])
    # Subject breakdown covers every question across the 12 subjects.
    assert sum(s["total"] for s in result["subjectBreakdown"]) == 50
    assert sum(s["correct"] for s in result["subjectBreakdown"]) == 50


async def test_submit_all_blank_fails(client):
    await _seed()
    slug = (await client.get("/model-tests")).json()[0]["slug"]
    session_id = (await client.post(f"/model-tests/{slug}/start")).json()["sessionId"]

    resp = await client.post(
        f"/model-tests/sessions/{session_id}/submit", json={"answers": [None] * 50}
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["score"] == 0
    assert result["marks"] == 0
    assert result["passed"] is False


async def test_submit_at_pass_threshold(client):
    """Exactly 20 correct = 60 marks = 40% qualifies as a pass."""
    await _seed()
    slug = (await client.get("/model-tests")).json()[0]["slug"]
    session_id = (await client.post(f"/model-tests/{slug}/start")).json()["sessionId"]

    test = await ModelTest.find_one(ModelTest.slug == slug)
    # First 20 correct, the rest deliberately wrong.
    answers = [
        q.correctIndex if i < 20 else (q.correctIndex + 1) % 4
        for i, q in enumerate(test.questions)
    ]
    resp = await client.post(
        f"/model-tests/sessions/{session_id}/submit", json={"answers": answers}
    )
    result = resp.json()
    assert result["score"] == 20
    assert result["marks"] == 60
    assert result["passed"] is True


async def test_submit_answer_length_mismatch_422(client):
    await _seed()
    slug = (await client.get("/model-tests")).json()[0]["slug"]
    session_id = (await client.post(f"/model-tests/{slug}/start")).json()["sessionId"]
    resp = await client.post(
        f"/model-tests/sessions/{session_id}/submit", json={"answers": [0, 1, 2]}
    )
    assert resp.status_code == 422


async def test_submit_unknown_session_404(client):
    await _seed()
    resp = await client.post(
        "/model-tests/sessions/0123456789abcdef01234567/submit",
        json={"answers": []},
    )
    assert resp.status_code == 404
