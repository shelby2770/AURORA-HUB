"""On-demand fill: chunked generation job, provider fallback, dedup degrade."""
from __future__ import annotations

import json

from app.api.authoring import JOBS, _run_fill_job
from app.generate.pipeline import generate_for
from app.llm.base import LLMError, LLMProvider
from app.llm.fallback import FallbackProvider
from app.llm.mock import MockProvider
from app.models.course import Course, Subtopic
from app.models.enums import Difficulty, QuestionSource
from app.models.question import Question
from app.scripts.seed import seed_database


async def _os_subtopic():
    await seed_database()
    course = await Course.find_one(Course.slug == "operating-systems")
    sub = await Subtopic.find_one(Subtopic.courseId == course.id)
    return course, sub


def _computable_batch_fn(size: int = 5):
    """Generator complete_fn returning `size` unique, exec-verifiable candidates
    per call (unique text avoids dedup; computable avoids any verifier call)."""
    counter = {"i": 0}

    def fn(system: str, prompt: str) -> str:
        items = []
        for _ in range(size):
            i = counter["i"]
            counter["i"] += 1
            idx = i % 4
            items.append({
                "questionText": f"Generated scenario number {i}",
                "options": ["0", "1", "2", "3"],
                "correctIndex": idx,
                "explanation": "worked",
                "distractorRationales": ["", "", "", ""],
                "computable": True,
                "verificationCode": f"correct_index = {idx}",
            })
        return json.dumps(items)

    return fn


class _DownProvider(LLMProvider):
    name = "down"

    async def complete(self, **kwargs) -> str:
        raise LLMError("quota exhausted")

    async def embed(self, texts):
        raise LLMError("no embeddings")


async def test_fill_job_reaches_target_in_chunks(db):
    _, sub = await _os_subtopic()
    generator = MockProvider(complete_fn=_computable_batch_fn(5))
    providers = (generator, MockProvider(), MockProvider())

    job_id = "job-reach"
    JOBS[job_id] = {"status": "running", "progress": None}
    await _run_fill_job(
        job_id, subtopic_id=sub.id, difficulty=Difficulty.medium,
        available=0, target=10, providers=providers,
    )

    assert JOBS[job_id]["status"] == "done"
    assert JOBS[job_id]["generated"] >= 10
    assert JOBS[job_id]["progress"]["percent"] == 100
    persisted = await Question.find(Question.source == QuestionSource.generated).count()
    assert persisted >= 10


async def test_generate_degrades_to_lexical_dedup_without_embeddings(db):
    _, sub = await _os_subtopic()
    candidates = [
        {"questionText": f"Distinct scenario {k}", "options": ["0", "1", "2", "3"],
         "correctIndex": 1, "explanation": "x", "distractorRationales": ["", "", "", ""],
         "computable": True, "verificationCode": "correct_index = 1"}
        for k in range(3)
    ]
    generator = MockProvider(responses=[json.dumps(candidates)])

    report = await generate_for(
        subtopic_id=sub.id, difficulty=Difficulty.medium, n=3,
        generator=generator, verifier=MockProvider(), embedder=_DownProvider(),
    )

    assert report.accepted == 3  # embeddings failed but lexical dedup let them through
    persisted = await Question.find(Question.source == QuestionSource.generated).to_list()
    assert len(persisted) == 3
    assert all(q.embedding is None for q in persisted)  # inserted without embedding


async def test_fallback_provider_uses_second_when_first_fails():
    fb = FallbackProvider([_DownProvider(), MockProvider(responses=["ok"])])
    out = await fb.complete(system="s", prompt="p", thinking=True)
    assert out == "ok"
    assert fb.last_used == "mock"


async def test_fill_job_errors_when_all_providers_down(db):
    _, sub = await _os_subtopic()
    dead = FallbackProvider([_DownProvider(), _DownProvider()])
    providers = (dead, MockProvider(), MockProvider())

    job_id = "job-down"
    JOBS[job_id] = {"status": "running", "progress": None}
    await _run_fill_job(
        job_id, subtopic_id=sub.id, difficulty=Difficulty.medium,
        available=0, target=10, providers=providers,
    )
    assert JOBS[job_id]["status"] == "error"
    assert "quota" in JOBS[job_id]["error"]
