"""Phase 5: pure units — dedup math, trivia guard, generation parsing."""
from __future__ import annotations

import json

from app.generate.dedup import cosine, is_duplicate, max_similarity
from app.generate.generator import (
    Difficulty,
    build_generation_prompt,
    extract_json_array,
    is_trivia,
    parse_generated,
)


def test_cosine_identity_and_orthogonal():
    assert cosine([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine([], [1.0]) == 0.0


def test_is_duplicate_threshold():
    corpus = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    assert is_duplicate([1.0, 0.0, 0.0], corpus, 0.92) is True
    assert is_duplicate([0.0, 0.0, 1.0], corpus, 0.92) is False
    assert round(max_similarity([1.0, 0.0, 0.0], corpus), 5) == 1.0


def test_trivia_guard():
    assert is_trivia("Who invented the TCP protocol?")
    assert is_trivia("In which year was UNIX released?")
    assert is_trivia("Dijkstra is known as the father of which field?")
    assert not is_trivia(
        "A FIFO buffer of size 3 receives the reference string 1 2 3 1; how many faults?"
    )


def test_parse_generated_skips_malformed():
    good = {
        "questionText": "Trace it",
        "options": ["a", "b", "c", "d"],
        "correctIndex": 1,
        "explanation": "x",
        "distractorRationales": ["", "", "", ""],
        "computable": False,
    }
    bad = {**good, "options": ["only", "two"]}  # invalid
    arr = json.dumps([good, bad, good])
    parsed = parse_generated(arr)
    assert len(parsed) == 2  # the malformed one is dropped


def test_extract_json_array_from_fence():
    arr = extract_json_array('```json\n[{"a": 1}]\n```')
    assert arr == [{"a": 1}]


def test_generation_prompt_contains_difficulty_and_count():
    prompt = build_generation_prompt(
        course_name="Operating Systems",
        subtopic_name="Page Replacement",
        difficulty=Difficulty.hard,
        n=7,
        exemplars=[],
    )
    assert "hard" in prompt
    assert "Write 7 NEW" in prompt
    assert "competitive-programming" in prompt
