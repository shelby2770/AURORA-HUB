"""CLI: ingest provided exemplars (local files / dirs) into MongoDB.

Usage:
    python -m app.scripts.ingest_exemplars <path> [<path> ...]

Each path is a file (.txt/.md/.json) or a directory of them. Items are
categorized + parsed by the configured cheap LLM, computable ones are
spot-verified by execution, and key mismatches are flagged for review.
Requires the database to be seeded first (`python -m app.scripts.seed`).
"""
from __future__ import annotations

import asyncio
import sys

from app.core.db import close_db, init_db
from app.ingest.ingest import ingest_items
from app.ingest.sources import from_paths
from app.llm.factory import get_generator


async def _main(paths: list[str]) -> None:
    items = from_paths(paths)
    if not items:
        print("No items found in the given paths.")
        return

    await init_db()
    # Parsing is the "cheap" call; reuse the generator provider (thinking off).
    provider = get_generator()
    report = await ingest_items(items, provider)

    print(
        f"\nIngest complete: {report.inserted} inserted "
        f"({report.verified} exec-verified, {report.unverifiable} unverifiable, "
        f"{len(report.flagged)} FLAGGED), {len(report.skipped)} skipped."
    )
    if report.flagged:
        print("\nFLAGGED for review (key disputed by execution):")
        for f in report.flagged:
            print(f"  - [{f['source']}] claimed {f['claimedIndex']} vs computed {f['computedIndex']}: {f['questionText']}")
    if report.skipped:
        print("\nSkipped:")
        for s in report.skipped:
            print(f"  - [{s['source']}] {s['reason']}")

    await close_db()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m app.scripts.ingest_exemplars <path> [<path> ...]")
        raise SystemExit(2)
    asyncio.run(_main(sys.argv[1:]))
