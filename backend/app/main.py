"""Aurora Hub FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.authoring import router as authoring_router
from app.api.courses import router as courses_router
from app.api.health import router as health_router
from app.api.quiz import router as quiz_router
from app.core.config import settings
from app.core.db import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(title="Aurora Hub API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(courses_router)
    app.include_router(quiz_router)
    app.include_router(authoring_router)
    return app


app = create_app()
