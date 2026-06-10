"""Course / Subtopic response schemas."""
from __future__ import annotations

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict

from app.models.course import Course, Subtopic


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PydanticObjectId
    name: str
    slug: str
    isActive: bool

    @classmethod
    def from_doc(cls, c: Course) -> "CourseOut":
        return cls.model_validate(c)


class SubtopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PydanticObjectId
    courseId: PydanticObjectId
    name: str
    slug: str

    @classmethod
    def from_doc(cls, s: Subtopic) -> "SubtopicOut":
        return cls.model_validate(s)
