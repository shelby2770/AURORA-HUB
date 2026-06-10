"""Quiz request/response schemas.

`QuestionOut` carries optional answer fields. On the exam-start route they are
left unset and stripped via response_model_exclude_none, so the answer key is
physically absent from the payload during an exam. Practice-start populates
them for instant feedback. `source` is never exposed to the client.
"""
from __future__ import annotations

from enum import Enum

from beanie import PydanticObjectId
from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import Difficulty, QuizMode
from app.models.question import Question

# Counts always selectable; 50 is allowed only for whole-course scope.
BASE_COUNTS = {10, 20, 30, 40}
WHOLE_COURSE_EXTRA = {50}
SECONDS_PER_QUESTION = 90


class RequestDifficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    random = "random"

    def as_model_difficulty(self) -> Difficulty | None:
        """None means 'no difficulty filter' (random/mixed)."""
        if self is RequestDifficulty.random:
            return None
        return Difficulty(self.value)


class QuestionOut(BaseModel):
    id: PydanticObjectId
    courseId: PydanticObjectId
    subtopicId: PydanticObjectId
    difficulty: Difficulty
    questionText: str
    codeSnippet: str | None = None
    latex: str | None = None
    options: list[str]
    # Answer fields — present only when answers are allowed to be revealed.
    correctIndex: int | None = None
    explanation: str | None = None
    distractorRationales: list[str] | None = None

    @classmethod
    def from_question(cls, q: Question, *, include_answer: bool) -> "QuestionOut":
        return cls(
            id=q.id,
            courseId=q.courseId,
            subtopicId=q.subtopicId,
            difficulty=q.difficulty,
            questionText=q.questionText,
            codeSnippet=q.codeSnippet,
            latex=q.latex,
            options=q.options,
            correctIndex=q.correctIndex if include_answer else None,
            explanation=q.explanation if include_answer else None,
            distractorRationales=(
                q.distractorRationales if include_answer else None
            ),
        )


class QuizStartRequest(BaseModel):
    courseId: PydanticObjectId
    subtopicId: PydanticObjectId | None = None
    count: int
    difficulty: RequestDifficulty
    mode: QuizMode

    @model_validator(mode="after")
    def _validate_count_for_scope(self) -> "QuizStartRequest":
        whole_course = self.subtopicId is None
        allowed = BASE_COUNTS | (WHOLE_COURSE_EXTRA if whole_course else set())
        if self.count not in allowed:
            scope = "whole-course" if whole_course else "subtopic"
            raise ValueError(
                f"count {self.count} not allowed for {scope} scope; "
                f"allowed: {sorted(allowed)}"
            )
        return self


class QuizStartResponse(BaseModel):
    sessionId: PydanticObjectId
    mode: QuizMode
    difficulty: RequestDifficulty
    count: int  # actual number of questions served (may be < requested)
    durationSeconds: int | None = None  # exam timer; None for practice
    questions: list[QuestionOut]


class QuizSubmitRequest(BaseModel):
    answers: list[int | None]

    @field_validator("answers")
    @classmethod
    def _answers_in_range(cls, v: list[int | None]) -> list[int | None]:
        for a in v:
            if a is not None and not 0 <= a <= 3:
                raise ValueError("each answer must be 0..3 or null")
        return v


class QuestionReview(QuestionOut):
    selectedIndex: int | None = None
    isCorrect: bool = False


class QuizResultResponse(BaseModel):
    sessionId: PydanticObjectId
    mode: QuizMode
    score: int
    total: int
    questions: list[QuestionReview]
