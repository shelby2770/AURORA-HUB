"""Phase 4: exemplar parser + JSON extraction (mock provider)."""
from __future__ import annotations

import json

import pytest

from app.ingest.parser import extract_json, parse_item
from app.llm.mock import MockProvider

SAMPLE = {
    "courseSlug": "operating-systems",
    "subtopicSlug": "cpu-scheduling",
    "difficulty": "medium",
    "questionText": "Which process runs next?",
    "options": ["P1", "P2", "P3", "P4"],
    "correctIndex": 1,
    "explanation": "Shortest job first.",
    "distractorRationales": ["longer", "", "longer", "longest"],
    "computable": False,
}


def test_extract_plain_json():
    assert extract_json(json.dumps(SAMPLE))["courseSlug"] == "operating-systems"


def test_extract_fenced_json():
    fenced = f"Here you go:\n```json\n{json.dumps(SAMPLE)}\n```\nthanks"
    assert extract_json(fenced)["correctIndex"] == 1


def test_extract_with_leading_prose():
    text = "Sure! " + json.dumps(SAMPLE)
    assert extract_json(text)["difficulty"] == "medium"


def test_extract_no_json_raises():
    with pytest.raises(ValueError):
        extract_json("there is no object here")


async def test_parse_item_builds_model():
    provider = MockProvider(responses=[json.dumps(SAMPLE)])
    taxonomy = {"operating-systems": ["cpu-scheduling", "paging"]}
    pq = await parse_item(provider, "raw question text", taxonomy)
    assert pq.courseSlug == "operating-systems"
    assert pq.subtopicSlug == "cpu-scheduling"
    assert len(pq.options) == 4
    assert pq.computable is False
    # taxonomy was injected into the prompt
    assert "cpu-scheduling" in provider.calls[0]["prompt"]


async def test_parse_item_rejects_bad_options():
    bad = {**SAMPLE, "options": ["only", "three", "here"]}
    provider = MockProvider(responses=[json.dumps(bad)])
    with pytest.raises(Exception):
        await parse_item(provider, "x", {"operating-systems": ["cpu-scheduling"]})
