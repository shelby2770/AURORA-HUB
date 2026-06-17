"""Model Test documents — a full-length DU-style mock exam.

A `ModelTest` is a curated, fixed set of 50 MCQs (3 marks each, 150 total,
90 minutes, 60-mark / 40% pass) spanning the 12 Phase-1 subjects. Unlike the
subtopic question bank, the questions are embedded directly on the test in a
fixed order, so a "session" only needs to remember the answers.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelTestQuestion(BaseModel):
    """One embedded MCQ inside a model test (always carries its answer key)."""

    number: int
    subject: str
    marks: int = 3

    questionText: str
    codeSnippet: str | None = None
    codeLang: str | None = None  # shiki lang hint: c | cpp | java | ...
    latex: str | None = None

    options: list[str]
    correctIndex: int
    explanation: str

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


class ModelTest(Document):
    slug: str
    title: str

    fullMarks: int = 150
    timeMinutes: int = 90
    totalQuestions: int = 50
    marksPerQuestion: int = 3
    passMarks: int = 60  # 40% of 150
    negativeMarking: bool = False
    instructions: list[str] = Field(default_factory=list)

    questions: list[ModelTestQuestion]
    order: int = 0  # display order in the list
    isActive: bool = True
    createdAt: datetime = Field(default_factory=_utcnow)

    class Settings:
        name = "model_tests"
        indexes = [
            pymongo.IndexModel([("slug", pymongo.ASCENDING)], unique=True),
        ]


class ModelTestSession(Document):
    """One sitting of a model test. Scored positionally against the test's
    fixed question order, so we only store the picked answers + the result."""

    modelTestId: PydanticObjectId
    answers: list[int | None] = Field(default_factory=list)
    score: int | None = None  # number of correct answers
    marks: int | None = None  # score * marksPerQuestion
    passed: bool | None = None
    startedAt: datetime = Field(default_factory=_utcnow)
    finishedAt: datetime | None = None

    class Settings:
        name = "model_test_sessions"
