"""Model Test request/response schemas.

`ModelTestQuestionOut` carries optional answer fields. On the start route they
are left unset and stripped via `response_model_exclude_none`, so the answer key
is physically absent during the exam — exactly like the quiz exam-start path.
Submit re-includes them for the review screen.
"""
from __future__ import annotations

from beanie import PydanticObjectId
from pydantic import BaseModel, field_validator

from app.models.model_test import ModelTest, ModelTestQuestion


class ModelTestSummary(BaseModel):
    """List-view metadata; no questions."""

    slug: str
    title: str
    totalQuestions: int
    fullMarks: int
    timeMinutes: int
    marksPerQuestion: int
    passMarks: int

    @classmethod
    def from_doc(cls, t: ModelTest) -> "ModelTestSummary":
        return cls(
            slug=t.slug,
            title=t.title,
            totalQuestions=t.totalQuestions,
            fullMarks=t.fullMarks,
            timeMinutes=t.timeMinutes,
            marksPerQuestion=t.marksPerQuestion,
            passMarks=t.passMarks,
        )


class ModelTestQuestionOut(BaseModel):
    number: int
    subject: str
    marks: int
    questionText: str
    codeSnippet: str | None = None
    codeLang: str | None = None
    latex: str | None = None
    options: list[str]
    # Answer fields — present only when answers are allowed to be revealed.
    correctIndex: int | None = None
    explanation: str | None = None

    @classmethod
    def from_embedded(
        cls, q: ModelTestQuestion, *, include_answer: bool
    ) -> "ModelTestQuestionOut":
        return cls(
            number=q.number,
            subject=q.subject,
            marks=q.marks,
            questionText=q.questionText,
            codeSnippet=q.codeSnippet,
            codeLang=q.codeLang,
            latex=q.latex,
            options=q.options,
            correctIndex=q.correctIndex if include_answer else None,
            explanation=q.explanation if include_answer else None,
        )


class ModelTestStartResponse(BaseModel):
    sessionId: PydanticObjectId
    slug: str
    title: str
    durationSeconds: int  # timeMinutes * 60
    totalQuestions: int
    fullMarks: int
    passMarks: int
    marksPerQuestion: int
    instructions: list[str]
    questions: list[ModelTestQuestionOut]


class ModelTestSubmitRequest(BaseModel):
    answers: list[int | None]

    @field_validator("answers")
    @classmethod
    def _answers_in_range(cls, v: list[int | None]) -> list[int | None]:
        for a in v:
            if a is not None and not 0 <= a <= 3:
                raise ValueError("each answer must be 0..3 or null")
        return v


class ModelTestQuestionReview(ModelTestQuestionOut):
    selectedIndex: int | None = None
    isCorrect: bool = False


class SubjectScore(BaseModel):
    subject: str
    correct: int
    total: int


class ModelTestResultResponse(BaseModel):
    sessionId: PydanticObjectId
    score: int  # number of correct answers
    total: int  # number of questions
    marks: int  # score * marksPerQuestion
    fullMarks: int
    passMarks: int
    passed: bool
    subjectBreakdown: list[SubjectScore]
    questions: list[ModelTestQuestionReview]
