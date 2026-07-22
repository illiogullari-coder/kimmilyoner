"""Exporter: merges generated questions with the existing pool and writes JSON."""
from __future__ import annotations

import json
from pathlib import Path


def load_existing(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def merge(existing: list[dict], new_items: list[dict]) -> list[dict]:
    """Add new items that don't already exist. Never removes existing questions."""
    seen: set[str] = {item.get("hash", "") for item in existing}
    merged = list(existing)
    for item in new_items:
        h = item.get("hash", "")
        if h and h not in seen:
            seen.add(h)
            merged.append(item)
    return merged


def export(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
