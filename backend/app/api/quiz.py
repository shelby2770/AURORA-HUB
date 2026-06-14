"""Quiz serving endpoints: start a session and submit answers."""
from __future__ import annotations

from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.api.authoring import get_ondemand_providers, start_fill_job
from app.models.course import Course, Subtopic
from app.models.enums import QuizMode
from app.models.question import Question
from app.models.quiz_session import QuizScope, QuizSession
from app.schemas.quiz import (
    SECONDS_PER_QUESTION,
    QuestionOut,
    QuestionReview,
    QuizFillRequest,
    QuizFillResponse,
    QuizResultResponse,
    QuizStartRequest,
    QuizStartResponse,
    QuizSubmitRequest,
)
from app.services.quiz import (
    count_available,
    order_questions_by_ids,
    score_answers,
    select_questions,
)

router = APIRouter(tags=["quiz"], prefix="/quiz")


@router.post("/fill", response_model=QuizFillResponse)
async def fill_quiz(
    req: QuizFillRequest, background: BackgroundTasks
) -> QuizFillResponse:
    """Pre-flight before starting: is the verified pool big enough, and if not
    (for a subtopic), launch on-demand generation. Whole-course requests are
    always 'ready' (they serve whatever exists, never generating)."""
    course = await Course.get(req.courseId)
    if course is None or not course.isActive:
        raise HTTPException(status_code=404, detail="Course not found")

    model_difficulty = req.difficulty.as_model_difficulty()
    available = await count_available(req.courseId, req.subtopicId, model_difficulty)

    if req.subtopicId is None or available >= req.count:
        return QuizFillResponse(ready=True, available=available, target=req.count)

    subtopic = await Subtopic.get(req.subtopicId)
    if subtopic is None or subtopic.courseId != req.courseId:
        raise HTTPException(status_code=404, detail="Subtopic not found for this course")

    job_id = start_fill_job(
        subtopic_id=req.subtopicId,
        difficulty=req.generation_difficulty(),
        available=available,
        target=req.count,
        providers=get_ondemand_providers(),
        background=background,
    )
    return QuizFillResponse(
        ready=False, available=available, target=req.count, jobId=job_id
    )


@router.post("/start", response_model=QuizStartResponse, response_model_exclude_none=True)
async def start_quiz(req: QuizStartRequest) -> QuizStartResponse:
    course = await Course.get(req.courseId)
    if course is None or not course.isActive:
        raise HTTPException(status_code=404, detail="Course not found")

    if req.subtopicId is not None:
        subtopic = await Subtopic.get(req.subtopicId)
        if subtopic is None or subtopic.courseId != req.courseId:
            raise HTTPException(
                status_code=404, detail="Subtopic not found for this course"
            )

    model_difficulty = req.difficulty.as_model_difficulty()
    selected = await select_questions(
        course_id=req.courseId,
        subtopic_id=req.subtopicId,
        difficulty=model_difficulty,
        count=req.count,
    )
    if not selected:
        raise HTTPException(
            status_code=404,
            detail="No verified questions available for this scope/difficulty",
        )

    session = await QuizSession(
        mode=req.mode,
        scope=QuizScope(courseId=req.courseId, subtopicId=req.subtopicId),
        difficulty=model_difficulty,
        questionIds=[q.id for q in selected],
        answers=[],
    ).insert()

    include_answer = req.mode == QuizMode.practice
    served = len(selected)
    return QuizStartResponse(
        sessionId=session.id,
        mode=req.mode,
        difficulty=req.difficulty,
        count=served,
        durationSeconds=(
            SECONDS_PER_QUESTION * served if req.mode == QuizMode.exam else None
        ),
        questions=[
            QuestionOut.from_question(q, include_answer=include_answer)
            for q in selected
        ],
    )


@router.post("/{session_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    session_id: PydanticObjectId, req: QuizSubmitRequest
) -> QuizResultResponse:
    session = await QuizSession.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    if len(req.answers) != len(session.questionIds):
        raise HTTPException(
            status_code=422,
            detail=(
                f"expected {len(session.questionIds)} answers, "
                f"got {len(req.answers)}"
            ),
        )

    fetched = await Question.find(
        {"_id": {"$in": session.questionIds}}
    ).to_list()
    questions = order_questions_by_ids(fetched, session.questionIds)

    score = score_answers(questions, req.answers)

    session.answers = req.answers
    session.score = score
    session.finishedAt = datetime.now(timezone.utc)
    await session.save()

    reviews: list[QuestionReview] = []
    for q, selected in zip(questions, req.answers):
        base = QuestionOut.from_question(q, include_answer=True)
        reviews.append(
            QuestionReview(
                **base.model_dump(),
                selectedIndex=selected,
                isCorrect=selected is not None and selected == q.correctIndex,
            )
        )

    return QuizResultResponse(
        sessionId=session.id,
        mode=session.mode,
        score=score,
        total=len(questions),
        questions=reviews,
    )
