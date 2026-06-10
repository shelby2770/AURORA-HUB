"""Question document — the unit served to the quiz runtime."""
from __future__ import annotations

from datetime import datetime, timezone

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field, field_validator

from app.models.enums import Difficulty, QuestionSource


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Question(Document):
    courseId: PydanticObjectId
    subtopicId: PydanticObjectId
    difficulty: Difficulty

    questionText: str
    codeSnippet: str | None = None
    latex: str | None = None

    options: list[str]
    correctIndex: int
    explanation: str
    distractorRationales: list[str] = Field(default_factory=list)

    source: QuestionSource
    examName: str | None = None
    year: int | None = None

    verified: bool = False
    verifiedBy: str | None = None

    embedding: list[float] | None = None
    createdAt: datetime = Field(default_factory=_utcnow)

    @field_validator("options")
    @classmethod
    def _four_options(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError("options must have exactly 4 entries")
        return v

    @field_validator("correctIndex")
    @classmethod
    def _index_in_range(cls, v: int) -> int:
        if not 0 <= v <= 3:
            raise ValueError("correctIndex must be 0..3")
        return v

    class Settings:
        name = "questions"
        indexes = [
            # Primary serving query path.
            pymongo.IndexModel(
                [
                    ("courseId", pymongo.ASCENDING),
                    ("subtopicId", pymongo.ASCENDING),
                    ("difficulty", pymongo.ASCENDING),
                    ("verified", pymongo.ASCENDING),
                    ("source", pymongo.ASCENDING),
                ],
                name="serving_path",
            ),
        ]
