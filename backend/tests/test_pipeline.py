"""Phase 5: generation pipeline (seeded DB + mock providers)."""
from __future__ import annotations

import json

from app.generate.pipeline import generate_for
from app.llm.mock import MockProvider
from app.models.course import Course, Subtopic
from app.models.enums import Difficulty, QuestionSource
from app.models.question import Question
from app.scripts.seed import seed_database
from tests.factories import make_question


def _cand(text, correct, *, computable=False, code=None):
    return {
        "questionText": text,
        "options": ["0", "1", "2", "3"],
        "correctIndex": correct,
        "explanation": "worked",
        "distractorRationales": ["", "", "", ""],
        "computable": computable,
        "verificationCode": code,
    }


async def _os_subtopic():
    await seed_database()
    course = await Course.find_one(Course.slug == "operating-systems")
    sub = await Subtopic.find_one(Subtopic.courseId == course.id)
    return course, sub


async def test_pipeline_accepts_verifies_and_discards(db):
    course, sub = await _os_subtopic()
    # An exemplar anchor in the subtopic.
    await make_question(
        course_id=course.id, subtopic_id=sub.id, source=QuestionSource.exemplar, text="anchor"
    )

    candidates = [
        _cand("Trace loop A", 2, computable=True, code="correct_index = 2"),  # exec match -> keep
        _cand("Trace loop B", 1, computable=True, code="correct_index = 3"),  # exec mismatch -> drop
        _cand("Scenario C reasoning", 0),  # crosscheck agree -> keep
        _cand("Scenario D reasoning", 0),  # crosscheck disagree -> drop
        _cand("Who invented paging?", 0),  # trivia -> drop
    ]
    generator = MockProvider(responses=[json.dumps(candidates)])
    # crosscheck called for the two non-computable items, in order: C then D.
    verifier = MockProvider(responses=['{"answer": 0}', '{"answer": 2}'])
    embedder = MockProvider()

    report = await generate_for(
        subtopic_id=sub.id,
        difficulty=Difficulty.medium,
        n=5,
        generator=generator,
        verifier=verifier,
        embedder=embedder,
    )

    assert report.parsed == 5
    assert report.accepted == 2
    assert report.discarded.get("exec_mismatch") == 1
    assert report.discarded.get("crosscheck_disagree") == 1
    assert report.discarded.get("trivia") == 1

    persisted = await Question.find(Question.source == QuestionSource.generated).to_list()
    assert len(persisted) == 2
    for q in persisted:
        assert q.verified is True
        assert q.embedding  # stored for future dedup
        assert q.verifiedBy in {"gen:exec", "gen:crosscheck"}


async def test_pipeline_rejects_near_duplicate(db):
    course, sub = await _os_subtopic()
    # Existing question; a candidate with identical text embeds identically
    # (mock hash embedding) -> cosine 1.0 -> duplicate.
    await make_question(
        course_id=course.id, subtopic_id=sub.id, source=QuestionSource.exemplar,
        text="Existing exemplar question",
    )
    candidate = _cand("Existing exemplar question", 2, computable=True, code="correct_index = 2")

    report = await generate_for(
        subtopic_id=sub.id,
        difficulty=Difficulty.medium,
        n=1,
        generator=MockProvider(responses=[json.dumps([candidate])]),
        verifier=MockProvider(),
        embedder=MockProvider(),
    )
    assert report.accepted == 0
    assert report.discarded.get("duplicate") == 1


async def test_pipeline_unknown_subtopic(db):
    await seed_database()
    from beanie import PydanticObjectId

    report = await generate_for(
        subtopic_id=PydanticObjectId(),
        difficulty=Difficulty.easy,
        n=3,
        generator=MockProvider(),
        verifier=MockProvider(),
        embedder=MockProvider(),
    )
    assert report.accepted == 0
    assert report.discarded.get("unknown_subtopic") == 1
