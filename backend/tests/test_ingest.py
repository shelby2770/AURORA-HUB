"""Phase 4: exemplar ingestion pipeline (seeded DB + mock provider)."""
from __future__ import annotations

import json

from app.ingest.ingest import ingest_items
from app.ingest.sources import RawItem, from_text
from app.llm.mock import MockProvider
from app.models.course import Course, Subtopic
from app.models.enums import QuestionSource
from app.models.question import Question
from app.scripts.seed import seed_database


async def _slugs(db):
    await seed_database()
    course = await Course.find_one(Course.slug == "operating-systems")
    sub = await Subtopic.find_one(Subtopic.courseId == course.id)
    return course.slug, sub.slug


def _parsed(course_slug, sub_slug, *, correct, computable=False, code=None):
    return json.dumps(
        {
            "courseSlug": course_slug,
            "subtopicSlug": sub_slug,
            "difficulty": "medium",
            "questionText": "Compute the answer.",
            "options": ["0", "1", "2", "3"],
            "correctIndex": correct,
            "explanation": "because",
            "distractorRationales": ["", "", "", ""],
            "computable": computable,
            "verificationCode": code,
        }
    )


async def test_non_computable_is_trusted(db):
    course_slug, sub_slug = await _slugs(db)
    provider = MockProvider(responses=[_parsed(course_slug, sub_slug, correct=1)])
    report = await ingest_items([RawItem("q", "notes")], provider)
    assert report.inserted == 1
    assert report.flagged == []
    q = await Question.find_one(Question.source == QuestionSource.exemplar)
    assert q.verified is True
    assert q.verifiedBy == "ingest:trusted"


async def test_computable_match_is_exec_verified(db):
    course_slug, sub_slug = await _slugs(db)
    provider = MockProvider(
        responses=[_parsed(course_slug, sub_slug, correct=2, computable=True, code="correct_index = 2")]
    )
    report = await ingest_items([RawItem("q", "gate")], provider)
    assert report.inserted == 1
    assert report.verified == 1
    q = await Question.find_one(Question.source == QuestionSource.exemplar)
    assert q.verified is True
    assert q.verifiedBy == "ingest:exec"


async def test_computable_mismatch_is_flagged_and_held_back(db):
    course_slug, sub_slug = await _slugs(db)
    # Claims index 1, but the code computes 2 → dispute.
    provider = MockProvider(
        responses=[_parsed(course_slug, sub_slug, correct=1, computable=True, code="correct_index = 2")]
    )
    report = await ingest_items([RawItem("q", "gate")], provider)
    assert report.inserted == 1
    assert len(report.flagged) == 1
    assert report.flagged[0]["claimedIndex"] == 1
    assert report.flagged[0]["computedIndex"] == 2
    q = await Question.find_one(Question.source == QuestionSource.exemplar)
    assert q.verified is False  # held back from serving
    assert q.verifiedBy == "ingest:flagged"


async def test_unknown_subtopic_is_skipped(db):
    course_slug, _ = await _slugs(db)
    provider = MockProvider(responses=[_parsed(course_slug, "not-a-subtopic", correct=0)])
    report = await ingest_items([RawItem("q", "notes")], provider)
    assert report.inserted == 0
    assert len(report.skipped) == 1
    assert "unknown subtopic" in report.skipped[0]["reason"]


async def test_unparseable_item_is_skipped(db):
    await _slugs(db)
    provider = MockProvider(responses=["this is not JSON"])
    report = await ingest_items([RawItem("q", "notes")], provider)
    assert report.inserted == 0
    assert len(report.skipped) == 1
    assert report.skipped[0]["reason"].startswith("parse:")


def test_from_text_splits_on_delimiter():
    items = from_text("Q1 text\n---\nQ2 text\n---\n\n")
    assert [i.text for i in items] == ["Q1 text", "Q2 text"]
