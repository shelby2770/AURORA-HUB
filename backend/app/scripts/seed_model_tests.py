"""Seed full-length model tests from JSON into MongoDB.

Each file under backend/data/model_tests/ mirrors the structure of
sample_model_test.json — a top-level `exam` block plus a `questions` array —
extended with the fields needed to grade and review a test: every question
carries a `subject`, an `answer` (option letter), and an `explanation`.

This script maps that sample shape onto the `ModelTest` document
(`question`->questionText, `code`->codeSnippet, `language`->codeLang,
`options{a..d}`->list, `answer` letter->correctIndex), validates the DU exam
constraints (50 questions, 150 marks, known subjects), and upserts by slug.
Idempotent: re-running refreshes existing tests in place.

Usage:  python -m app.scripts.seed_model_tests
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.slug import slugify
from app.models.model_test import ModelTest, ModelTestQuestion

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "model_tests"
LETTER_TO_INDEX = {"a": 0, "b": 1, "c": 2, "d": 3}

# The 12 Phase-1 subjects a DU CS model test draws from. A question's `subject`
# must be one of these (keeps the per-test distribution honest).
SUBJECTS = {
    "Mathematics",
    "Statistics",
    "Theory of Computation (TOC)",
    "Programming",
    "Data Structures & Algorithms (DSA)",
    "Computer Architecture",
    "Operating Systems (OS)",
    "Computer Networks",
    "Database Management Systems (DBMS)",
    "Distributed Systems",
    "Artificial Intelligence (AI)",
    "Analytical Ability",
}


def _build_question(i: int, raw: dict) -> ModelTestQuestion:
    opts = raw["options"]
    options = [opts["a"], opts["b"], opts["c"], opts["d"]]
    answer = str(raw["answer"]).strip().lower()
    if answer not in LETTER_TO_INDEX:
        raise ValueError(f"question {i}: answer '{raw['answer']}' must be a/b/c/d")
    subject = raw["subject"]
    if subject not in SUBJECTS:
        raise ValueError(f"question {i}: unknown subject '{subject}'")
    return ModelTestQuestion(
        number=raw.get("number", i),
        subject=subject,
        marks=raw.get("marks", 3),
        questionText=raw["question"],
        codeSnippet=raw.get("code"),
        codeLang=raw.get("language"),
        latex=raw.get("latex"),
        options=options,
        correctIndex=LETTER_TO_INDEX[answer],
        explanation=raw["explanation"],
    )


def _parse_file(path: Path, order: int) -> tuple[ModelTest, dict[str, int]]:
    doc = json.loads(path.read_text())
    exam = doc["exam"]
    questions = [_build_question(i + 1, q) for i, q in enumerate(doc["questions"])]

    title = exam.get("model_test") or exam.get("title") or path.stem
    slug = slugify(title)

    full_marks = exam.get("full_marks", 150)
    marks_per_q = exam.get("marks_per_question", 3)
    total = exam.get("total_questions", len(questions))

    # Validate DU exam constraints.
    problems: list[str] = []
    if len(questions) != total:
        problems.append(f"{len(questions)} questions, exam says {total}")
    marks_sum = sum(q.marks for q in questions)
    if marks_sum != full_marks:
        problems.append(f"marks sum {marks_sum} != full_marks {full_marks}")
    if problems:
        raise ValueError(f"{path.name}: " + "; ".join(problems))

    dist: dict[str, int] = {}
    for q in questions:
        dist[q.subject] = dist.get(q.subject, 0) + 1

    test = ModelTest(
        slug=slug,
        title=title,
        fullMarks=full_marks,
        timeMinutes=_minutes(exam.get("time", "90 minutes")),
        totalQuestions=total,
        marksPerQuestion=marks_per_q,
        passMarks=round(full_marks * 0.4),
        negativeMarking=exam.get("negative_marking", False),
        instructions=exam.get("instructions", []),
        questions=questions,
        order=order,
    )
    return test, dist


def _minutes(time_str: str) -> int:
    """Parse a '90 minutes' style string to an int; default 90."""
    digits = "".join(ch for ch in str(time_str) if ch.isdigit())
    return int(digits) if digits else 90


async def seed_model_tests(verbose: bool = False) -> tuple[int, int]:
    """Upsert every model test JSON by slug. Returns (created, updated)."""
    files = sorted(DATA_DIR.glob("*.json"))
    created = updated = 0

    for order, path in enumerate(files):
        test, dist = _parse_file(path, order)
        existing = await ModelTest.find_one(ModelTest.slug == test.slug)
        if existing is None:
            await test.insert()
            created += 1
            verb = "+"
        else:
            test.id = existing.id
            test.createdAt = existing.createdAt
            await test.save()
            updated += 1
            verb = "~"
        if verbose:
            dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(dist.items()))
            print(f"  {verb} {test.slug:16s} {len(test.questions)} Q  [{dist_str}]")

    return created, updated


async def _main() -> None:
    from app.core.db import close_db, init_db

    if not DATA_DIR.exists():
        print(f"No model-test data dir: {DATA_DIR}")
        raise SystemExit(2)

    await init_db()
    created, updated = await seed_model_tests(verbose=True)
    print(f"\nModel tests: {created} created, {updated} updated.")
    await close_db()


if __name__ == "__main__":
    asyncio.run(_main())
