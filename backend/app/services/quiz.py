"""Serving-plane quiz logic: question selection + scoring.

Selection is the hot path: a plain Mongo read of verified questions, exemplars
prioritized to fill the requested count, generated questions filling any
remainder. No LLM, no vector search. Random sampling gives quiz-to-quiz
variety; exemplar-first *counts* stay deterministic.
"""
from __future__ import annotations

import random

from beanie import PydanticObjectId

from app.models.enums import Difficulty, QuestionSource
from app.models.question import Question


def _base_match(
    course_id: PydanticObjectId,
    subtopic_id: PydanticObjectId | None,
    difficulty: Difficulty | None,
) -> dict:
    match: dict = {"courseId": course_id, "verified": True}
    if subtopic_id is not None:
        match["subtopicId"] = subtopic_id
    if difficulty is not None:
        match["difficulty"] = difficulty.value
    return match


async def _sample(match: dict, size: int) -> list[Question]:
    if size <= 0:
        return []
    pipeline = [{"$match": match}, {"$sample": {"size": size}}]
    return await Question.aggregate(
        pipeline, projection_model=Question
    ).to_list()


async def select_questions(
    *,
    course_id: PydanticObjectId,
    subtopic_id: PydanticObjectId | None,
    difficulty: Difficulty | None,
    count: int,
) -> list[Question]:
    """Pick up to `count` verified questions, exemplars first, then generated.

    The returned list is shuffled so exemplar/generated items are not grouped.
    May return fewer than `count` when not enough verified questions exist.
    """
    base = _base_match(course_id, subtopic_id, difficulty)

    exemplars = await _sample({**base, "source": QuestionSource.exemplar.value}, count)
    remaining = count - len(exemplars)
    generated = await _sample(
        {**base, "source": QuestionSource.generated.value}, remaining
    )

    selected = exemplars + generated
    random.shuffle(selected)
    return selected


def score_answers(
    questions: list[Question], answers: list[int | None]
) -> int:
    """Count answers matching the correct index (None = unanswered)."""
    return sum(
        1
        for q, a in zip(questions, answers)
        if a is not None and a == q.correctIndex
    )


def order_questions_by_ids(
    questions: list[Question], ids: list[PydanticObjectId]
) -> list[Question]:
    """Reorder a fetched batch to match the stored session order."""
    by_id = {q.id: q for q in questions}
    return [by_id[i] for i in ids if i in by_id]
