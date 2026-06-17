"""Database initialization. Registers Beanie document models.

Beanie 2.x runs on PyMongo's native async driver (AsyncMongoClient); Motor is
EOL and no longer used. `init_db` accepts an optional client so tests can
inject one pointed at an ephemeral mongod.
"""
from __future__ import annotations

from pymongo import AsyncMongoClient

from beanie import init_beanie

from app.core.config import settings
from app.models.course import Course, Subtopic
from app.models.model_test import ModelTest, ModelTestSession
from app.models.question import Question
from app.models.quiz_session import QuizSession
from app.models.visit import Visit

DOCUMENT_MODELS = [
    Course,
    Subtopic,
    Question,
    QuizSession,
    Visit,
    ModelTest,
    ModelTestSession,
]

_client: AsyncMongoClient | None = None


async def init_db(
    client: AsyncMongoClient | None = None, db_name: str | None = None
) -> None:
    global _client
    if client is None:
        client = AsyncMongoClient(settings.mongodb_uri)
    _client = client
    database = client[db_name or settings.mongodb_db]
    await init_beanie(database=database, document_models=DOCUMENT_MODELS)


async def close_db() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
