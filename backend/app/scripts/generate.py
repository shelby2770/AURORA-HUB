"""CLI: generate + verify + dedup new questions for a subtopic & difficulty.

Usage:
    python -m app.scripts.generate <course-slug> <subtopic-slug> <difficulty> <n>

Example:
    python -m app.scripts.generate operating-systems virtual-memory-page-replacement medium 10

Requires a seeded DB and provider keys in backend/.env.
"""
from __future__ import annotations

import asyncio
import sys

from app.core.db import close_db, init_db
from app.generate.pipeline import generate_for
from app.llm.factory import get_embedder, get_generator, get_verifier
from app.models.course import Course, Subtopic
from app.models.enums import Difficulty


async def _main(course_slug: str, subtopic_slug: str, difficulty: str, n: int) -> None:
    await init_db()
    course = await Course.find_one(Course.slug == course_slug)
    if course is None:
        print(f"Unknown course slug: {course_slug}")
        await close_db()
        return
    sub = await Subtopic.find_one(
        Subtopic.courseId == course.id, Subtopic.slug == subtopic_slug
    )
    if sub is None:
        print(f"Unknown subtopic slug for {course_slug}: {subtopic_slug}")
        await close_db()
        return

    report = await generate_for(
        subtopic_id=sub.id,
        difficulty=Difficulty(difficulty),
        n=n,
        generator=get_generator(),
        verifier=get_verifier(),
        embedder=get_embedder(),
    )
    print(
        f"\nGenerated for {course_slug}/{subtopic_slug} [{difficulty}]: "
        f"requested {report.requested}, parsed {report.parsed}, "
        f"accepted {report.accepted}. Discarded: {report.discarded or '{}'}"
    )
    await close_db()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("usage: python -m app.scripts.generate <course-slug> <subtopic-slug> <difficulty> <n>")
        raise SystemExit(2)
    asyncio.run(_main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])))
