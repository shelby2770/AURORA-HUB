"""Course + Subtopic documents."""
from __future__ import annotations

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field


class Course(Document):
    name: str
    slug: str
    isActive: bool = True

    class Settings:
        name = "courses"
        indexes = [
            pymongo.IndexModel([("slug", pymongo.ASCENDING)], unique=True),
        ]


class Subtopic(Document):
    courseId: PydanticObjectId
    name: str
    slug: str

    class Settings:
        name = "subtopics"
        indexes = [
            pymongo.IndexModel(
                [("courseId", pymongo.ASCENDING), ("slug", pymongo.ASCENDING)],
                unique=True,
            ),
        ]
