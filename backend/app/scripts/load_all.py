"""One-shot content load: seed taxonomy, then load every authored JSON file.

Loads, in order:
  1. Course + subtopic taxonomy (idempotent upsert).
  2. data/*.json                 — top-level authored/exemplar sets.
  3. data/gate_authored/*.json   — transcribed GATE PYQ sets.
  4. data/precomputed/*.json     — the hand-authored 20-per-subtopic bank.

Every file is loaded with the same idempotent `load_authored` used by
`author_questions.py` (skips an item whose exact questionText already exists in
its subtopic), so re-running is safe and only inserts what's new. Finishes with
a per-subtopic coverage report against the 20-per-subtopic target.

Usage:  python -m app.scripts.load_all
"""
from __future__ import annotations

import asyncio
import collections
from pathlib import Path

from app.core.db import close_db, init_db
from app.models.course import Course, Subtopic
from app.models.question import Question
from app.scripts.author_questions import load_authored
from app.scripts.seed import seed_database
from app.scripts.seed_model_tests import seed_model_tests

DATA = Path(__file__).resolve().parents[2] / "data"
TARGET_PER_SUBTOPIC = 20


def _data_files() -> list[Path]:
    files: list[Path] = sorted(DATA.glob("*.json"))
    files = [f for f in files if f.name != "taxonomy.json"]
    files += sorted((DATA / "gate_authored").glob("*.json"))
    files += sorted((DATA / "precomputed").glob("*.json"))
    return files


async def _coverage_report() -> None:
    courses = {c.id: c.slug async for c in Course.find_all()}
    subs = {s.id: (courses.get(s.courseId, "?"), s.slug) async for s in Subtopic.find_all()}
    counts: collections.Counter = collections.Counter()
    async for q in Question.find(Question.verified == True):  # noqa: E712
        counts[q.subtopicId] += 1

    by_course: dict[str, list[tuple[str, int]]] = collections.defaultdict(list)
    for sid, (cslug, sslug) in subs.items():
        by_course[cslug].append((sslug, counts.get(sid, 0)))

    short = 0
    print("\n=== Coverage (verified questions per subtopic, target 20) ===")
    for cslug in sorted(by_course):
        print(f"## {cslug}")
        for sslug, n in sorted(by_course[cslug]):
            ok = "OK" if n >= TARGET_PER_SUBTOPIC else f"need +{TARGET_PER_SUBTOPIC - n}"
            if n < TARGET_PER_SUBTOPIC:
                short += 1
            print(f"   {n:3d}  {sslug:45s} {ok}")
    total = sum(counts.values())
    print(f"\nTotal verified questions: {total}  |  subtopics below target: {short}")


async def _main() -> None:
    await init_db()
    seed = await seed_database()
    print(
        f"Seed: {seed.courses_created} courses / {seed.subtopics_created} subtopics created."
    )

    grand_ins = grand_skip = 0
    for path in _data_files():
        inserted, skipped, problems = await load_authored(path)
        grand_ins += inserted
        grand_skip += skipped
        tag = f"+{inserted} new, {skipped} dup"
        if problems:
            tag += f", {len(problems)} PROBLEMS"
        print(f"  {path.name:40s} {tag}")
        for p in problems:
            print("      !", p)

    print(f"\nLoaded: {grand_ins} inserted, {grand_skip} already present.")

    mt_created, mt_updated = await seed_model_tests()
    print(f"Model tests: {mt_created} created, {mt_updated} updated.")

    await _coverage_report()
    await close_db()


if __name__ == "__main__":
    asyncio.run(_main())
