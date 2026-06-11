"""Categorize + parse a raw exemplar item into the Question schema.

A cheap LLM call (thinking off) classifies the item into one of the 9 courses +
a subtopic slug from the controlled vocabulary, parses it into structured
fields, and — when the answer is computable — emits a runnable Python check
that recomputes the answer (used later for spot-verification).
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, field_validator

from app.llm.base import LLMProvider
from app.models.enums import Difficulty

PARSE_SYSTEM_PROMPT = """\
You are a careful exam-content parser for a CS MSc admission MCQ app.
You will be given the raw text of ONE multiple-choice question (a past-year
exam item or a study note). Convert it into a single JSON object — and nothing
else, no markdown fences, no prose.

Rules:
- Pick `courseSlug` from the ALLOWED COURSES and `subtopicSlug` from that
  course's ALLOWED SUBTOPICS. Never invent a slug.
- If the item belongs to NO allowed course — e.g. general aptitude, English,
  pure/engineering mathematics, discrete mathematics, digital logic, or compiler
  design (topics outside this app's scope) — set `courseSlug` to "none". The
  item will be dropped; still fill the other fields best-effort.
- `options` must be exactly 4 strings. `correctIndex` is 0-3.
- `difficulty` is one of easy|medium|hard (judge at university level).
- Put math/formal notation in `latex` (KaTeX) and any code in `codeSnippet`.
- `explanation` justifies the answer; `distractorRationales` has exactly 4
  strings (one per option) saying why each non-answer is wrong (use "" for the
  correct option's slot).
- Set `computable` true only if the answer can be checked by running code
  (page faults, complexity, code tracing, automata, SQL, arithmetic). If so,
  put in `verificationCode` self-contained Python that COMPUTES the answer and
  assigns the matching option index to a variable `correct_index` (0-3). Do not
  hard-code the answer — compute it. Otherwise set computable false and omit
  verificationCode.
- `examName`/`year` only if clearly present, else null.

Output JSON keys: courseSlug, subtopicSlug, difficulty, questionText,
codeSnippet, latex, options, correctIndex, explanation, distractorRationales,
examName, year, computable, verificationCode.
"""


class ParsedQuestion(BaseModel):
    courseSlug: str
    subtopicSlug: str | None = None  # null allowed when courseSlug == "none"
    difficulty: Difficulty
    questionText: str
    codeSnippet: str | None = None
    latex: str | None = None
    options: list[str]
    correctIndex: int
    explanation: str
    distractorRationales: list[str] = Field(default_factory=list)
    examName: str | None = None
    year: int | None = None
    computable: bool = False
    verificationCode: str | None = None

    @field_validator("options")
    @classmethod
    def _four_options(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError("options must have exactly 4 entries")
        return v

    @field_validator("correctIndex")
    @classmethod
    def _index_range(cls, v: int) -> int:
        if not 0 <= v <= 3:
            raise ValueError("correctIndex must be 0..3")
        return v


def extract_json(text: str) -> dict:
    """Pull the first balanced JSON object out of a model response."""
    text = text.strip()
    # Strip code fences if present.
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object in response")
    # Balance braces while ignoring any that appear inside string literals
    # (e.g. code with `{`/`}`), respecting escapes.
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                # strict=False tolerates literal control chars inside strings.
                return json.loads(text[start : i + 1], strict=False)
    raise ValueError("unterminated JSON object in response")


def _taxonomy_block(taxonomy: dict[str, list[str]]) -> str:
    lines = ["ALLOWED COURSES and SUBTOPICS:"]
    for course_slug, subs in taxonomy.items():
        lines.append(f"- {course_slug}: {', '.join(subs)}")
    return "\n".join(lines)


async def parse_item(
    provider: LLMProvider, raw_text: str, taxonomy: dict[str, list[str]]
) -> ParsedQuestion:
    prompt = f"{_taxonomy_block(taxonomy)}\n\nRAW ITEM:\n{raw_text}"
    out = await provider.complete(
        system=PARSE_SYSTEM_PROMPT, prompt=prompt, thinking=False, max_tokens=8000, json_mode=True
    )
    data = extract_json(out)
    return ParsedQuestion.model_validate(data)
