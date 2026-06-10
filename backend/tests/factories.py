"""Test helpers for inserting questions/courses directly."""
from __future__ import annotations

from beanie import PydanticObjectId

from app.models.enums import Difficulty, QuestionSource
from app.models.question import Question


async def make_question(
    *,
    course_id: PydanticObjectId,
    subtopic_id: PydanticObjectId,
    difficulty: Difficulty = Difficulty.medium,
    source: QuestionSource = QuestionSource.exemplar,
    verified: bool = True,
    correct_index: int = 0,
    text: str = "Sample question?",
) -> Question:
    return await Question(
        courseId=course_id,
        subtopicId=subtopic_id,
        difficulty=difficulty,
        questionText=text,
        options=["A", "B", "C", "D"],
        correctIndex=correct_index,
        explanation="Because.",
        distractorRationales=["w1", "w2", "w3", "w4"],
        source=source,
        verified=verified,
    ).insert()


async def make_many(
    *,
    course_id: PydanticObjectId,
    subtopic_id: PydanticObjectId,
    n: int,
    source: QuestionSource,
    difficulty: Difficulty = Difficulty.medium,
    verified: bool = True,
) -> list[Question]:
    out = []
    for i in range(n):
        out.append(
            await make_question(
                course_id=course_id,
                subtopic_id=subtopic_id,
                difficulty=difficulty,
                source=source,
                verified=verified,
                correct_index=i % 4,
                text=f"{source.value} Q{i}",
            )
        )
    return out
