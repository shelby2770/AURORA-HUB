"""Exemplar ingestion pipeline (authoring plane, offline).

For each provided item: categorize+parse to the Question schema, resolve the
course/subtopic against the seeded taxonomy, and — for computable items — run
the model's check through the SAME execution sandbox used for generated
questions. Exemplars are treated as high-quality but NOT infallible: a key that
the execution DISAGREES with is FLAGGED (stored verified=False, held back from
serving) for the user's review rather than trusted blindly.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from beanie import PydanticObjectId

from app.ingest.parser import ParsedQuestion, parse_item
from app.ingest.sources import RawItem
from app.llm.base import LLMProvider
from app.models.course import Course, Subtopic
from app.models.enums import QuestionSource
from app.models.question import Question
from app.verify.check import Verdict, verify_computable


@dataclass
class IngestReport:
    inserted: int = 0
    flagged: list[dict] = field(default_factory=list)  # key disputed by execution
    skipped: list[dict] = field(default_factory=list)  # parse/resolve failures
    verified: int = 0
    unverifiable: int = 0


async def load_taxonomy() -> tuple[dict[str, list[str]], dict[str, Course], dict[tuple[PydanticObjectId, str], Subtopic]]:
    """Return (course_slug -> [subtopic_slug], course-by-slug, subtopic-by-(courseId,slug))."""
    taxonomy: dict[str, list[str]] = {}
    by_course: dict[str, Course] = {}
    by_sub: dict[tuple[PydanticObjectId, str], Subtopic] = {}
    for course in await Course.find_all().to_list():
        by_course[course.slug] = course
        subs = await Subtopic.find(Subtopic.courseId == course.id).to_list()
        taxonomy[course.slug] = [s.slug for s in subs]
        for s in subs:
            by_sub[(course.id, s.slug)] = s
    return taxonomy, by_course, by_sub


async def _persist(pq: ParsedQuestion, course: Course, sub: Subtopic, *, verified: bool, verified_by: str) -> None:
    await Question(
        courseId=course.id,
        subtopicId=sub.id,
        difficulty=pq.difficulty,
        questionText=pq.questionText,
        codeSnippet=pq.codeSnippet,
        latex=pq.latex,
        options=pq.options,
        correctIndex=pq.correctIndex,
        explanation=pq.explanation,
        distractorRationales=pq.distractorRationales,
        source=QuestionSource.exemplar,
        examName=pq.examName,
        year=pq.year,
        verified=verified,
        verifiedBy=verified_by,
    ).insert()


async def ingest_items(
    items: list[RawItem],
    provider: LLMProvider,
    *,
    run_sandbox: bool = True,
) -> IngestReport:
    taxonomy, by_course, by_sub = await load_taxonomy()
    report = IngestReport()

    for item in items:
        try:
            pq = await parse_item(provider, item.text, taxonomy)
        except Exception as e:
            report.skipped.append({"source": item.source_name, "reason": f"parse: {e}"})
            continue

        if pq.courseSlug == "none":
            report.skipped.append({"source": item.source_name, "reason": "out-of-scope (courseSlug=none)"})
            continue

        course = by_course.get(pq.courseSlug)
        if course is None:
            report.skipped.append({"source": item.source_name, "reason": f"unknown course '{pq.courseSlug}'"})
            continue
        sub = by_sub.get((course.id, pq.subtopicSlug))
        if sub is None:
            report.skipped.append(
                {"source": item.source_name, "reason": f"unknown subtopic '{pq.subtopicSlug}' for {pq.courseSlug}"}
            )
            continue

        verified, verified_by = True, "ingest:trusted"
        if pq.computable and run_sandbox:
            verdict, result = verify_computable(pq.verificationCode, pq.correctIndex)
            if verdict is Verdict.mismatch:
                verified, verified_by = False, "ingest:flagged"
                report.flagged.append(
                    {
                        "source": item.source_name,
                        "questionText": pq.questionText[:160],
                        "claimedIndex": pq.correctIndex,
                        "computedIndex": result.value if result else None,
                    }
                )
            elif verdict is Verdict.match:
                verified_by = "ingest:exec"
                report.verified += 1
            else:  # unverifiable
                verified_by = "ingest:exec-unverifiable"
                report.unverifiable += 1

        await _persist(pq, course, sub, verified=verified, verified_by=verified_by)
        report.inserted += 1

    return report
