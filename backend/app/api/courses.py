"""Course + subtopic listing endpoints (serving plane)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.course import Course, Subtopic
from app.schemas.course import CourseOut, SubtopicOut

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=list[CourseOut])
async def list_courses() -> list[CourseOut]:
    courses = await Course.find(Course.isActive == True).to_list()  # noqa: E712
    return [CourseOut.from_doc(c) for c in courses]


@router.get("/courses/{slug}/subtopics", response_model=list[SubtopicOut])
async def list_subtopics(slug: str) -> list[SubtopicOut]:
    course = await Course.find_one(Course.slug == slug)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course '{slug}' not found")
    subs = await Subtopic.find(Subtopic.courseId == course.id).to_list()
    return [SubtopicOut.from_doc(s) for s in subs]
