"""Authoring generation pipeline: anchor -> generate -> dedup -> verify -> persist.

Offline / async only. Survivors are persisted source=generated, verified=true
with their embedding stored in Mongo so future runs dedup against them.
"""
from __future__ import annotations

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.core.config import settings
from app.generate.crosscheck import cross_check
from app.generate.dedup import is_duplicate
from app.generate.generator import (
    GENERATION_SYSTEM_PROMPT,
    GeneratedQuestion,
    build_generation_prompt,
    is_trivia,
    parse_generated,
)
from app.llm.base import LLMProvider
from app.models.course import Course, Subtopic
from app.models.enums import Difficulty, QuestionSource
from app.models.question import Question
from app.verify.check import Verdict, verify_computable

_ANCHOR_LIMIT = 3


class GenerationReport(BaseModel):
    requested: int = 0
    parsed: int = 0
    accepted: int = 0
    acceptedIds: list[str] = Field(default_factory=list)
    discarded: dict[str, int] = Field(default_factory=dict)

    def _drop(self, reason: str) -> None:
        self.discarded[reason] = self.discarded.get(reason, 0) + 1


async def _anchors(course_id: PydanticObjectId, subtopic_id: PydanticObjectId, difficulty: Difficulty) -> list[Question]:
    """2-3 exemplars tagged to the subtopic (difficulty first), plain query."""
    matched = await Question.find(
        Question.subtopicId == subtopic_id,
        Question.source == QuestionSource.exemplar,
        Question.verified == True,  # noqa: E712
        Question.difficulty == difficulty,
    ).limit(_ANCHOR_LIMIT).to_list()
    if len(matched) >= 2:
        return matched
    extra = await Question.find(
        Question.subtopicId == subtopic_id,
        Question.source == QuestionSource.exemplar,
        Question.verified == True,  # noqa: E712
    ).limit(_ANCHOR_LIMIT).to_list()
    seen = {q.id for q in matched}
    return (matched + [q for q in extra if q.id not in seen])[:_ANCHOR_LIMIT]


async def _dedup_corpus(
    subtopic_id: PydanticObjectId, embedder: LLMProvider
) -> list[list[float]]:
    """Embeddings of all verified questions in the subtopic (exemplars +
    generated). Backfills + persists embeddings missing on exemplars."""
    corpus: list[list[float]] = []
    questions = await Question.find(
        Question.subtopicId == subtopic_id,
        Question.verified == True,  # noqa: E712
    ).to_list()
    for q in questions:
        if q.embedding:
            corpus.append(q.embedding)
        else:
            vec = (await embedder.embed([q.questionText]))[0]
            q.embedding = vec
            await q.save()
            corpus.append(vec)
    return corpus


async def _verify(
    cand: GeneratedQuestion, verifier: LLMProvider
) -> tuple[bool, str]:
    """Return (kept, verifiedBy). Computable -> execute; else/unverifiable ->
    cold cross-check with a different model."""
    if cand.computable:
        verdict, _ = verify_computable(cand.verificationCode, cand.correctIndex)
        if verdict is Verdict.match:
            return True, "gen:exec"
        if verdict is Verdict.mismatch:
            return False, "exec_mismatch"
        # unverifiable -> fall through to cross-check
    chosen = await cross_check(verifier, cand)
    if chosen is None:
        return False, "crosscheck_failed"
    if chosen != cand.correctIndex:
        return False, "crosscheck_disagree"
    return True, "gen:crosscheck"


async def generate_for(
    *,
    subtopic_id: PydanticObjectId,
    difficulty: Difficulty,
    n: int,
    generator: LLMProvider,
    verifier: LLMProvider,
    embedder: LLMProvider,
    threshold: float | None = None,
) -> GenerationReport:
    threshold = settings.dedup_similarity_threshold if threshold is None else threshold
    report = GenerationReport(requested=n)

    sub = await Subtopic.get(subtopic_id)
    if sub is None:
        report._drop("unknown_subtopic")
        return report
    course = await Course.get(sub.courseId)

    anchors = await _anchors(sub.courseId, subtopic_id, difficulty)
    corpus = await _dedup_corpus(subtopic_id, embedder)

    prompt = build_generation_prompt(
        course_name=course.name if course else "",
        subtopic_name=sub.name,
        difficulty=difficulty,
        n=n,
        exemplars=anchors,
    )
    raw = await generator.complete(
        system=GENERATION_SYSTEM_PROMPT, prompt=prompt, thinking=True
    )
    candidates = parse_generated(raw)
    report.parsed = len(candidates)

    accepted_embeddings: list[list[float]] = []
    for cand in candidates:
        if is_trivia(cand.questionText):
            report._drop("trivia")
            continue

        embedding = (await embedder.embed([cand.questionText]))[0]
        if is_duplicate(embedding, corpus + accepted_embeddings, threshold):
            report._drop("duplicate")
            continue

        kept, tag = await _verify(cand, verifier)
        if not kept:
            report._drop(tag)
            continue

        q = await Question(
            courseId=sub.courseId,
            subtopicId=subtopic_id,
            difficulty=difficulty,
            questionText=cand.questionText,
            codeSnippet=cand.codeSnippet,
            latex=cand.latex,
            options=cand.options,
            correctIndex=cand.correctIndex,
            explanation=cand.explanation,
            distractorRationales=cand.distractorRationales,
            source=QuestionSource.generated,
            verified=True,
            verifiedBy=tag,
            embedding=embedding,
        ).insert()
        accepted_embeddings.append(embedding)
        report.accepted += 1
        report.acceptedIds.append(str(q.id))

    return report
