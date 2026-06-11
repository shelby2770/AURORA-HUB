"""Authoring plane endpoint: kick off offline question generation.

Async by design — generation is slow and must NEVER block a quiz. POST returns
202 with a jobId immediately and runs the pipeline in the background; poll the
job for the GenerationReport. Providers are injected via a dependency so tests
can supply mocks (the real ones need API keys).
"""
from __future__ import annotations

import uuid

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app.generate.pipeline import GenerationReport, generate_for
from app.llm.base import LLMProvider
from app.llm.factory import get_embedder, get_generator, get_verifier
from app.models.course import Subtopic
from app.models.enums import Difficulty

router = APIRouter(tags=["authoring"], prefix="/authoring")

# In-memory job registry (single-user, single-process). A durable queue would
# replace this for multi-worker deployments.
JOBS: dict[str, dict] = {}


def get_authoring_providers() -> tuple[LLMProvider, LLMProvider, LLMProvider]:
    return get_generator(), get_verifier(), get_embedder()


class GenerateRequest(BaseModel):
    subtopicId: PydanticObjectId
    difficulty: Difficulty
    n: int

    @field_validator("n")
    @classmethod
    def _bounded(cls, v: int) -> int:
        if not 1 <= v <= 20:
            raise ValueError("n must be between 1 and 20")
        return v


class JobAccepted(BaseModel):
    jobId: str
    status: str


class JobStatus(BaseModel):
    jobId: str
    status: str  # running | done | error
    report: GenerationReport | None = None
    error: str | None = None


async def _run_job(job_id: str, req: GenerateRequest, providers) -> None:
    generator, verifier, embedder = providers
    try:
        report = await generate_for(
            subtopic_id=req.subtopicId,
            difficulty=req.difficulty,
            n=req.n,
            generator=generator,
            verifier=verifier,
            embedder=embedder,
        )
        JOBS[job_id] = {"status": "done", "report": report}
    except Exception as e:  # pragma: no cover - provider/runtime failures
        JOBS[job_id] = {"status": "error", "error": str(e)}


@router.post("/generate", response_model=JobAccepted, status_code=202)
async def start_generation(
    req: GenerateRequest,
    background: BackgroundTasks,
    providers=Depends(get_authoring_providers),
) -> JobAccepted:
    if await Subtopic.get(req.subtopicId) is None:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "running"}
    background.add_task(_run_job, job_id, req, providers)
    return JobAccepted(jobId=job_id, status="running")


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str) -> JobStatus:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(
        jobId=job_id,
        status=job["status"],
        report=job.get("report"),
        error=job.get("error"),
    )
