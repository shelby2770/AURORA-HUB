"""In-process cosine dedup over embeddings stored in MongoDB.

No separate vector database. Atlas Vector Search could replace `is_duplicate`
behind the same call if the deployment later moves to Atlas.
"""
from __future__ import annotations

import math


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def max_similarity(embedding: list[float], corpus: list[list[float]]) -> float:
    return max((cosine(embedding, c) for c in corpus), default=0.0)


def is_duplicate(
    embedding: list[float], corpus: list[list[float]], threshold: float
) -> bool:
    """True if `embedding` is at/above the cosine threshold to any corpus item."""
    return max_similarity(embedding, corpus) >= threshold
