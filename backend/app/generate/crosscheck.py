"""Cold cross-check: a DIFFERENT model re-solves the MCQ with the answer hidden.

Used for non-computable (or unverifiable) generated items — keep only if the
independent solver lands on the same option the author claimed.
"""
from __future__ import annotations

from app.generate.generator import GeneratedQuestion
from app.ingest.parser import extract_json
from app.llm.base import LLMError, LLMProvider

CROSSCHECK_SYSTEM_PROMPT = """\
You are independently solving ONE multiple-choice question. Reason it through,
then respond with ONLY a JSON object {"answer": <index 0-3>} naming the single
correct option. No prose, no explanation, no fences.
"""


def _question_block(q: GeneratedQuestion) -> str:
    parts = [q.questionText]
    if q.codeSnippet:
        parts.append(f"\nCode:\n{q.codeSnippet}")
    if q.latex:
        parts.append(f"\nMath: {q.latex}")
    for i, opt in enumerate(q.options):
        parts.append(f"{i}. {opt}")
    return "\n".join(parts)


async def cross_check(provider: LLMProvider, q: GeneratedQuestion) -> int | None:
    """Return the index the independent solver chose, or None if unparseable."""
    try:
        out = await provider.complete(
            system=CROSSCHECK_SYSTEM_PROMPT,
            prompt=_question_block(q),
            thinking=True,
            max_tokens=4000,
        )
    except LLMError:
        return None
    try:
        answer = int(extract_json(out)["answer"])
    except (ValueError, KeyError, TypeError):
        return None
    return answer if 0 <= answer <= 3 else None
