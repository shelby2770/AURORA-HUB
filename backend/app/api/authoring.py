"""Authoring plane endpoint: kick off offline question generation.

Async by design — generation is slow and must NEVER block a quiz. POST returns
202 with a jobId immediately and runs the pipeline in the background; poll the
job for the GenerationReport. Providers are injected via a dependency so tests
can supply mocks (the real ones need API keys).
"""
from __future__ import annotations

import math
import time
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

# On-demand fill tuning. Chunk kept small: one generation call must fit a
# complete JSON array in the model's output budget — ~5+ questions can overflow
# it and truncate. 3 is reliable and updates the progress bar more often.
FILL_CHUNK = 3            # questions generated per chunk / progress tick
FILL_TIME_BUDGET = 180    # seconds wall-clock cap for a fill job


class JobProgress(BaseModel):
    done: int      # questions now available toward the target (existing + generated)
    target: int    # requested total
    percent: int   # 0-100


async def _run_fill_job(
    job_id: str,
    *,
    subtopic_id: PydanticObjectId,
    difficulty: Difficulty,
    available: int,
    target: int,
    providers,
) -> None:
    """Generate questions in chunks until `target` is reached or a cap is hit.

    Progress is published to JOBS[job_id]['progress'] after every chunk so the
    client's bar advances. Distinguishes 'providers down' (error, nothing made)
    from 'low yield / partial' (done, started anyway).
    """
    generator, verifier, embedder = providers
    needed = target - available
    generated = 0
    max_chunks = math.ceil(needed / FILL_CHUNK) + 3  # headroom for sub-100% yield
    deadline = time.monotonic() + FILL_TIME_BUDGET

    def publish() -> None:
        done = available + generated
        JOBS[job_id]["progress"] = JobProgress(
            done=done, target=target,
            percent=min(100, round(done * 100 / target)) if target else 100,
        ).model_dump()

    publish()
    for _ in range(max_chunks):
        if generated >= needed or time.monotonic() >= deadline:
            break
        chunk_n = min(FILL_CHUNK, needed - generated)
        try:
            report = await generate_for(
                subtopic_id=subtopic_id,
                difficulty=difficulty,
                n=chunk_n,
                generator=generator,
                verifier=verifier,
                embedder=embedder,
            )
        except Exception as e:  # providers down, parse failure, etc.
            # Must never leave the job 'running' — always resolve to error/done.
            if generated == 0:
                JOBS[job_id] = {"status": "error", "error": str(e), "progress": JOBS[job_id].get("progress")}
                return
            break  # keep what we already generated
        generated += report.accepted
        publish()
        if report.accepted == 0:  # a full chunk yielded nothing new — stop early
            break

    JOBS[job_id]["status"] = "done"
    JOBS[job_id]["generated"] = generated


def start_fill_job(
    *,
    subtopic_id: PydanticObjectId,
    difficulty: Difficulty,
    available: int,
    target: int,
    providers,
    background: BackgroundTasks,
) -> str:
    """Register a running fill job and schedule it; returns the job id."""
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "running", "progress": None}
    background.add_task(
        _run_fill_job, job_id,
        subtopic_id=subtopic_id, difficulty=difficulty,
        available=available, target=target, providers=providers,
    )
    return job_id


def get_ondemand_providers() -> tuple[LLMProvider, LLMProvider, LLMProvider]:
    from app.llm.factory import get_ondemand_generator, get_ondemand_verifier

    return get_ondemand_generator(), get_ondemand_verifier(), get_embedder()


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
    progress: JobProgress | None = None
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
        progress=job.get("progress"),
        error=job.get("error"),
    )
