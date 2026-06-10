"""Source adapters for exemplar ingestion.

Default to LOCAL content the user provides — files on disk or pasted text. No
URL fetching is implemented; if it is ever added, it must respect robots.txt
and the source's terms (official GATE CS papers, the user's own notes, etc.).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DELIMITER = "\n---\n"


@dataclass
class RawItem:
    text: str
    source_name: str


def from_text(text: str, *, source_name: str = "pasted", delimiter: str = DEFAULT_DELIMITER) -> list[RawItem]:
    """Split pasted text into items on a delimiter (default a `---` line)."""
    blocks = [b.strip() for b in text.split(delimiter)]
    return [RawItem(text=b, source_name=source_name) for b in blocks if b]


def from_file(path: str | Path, *, delimiter: str = DEFAULT_DELIMITER) -> list[RawItem]:
    """Read one local file. `.json` may be a list of strings or `{text}` objects;
    `.txt`/`.md` are split on the delimiter."""
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        data = json.loads(content)
        items: list[RawItem] = []
        for entry in data:
            text = entry if isinstance(entry, str) else entry.get("text", "")
            if text.strip():
                items.append(RawItem(text=text.strip(), source_name=p.name))
        return items
    return from_text(content, source_name=p.name, delimiter=delimiter)


def from_paths(paths: list[str | Path], *, delimiter: str = DEFAULT_DELIMITER) -> list[RawItem]:
    items: list[RawItem] = []
    for path in paths:
        p = Path(path)
        if p.is_dir():
            for child in sorted(p.iterdir()):
                if child.suffix.lower() in {".txt", ".md", ".json"}:
                    items.extend(from_file(child, delimiter=delimiter))
        else:
            items.extend(from_file(p, delimiter=delimiter))
    return items
