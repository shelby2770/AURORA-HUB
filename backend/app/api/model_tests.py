"""Model Test serving endpoints: list, start a sitting, submit answers."""
from __future__ import annotations

from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException

from app.models.model_test import ModelTest, ModelTestSession
from app.schemas.model_test import (
    ModelTestQuestionOut,
    ModelTestQuestionReview,
    ModelTestResultResponse,
    ModelTestStartResponse,
    ModelTestSubmitRequest,
    ModelTestSummary,
)
from app.services.model_test import score_model_test

router = APIRouter(tags=["model-tests"], prefix="/model-tests")


@router.get("", response_model=list[ModelTestSummary])
async def list_model_tests() -> list[ModelTestSummary]:
    tests = await ModelTest.find(ModelTest.isActive == True).to_list()  # noqa: E712
    tests.sort(key=lambda t: (t.order, t.slug))
    return [ModelTestSummary.from_doc(t) for t in tests]


@router.post(
    "/{slug}/start",
    response_model=ModelTestStartResponse,
    response_model_exclude_none=True,
)
async def start_model_test(slug: str) -> ModelTestStartResponse:
    test = await ModelTest.find_one(ModelTest.slug == slug)
    if test is None or not test.isActive:
        raise HTTPException(status_code=404, detail="Model test not found")

    session = await ModelTestSession(modelTestId=test.id, answers=[]).insert()

    return ModelTestStartResponse(
        sessionId=session.id,
        slug=test.slug,
        title=test.title,
        durationSeconds=test.timeMinutes * 60,
        totalQuestions=test.totalQuestions,
        fullMarks=test.fullMarks,
        passMarks=test.passMarks,
        marksPerQuestion=test.marksPerQuestion,
        instructions=test.instructions,
        questions=[
            ModelTestQuestionOut.from_embedded(q, include_answer=False)
            for q in test.questions
        ],
    )


@router.post(
    "/sessions/{session_id}/submit", response_model=ModelTestResultResponse
)
async def submit_model_test(
    session_id: PydanticObjectId, req: ModelTestSubmitRequest
) -> ModelTestResultResponse:
    session = await ModelTestSession.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Model test session not found")

    test = await ModelTest.get(session.modelTestId)
    if test is None:
        raise HTTPException(status_code=404, detail="Model test not found")

    if len(req.answers) != len(test.questions):
        raise HTTPException(
            status_code=422,
            detail=(
                f"expected {len(test.questions)} answers, got {len(req.answers)}"
            ),
        )

    score, breakdown = score_model_test(test.questions, req.answers)
    marks = score * test.marksPerQuestion
    passed = marks >= test.passMarks

    session.answers = req.answers
    session.score = score
    session.marks = marks
    session.passed = passed
    session.finishedAt = datetime.now(timezone.utc)
    await session.save()

    reviews: list[ModelTestQuestionReview] = []
    for q, selected in zip(test.questions, req.answers):
        base = ModelTestQuestionOut.from_embedded(q, include_answer=True)
        reviews.append(
            ModelTestQuestionReview(
                **base.model_dump(),
                selectedIndex=selected,
                isCorrect=selected is not None and selected == q.correctIndex,
            )
        )

    return ModelTestResultResponse(
        sessionId=session.id,
        score=score,
        total=len(test.questions),
        marks=marks,
        fullMarks=test.fullMarks,
        passMarks=test.passMarks,
        passed=passed,
        subjectBreakdown=breakdown,
        questions=reviews,
    )
