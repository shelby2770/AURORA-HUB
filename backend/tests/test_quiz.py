"""Phase 2: quiz serving plane — selection, caps, withholding, scoring."""
from __future__ import annotations

from app.models.course import Course, Subtopic
from app.models.enums import Difficulty, QuestionSource
from app.models.question import Question
from app.scripts.seed import seed_database
from tests.factories import make_many, make_question

ANSWER_KEYS = {"correctIndex", "explanation", "distractorRationales"}


async def _course_and_subtopic() -> tuple[Course, Subtopic]:
    await seed_database()
    course = await Course.find_one(Course.slug == "operating-systems")
    sub = await Subtopic.find_one(Subtopic.courseId == course.id)
    return course, sub


async def _start(client, course, sub, *, count, difficulty="medium", mode="exam"):
    body = {
        "courseId": str(course.id),
        "count": count,
        "difficulty": difficulty,
        "mode": mode,
    }
    if sub is not None:
        body["subtopicId"] = str(sub.id)
    return await client.post("/quiz/start", json=body)


# ── withholding ────────────────────────────────────────────────────────────
async def test_exam_start_withholds_answer_key(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=10,
                    source=QuestionSource.exemplar)
    resp = await _start(client, course, sub, count=10, mode="exam")
    assert resp.status_code == 200
    data = resp.json()
    assert data["durationSeconds"] == 90 * 10
    for q in data["questions"]:
        assert ANSWER_KEYS.isdisjoint(q.keys()), "exam must not leak answer key"
        assert "options" in q


async def test_practice_start_includes_answer_key(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=10,
                    source=QuestionSource.exemplar)
    resp = await _start(client, course, sub, count=10, mode="practice")
    assert resp.status_code == 200
    data = resp.json()
    assert "durationSeconds" not in data  # timer omitted for practice
    for q in data["questions"]:
        assert ANSWER_KEYS <= q.keys(), "practice must include answers for feedback"


# ── exemplars-first selection ───────────────────────────────────────────────
async def _sources_of(ids: list[str]) -> list[str]:
    out = []
    for i in ids:
        q = await Question.get(i)
        out.append(q.source.value)
    return out


async def test_exemplars_consume_budget_first(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=12,
                    source=QuestionSource.exemplar)
    await make_many(course_id=course.id, subtopic_id=sub.id, n=10,
                    source=QuestionSource.generated)
    resp = await _start(client, course, sub, count=10)
    data = resp.json()
    assert data["count"] == 10
    sources = await _sources_of([q["id"] for q in data["questions"]])
    assert sources.count("exemplar") == 10
    assert sources.count("generated") == 0


async def test_generated_fill_remaining(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=6,
                    source=QuestionSource.exemplar)
    await make_many(course_id=course.id, subtopic_id=sub.id, n=10,
                    source=QuestionSource.generated)
    resp = await _start(client, course, sub, count=10)
    data = resp.json()
    sources = await _sources_of([q["id"] for q in data["questions"]])
    assert sources.count("exemplar") == 6
    assert sources.count("generated") == 4


async def test_serves_fewer_when_pool_small(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=3,
                    source=QuestionSource.exemplar)
    await make_many(course_id=course.id, subtopic_id=sub.id, n=5,
                    source=QuestionSource.generated)
    resp = await _start(client, course, sub, count=20)
    data = resp.json()
    assert data["count"] == 8  # all available, fewer than requested


async def test_unverified_and_other_subtopic_excluded(client):
    course, sub = await _course_and_subtopic()
    other_sub = await Subtopic.find(Subtopic.courseId == course.id).to_list()
    other = next(s for s in other_sub if s.id != sub.id)
    # 4 valid, plus noise that must be excluded.
    await make_many(course_id=course.id, subtopic_id=sub.id, n=4,
                    source=QuestionSource.exemplar)
    await make_question(course_id=course.id, subtopic_id=sub.id,
                        source=QuestionSource.generated, verified=False)
    await make_question(course_id=course.id, subtopic_id=other.id,
                        source=QuestionSource.exemplar, verified=True)
    resp = await _start(client, course, sub, count=10)
    assert resp.json()["count"] == 4


