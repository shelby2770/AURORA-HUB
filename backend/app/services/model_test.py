"""Model-test scoring: positional correctness + per-subject tally.

Questions are embedded in a fixed order on the test, so scoring is a plain
positional compare (mirrors `services.quiz.score_answers`), with an extra
subject-wise breakdown for the result screen. Subject order is preserved as it
first appears across the questions.
"""
from __future__ import annotations

from app.models.model_test import ModelTestQuestion
from app.schemas.model_test import SubjectScore


def score_model_test(
    questions: list[ModelTestQuestion], answers: list[int | None]
) -> tuple[int, list[SubjectScore]]:
    """Return (number correct, per-subject breakdown). `None` = unanswered."""
    score = 0
    order: list[str] = []
    correct: dict[str, int] = {}
    total: dict[str, int] = {}

    for q, a in zip(questions, answers):
        if q.subject not in total:
            order.append(q.subject)
            correct[q.subject] = 0
            total[q.subject] = 0
        total[q.subject] += 1
        if a is not None and a == q.correctIndex:
            score += 1
            correct[q.subject] += 1

    breakdown = [
        SubjectScore(subject=s, correct=correct[s], total=total[s]) for s in order
    ]
    return score, breakdown
