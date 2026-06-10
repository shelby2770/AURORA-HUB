"""QuizSession document — one taken quiz."""
from __future__ import annotations

from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

from app.models.enums import Difficulty, QuizMode


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class QuizScope(BaseModel):
    courseId: PydanticObjectId
    subtopicId: PydanticObjectId | None = None


class QuizSession(Document):
    mode: QuizMode
    scope: QuizScope
    difficulty: Difficulty | None = None  # None == random/mixed
    questionIds: list[PydanticObjectId] = Field(default_factory=list)
    answers: list[int | None] = Field(default_factory=list)
    score: int | None = None
    startedAt: datetime = Field(default_factory=_utcnow)
    finishedAt: datetime | None = None
    userId: PydanticObjectId | None = None  # reserved for later multi-user

    class Settings:
        name = "quiz_sessions"
