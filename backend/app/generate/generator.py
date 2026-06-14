"""Few-shot anchored question generation: prompts, parsing, trivia guard."""
from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, field_validator

from app.models.enums import Difficulty
from app.models.question import Question

DIFFICULTY_GUIDANCE = {
    Difficulty.easy: (
        "core concept APPLICATION (never definition trivia) — a small scenario "
        "the student resolves by applying one idea correctly."
    ),
    Difficulty.medium: (
        "short code traces, page-fault / normalization / complexity "
        "calculations — a few deliberate steps with a single correct result."
    ),
    Difficulty.hard: (
        "rigorous scenario / algorithmic reasoning; for DSA & Programming, "
        "approach competitive-programming depth."
    ),
}

GENERATION_SYSTEM_PROMPT = """\
You author NEW university-level CS multiple-choice questions for Dhaka
University MSc admission prep. Think step by step and show your working before
committing to an answer.

ABSOLUTE RULES:
- NO TRIVIA. Forbidden: "who invented", "what year", "who coined", "father of",
  and any recall-of-names/dates question. Every item must be scenario-,
  code/trace-, or computation-based and solvable by reasoning.
- Create genuinely NEW questions that test the SAME CONCEPTS as the provided
  exemplars — not reworded copies with swapped numbers, not paraphrases.
- Exactly 4 options; exactly one correct. Put math in `latex` (KaTeX) and code
  in `codeSnippet`.
- Include a worked `explanation` and `distractorRationales`: exactly 4 strings,
  a one-line reason each non-answer is wrong ("" for the correct option).
- If the answer is computable (page faults, complexity, code tracing, automata,
  SQL, arithmetic), set `computable` true and put in `verificationCode`
  self-contained Python that COMPUTES the answer and assigns the matching
  option index to a variable `correct_index` (0-3). Do not hard-code it —
  compute it. Otherwise set computable false and omit verificationCode.

Output ONLY a JSON array (no prose, no fences) of objects with keys:
questionText, codeSnippet, latex, options, correctIndex, explanation,
distractorRationales, computable, verificationCode.
"""

# Defense-in-depth: reject any item that slips past the prompt as trivia.
_TRIVIA_PATTERNS = [
    r"\bwho\s+(invented|coined|created|discovered|developed|proposed)\b",
    r"\bwhat\s+year\b",
    r"\bin\s+which\s+year\b",
    r"\bfather\s+of\b",
    r"\bwho\s+is\s+(known\s+as|called)\b",
    r"\bnamed\s+after\b",
]
_TRIVIA_RE = re.compile("|".join(_TRIVIA_PATTERNS), re.IGNORECASE)


def is_trivia(text: str) -> bool:
    return bool(_TRIVIA_RE.search(text or ""))


class GeneratedQuestion(BaseModel):
    questionText: str
    codeSnippet: str | None = None
    latex: str | None = None
    options: list[str]
    correctIndex: int
    explanation: str
    distractorRationales: list[str] = Field(default_factory=list)
    computable: bool = False
    verificationCode: str | None = None

    @field_validator("options")
    @classmethod
    def _four(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError("options must have exactly 4 entries")
        return v

    @field_validator("correctIndex")
    @classmethod
    def _range(cls, v: int) -> int:
        if not 0 <= v <= 3:
            raise ValueError("correctIndex must be 0..3")
        return v


def _exemplar_block(exemplars: list[Question]) -> str:
    if not exemplars:
        return "(no exemplars available — match the caliber of a GATE CS paper)"
    out = []
    for i, q in enumerate(exemplars, 1):
        parts = [f"Exemplar {i}: {q.questionText}"]
        if q.codeSnippet:
            parts.append(f"Code:\n{q.codeSnippet}")
        if q.latex:
            parts.append(f"Math: {q.latex}")
        parts.append("Options: " + " | ".join(q.options))
        out.append("\n".join(parts))
    return "\n\n".join(out)


def build_generation_prompt(
    *,
    course_name: str,
    subtopic_name: str,
    difficulty: Difficulty,
    n: int,
    exemplars: list[Question],
) -> str:
    return (
        f"Course: {course_name}\nSubtopic: {subtopic_name}\n"
        f"Target difficulty: {difficulty.value} — {DIFFICULTY_GUIDANCE[difficulty]}\n\n"
        f"Style/caliber anchors (test the same CONCEPTS, do not copy):\n"
        f"{_exemplar_block(exemplars)}\n\n"
        f"Write {n} NEW {difficulty.value} questions as a JSON array."
    )


def extract_json_array(text: str) -> list:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    if start == -1:
        raise ValueError("no JSON array in response")
    # Balance brackets while ignoring any inside string literals (e.g. code or
    # math containing `[`/`]`), respecting escapes; strict=False tolerates raw
    # control chars inside strings.
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
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1], strict=False)
    raise ValueError("unterminated JSON array in response")


def parse_generated(text: str) -> list[GeneratedQuestion]:
    out: list[GeneratedQuestion] = []
    for entry in extract_json_array(text):
        try:
            out.append(GeneratedQuestion.model_validate(entry))
        except Exception:
            continue  # skip malformed items, keep the good ones
    return out
