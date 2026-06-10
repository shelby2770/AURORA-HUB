"""Seed courses + subtopics. Idempotent: safe to run repeatedly.

Courses are upserted by `slug`; subtopics by `(courseId, slug)`. Re-running
never creates duplicates — it only fills in anything missing (and refreshes
the course display name).

Run as a script:  python -m app.scripts.seed
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.core.slug import slugify
from app.models.course import Course, Subtopic
from app.scripts.seed_data import SEED


@dataclass
class SeedResult:
    courses_created: int = 0
    courses_existing: int = 0
    subtopics_created: int = 0
    subtopics_existing: int = 0
    course_order: list[str] = field(default_factory=list)


async def seed_database(verbose: bool = False) -> SeedResult:
    """Upsert all seed courses and subtopics against already-initialized Beanie."""
    result = SeedResult()

    for course_name, subtopic_names in SEED.items():
        course_slug = slugify(course_name)
        course = await Course.find_one(Course.slug == course_slug)
        if course is None:
            course = await Course(
                name=course_name, slug=course_slug, isActive=True
            ).insert()
            result.courses_created += 1
            if verbose:
                print(f"  + course  {course_name}")
        else:
            result.courses_existing += 1

        for subtopic_name in subtopic_names:
            sub_slug = slugify(subtopic_name)
            existing = await Subtopic.find_one(
                Subtopic.courseId == course.id, Subtopic.slug == sub_slug
            )
            if existing is None:
                await Subtopic(
                    courseId=course.id, name=subtopic_name, slug=sub_slug
                ).insert()
                result.subtopics_created += 1
                if verbose:
                    print(f"      + subtopic  {subtopic_name}")
            else:
                result.subtopics_existing += 1

        result.course_order.append(course_slug)

    return result


async def _main() -> None:
    from app.core.db import close_db, init_db

    await init_db()
    result = await seed_database(verbose=True)
    print(
        f"\nSeed complete: "
        f"{result.courses_created} courses created "
        f"({result.courses_existing} existing), "
        f"{result.subtopics_created} subtopics created "
        f"({result.subtopics_existing} existing)."
    )
    await close_db()


if __name__ == "__main__":
    asyncio.run(_main())
