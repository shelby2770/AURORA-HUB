"""Load hand-authored exemplar questions from a JSON file into MongoDB.

These are high-quality MCQs authored directly (not via the LLM generation
pipeline) and inserted as verified `exemplar` questions, so they serve first and
also act as few-shot anchors for any future generation.

Usage:
    python -m app.scripts.author_questions [path-to-json]

Defaults to backend/data/authored_questions.json. Idempotent: an item whose
exact questionText already exists in the same subtopic is skipped.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from app.core.db import close_db, init_db
from app.models.course import Course, Subtopic
from app.models.enums import Difficulty, QuestionSource
from app.models.question import Question

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "authored_questions.json"
VERIFIED_BY = "claude-opus-4-8"


async def load_authored(path: Path) -> tuple[int, int, list[str]]:
    items = json.loads(path.read_text())
    inserted = 0
    skipped = 0
    problems: list[str] = []

    # Cache course/subtopic lookups by slug.
    course_by_slug: dict[str, Course] = {}
    sub_by_key: dict[tuple[str, str], Subtopic] = {}

    for i, item in enumerate(items):
        cslug, sslug = item["course"], item["subtopic"]
        course = course_by_slug.get(cslug)
        if course is None:
            course = await Course.find_one(Course.slug == cslug)
            if course is None:
                problems.append(f"[{i}] unknown course slug: {cslug}")
                continue
            course_by_slug[cslug] = course

        sub = sub_by_key.get((cslug, sslug))
        if sub is None:
            sub = await Subtopic.find_one(
                Subtopic.courseId == course.id, Subtopic.slug == sslug
            )
            if sub is None:
                problems.append(f"[{i}] unknown subtopic {cslug}/{sslug}")
                continue
            sub_by_key[(cslug, sslug)] = sub

        text = item["questionText"]
        existing = await Question.find_one(
            Question.subtopicId == sub.id, Question.questionText == text
        )
        if existing is not None:
            skipped += 1
            continue

        try:
            q = Question(
                courseId=course.id,
                subtopicId=sub.id,
                difficulty=Difficulty(item["difficulty"]),
                questionText=text,
                codeSnippet=item.get("codeSnippet"),
                latex=item.get("latex"),
                options=item["options"],
                correctIndex=item["correctIndex"],
                explanation=item["explanation"],
                distractorRationales=item.get("distractorRationales", []),
                source=QuestionSource.exemplar,
                examName=item.get("examName"),
                year=item.get("year"),
                verified=True,
                verifiedBy=item.get("verifiedBy", VERIFIED_BY),
            )
            await q.insert()
            inserted += 1
        except Exception as e:  # validation or insert error — report, keep going
            problems.append(f"[{i}] {cslug}/{sslug}: {type(e).__name__}: {e}")

    return inserted, skipped, problems


async def _main(path: Path) -> None:
    if not path.exists():
        print(f"No such file: {path}")
        raise SystemExit(2)
    await init_db()
    inserted, skipped, problems = await load_authored(path)
    print(
        f"\nAuthored load complete: {inserted} inserted, {skipped} skipped "
        f"(already present), {len(problems)} problems."
    )
    for p in problems:
        print("  !", p)
    await close_db()


if __name__ == "__main__":
    arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    asyncio.run(_main(arg))
