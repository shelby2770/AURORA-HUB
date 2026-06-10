"""Phase 0: model round-trip + validation tests."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.course import Course, Subtopic
from app.models.enums import Difficulty, QuestionSource, QuizMode
from app.models.question import Question
from app.models.quiz_session import QuizScope, QuizSession


async def test_course_subtopic_question_roundtrip(db):
    course = await Course(name="Operating Systems", slug="operating-systems").insert()
    sub = await Subtopic(
        courseId=course.id, name="Memory Management", slug="memory-management"
    ).insert()

    q = await Question(
        courseId=course.id,
        subtopicId=sub.id,
        difficulty=Difficulty.medium,
        questionText="A system uses FIFO page replacement...",
        options=["3", "4", "5", "6"],
        correctIndex=2,
        explanation="Count page faults across the reference string.",
        distractorRationales=["off by one", "wrong policy", "", "miscount"],
        source=QuestionSource.exemplar,
        examName="GATE CS",
        year=2018,
        verified=True,
        verifiedBy="ingest",
    ).insert()

    fetched = await Question.get(q.id)
    assert fetched is not None
    assert fetched.correctIndex == 2
    assert fetched.source == QuestionSource.exemplar
    assert fetched.difficulty == Difficulty.medium
    assert len(fetched.options) == 4


async def test_quiz_session_roundtrip(db):
    course = await Course(name="DBMS", slug="dbms").insert()
    session = await QuizSession(
        mode=QuizMode.exam,
        scope=QuizScope(courseId=course.id),
        difficulty=Difficulty.hard,
        questionIds=[],
        answers=[],
    ).insert()

    fetched = await QuizSession.get(session.id)
    assert fetched is not None
    assert fetched.mode == QuizMode.exam
    assert fetched.userId is None  # reserved for later multi-user


def test_question_requires_four_options():
    with pytest.raises(ValidationError):
        Question(
            courseId="000000000000000000000000",
            subtopicId="000000000000000000000000",
            difficulty=Difficulty.easy,
            questionText="bad",
            options=["a", "b", "c"],  # only 3
            correctIndex=0,
            explanation="x",
            source=QuestionSource.generated,
        )


def test_question_correct_index_bounds():
    with pytest.raises(ValidationError):
        Question(
            courseId="000000000000000000000000",
            subtopicId="000000000000000000000000",
            difficulty=Difficulty.easy,
            questionText="bad",
            options=["a", "b", "c", "d"],
            correctIndex=4,  # out of range
            explanation="x",
            source=QuestionSource.generated,
        )
