"""Shared enums for the data model."""
from __future__ import annotations

from enum import Enum


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuizMode(str, Enum):
    exam = "exam"
    practice = "practice"


class QuestionSource(str, Enum):
    exemplar = "exemplar"
    generated = "generated"
