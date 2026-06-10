"""Phase 1: seed idempotency + index presence."""
from __future__ import annotations

from app.models.course import Course, Subtopic
from app.models.question import Question
from app.scripts.seed import seed_database
from app.scripts.seed_data import SEED

EXPECTED_COURSES = len(SEED)
EXPECTED_SUBTOPICS = sum(len(v) for v in SEED.values())


async def test_seed_creates_all(db):
    result = await seed_database()
    assert result.courses_created == EXPECTED_COURSES
    assert result.subtopics_created == EXPECTED_SUBTOPICS

    assert await Course.find_all().count() == EXPECTED_COURSES
    assert await Subtopic.find_all().count() == EXPECTED_SUBTOPICS


async def test_seed_is_idempotent(db):
    first = await seed_database()
    second = await seed_database()

    # Second run creates nothing new.
    assert second.courses_created == 0
    assert second.subtopics_created == 0
    assert second.courses_existing == EXPECTED_COURSES
    assert second.subtopics_existing == EXPECTED_SUBTOPICS

    # Counts unchanged after a duplicate run.
    assert await Course.find_all().count() == first.courses_created
    assert await Subtopic.find_all().count() == first.subtopics_created


async def test_every_course_has_subtopics(db):
    await seed_database()
    for course in await Course.find_all().to_list():
        n = await Subtopic.find(Subtopic.courseId == course.id).count()
        assert n > 0, f"{course.name} has no subtopics"


async def test_indexes_present(db):
    # Beanie creates indexes on init_beanie (run by the `db` fixture).
    course_idx = await Course.get_pymongo_collection().index_information()
    assert any("slug" in name for name in course_idx)

    sub_idx = await Subtopic.get_pymongo_collection().index_information()
    assert any("courseId" in name and "slug" in name for name in sub_idx)

    q_idx = await Question.get_pymongo_collection().index_information()
    assert "serving_path" in q_idx


async def test_course_slug_unique(db):
    await seed_database()
    import pymongo.errors

    existing = await Course.find_one()
    raised = False
    try:
        await Course(name="Dup", slug=existing.slug).insert()
    except pymongo.errors.DuplicateKeyError:
        raised = True
    assert raised, "expected unique index to reject duplicate course slug"
