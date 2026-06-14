"""One-shot live demo: generate a single MCQ via the on-demand fallback path.

Calls the REAL Gemini→Groq fallback generator (same one /quiz/fill uses), with
no database — just prompt → LLM → parse → print. Run from backend/:

    python -m scripts.demo_generate_one [subtopic] [difficulty]
"""
from __future__ import annotations

import asyncio
import json
import sys

from app.generate.generator import (
    GENERATION_SYSTEM_PROMPT,
    build_generation_prompt,
    parse_generated,
)
from app.llm.factory import get_ondemand_generator
from app.models.enums import Difficulty


async def main() -> None:
    subtopic = sys.argv[1] if len(sys.argv) > 1 else "Disk Scheduling"
    diff = Difficulty(sys.argv[2]) if len(sys.argv) > 2 else Difficulty.medium

    gen = get_ondemand_generator()
    prompt = build_generation_prompt(
        course_name="Operating Systems",
        subtopic_name=subtopic,
        difficulty=diff,
        n=1,
        exemplars=[],
    )
    print(f"→ Generating 1 {diff.value} MCQ on '{subtopic}' …", flush=True)
    raw = await gen.complete(
        system=GENERATION_SYSTEM_PROMPT,
        prompt=prompt,
        thinking=True,
        json_mode=True,
        max_tokens=16000,
    )
    print(f"✓ Provider used: {getattr(gen, 'last_used', '?')}\n", flush=True)

    items = parse_generated(raw)
    if not items:
        print("✗ Parse failed. Raw output:\n", raw[:2000])
        return
    q = items[0]
    print("=" * 70)
    print(q.questionText)
    if q.codeSnippet:
        print("\nCode:\n" + q.codeSnippet)
    if q.latex:
        print("\nMath: " + q.latex)
    print()
    for i, opt in enumerate(q.options):
        mark = "   <-- correct" if i == q.correctIndex else ""
        print(f"  {chr(65 + i)}. {opt}{mark}")
    print("\nExplanation: " + q.explanation)
    if q.distractorRationales:
        print("\nWhy the others are wrong:")
        for i, r in enumerate(q.distractorRationales):
            if r:
                print(f"  {chr(65 + i)}: {r}")
    print("=" * 70)
    if q.computable and q.verificationCode:
        print("\n(model marked this computable; verifier would re-solve via:)")
        print(q.verificationCode)


if __name__ == "__main__":
    asyncio.run(main())