async def test_difficulty_filter(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=5,
                    source=QuestionSource.exemplar, difficulty=Difficulty.hard)
    await make_many(course_id=course.id, subtopic_id=sub.id, n=5,
                    source=QuestionSource.exemplar, difficulty=Difficulty.easy)
    resp = await _start(client, course, sub, count=10, difficulty="hard")
    data = resp.json()
    assert data["count"] == 5
    assert all(q["difficulty"] == "hard" for q in data["questions"])


# ── count caps ──────────────────────────────────────────────────────────────
async def test_subtopic_scope_rejects_50(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=5,
                    source=QuestionSource.exemplar)
    resp = await _start(client, course, sub, count=50)
    assert resp.status_code == 422


async def test_whole_course_scope_allows_50(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=12,
                    source=QuestionSource.exemplar)
    resp = await _start(client, course, None, count=50)  # whole-course
    assert resp.status_code == 200
    assert resp.json()["count"] == 12  # served what's available, cap satisfied


async def test_non_standard_count_rejected(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=20,
                    source=QuestionSource.exemplar)
    resp = await _start(client, course, sub, count=15)
    assert resp.status_code == 422


# ── empties / not-found ─────────────────────────────────────────────────────
async def test_no_questions_404(client):
    course, sub = await _course_and_subtopic()
    resp = await _start(client, course, sub, count=10)
    assert resp.status_code == 404


async def test_unknown_course_404(client):
    await seed_database()
    resp = await client.post(
        "/quiz/start",
        json={
            "courseId": "0123456789abcdef01234567",
            "count": 10,
            "difficulty": "medium",
            "mode": "exam",
        },
    )
    assert resp.status_code == 404


# ── scoring + review ────────────────────────────────────────────────────────
async def test_submit_scores_and_persists(client):
    course, sub = await _course_and_subtopic()
    # Known correct indices 0,1,2,3,0,1,2,3,0,1 via make_many (i % 4).
    await make_many(course_id=course.id, subtopic_id=sub.id, n=10,
                    source=QuestionSource.exemplar)
    start = await _start(client, course, sub, count=10, mode="exam")
    data = start.json()
    session_id = data["sessionId"]

    # Answer each with its own correctIndex (need the key — fetch from DB).
    answers = []
    for q in data["questions"]:
        doc = await Question.get(q["id"])
        answers.append(doc.correctIndex)
    # Make exactly one wrong.
    answers[0] = (answers[0] + 1) % 4

    resp = await client.post(f"/quiz/{session_id}/submit", json={"answers": answers})
    assert resp.status_code == 200
    result = resp.json()
    assert result["total"] == 10
    assert result["score"] == 9
    # Review includes full answer key + per-question correctness.
    assert all(ANSWER_KEYS <= q.keys() for q in result["questions"])
    assert sum(1 for q in result["questions"] if q["isCorrect"]) == 9

    from app.models.quiz_session import QuizSession
    session = await QuizSession.get(session_id)
    assert session.score == 9
    assert session.finishedAt is not None
    assert session.answers == answers


async def test_submit_handles_unanswered(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=10,
                    source=QuestionSource.exemplar)
    start = await _start(client, course, sub, count=10)
    session_id = start.json()["sessionId"]
    resp = await client.post(
        f"/quiz/{session_id}/submit", json={"answers": [None] * 10}
    )
    assert resp.status_code == 200
    assert resp.json()["score"] == 0


async def test_submit_answer_length_mismatch_422(client):
    course, sub = await _course_and_subtopic()
    await make_many(course_id=course.id, subtopic_id=sub.id, n=10,
                    source=QuestionSource.exemplar)
    start = await _start(client, course, sub, count=10)
    session_id = start.json()["sessionId"]
    resp = await client.post(f"/quiz/{session_id}/submit", json={"answers": [0, 1]})
    assert resp.status_code == 422


async def test_submit_unknown_session_404(client):
    await seed_database()
    resp = await client.post(
        "/quiz/0123456789abcdef01234567/submit", json={"answers": []}
    )
    assert resp.status_code == 404
