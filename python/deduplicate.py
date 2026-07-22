"""Deduplication via SHA-256 hashing of normalized question text."""
from __future__ import annotations

import hashlib
import re


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def question_hash(question: str, correct: str) -> str:
    key = normalize(question) + "|" + normalize(correct)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def filter_unique(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        h = item.get("hash", "")
        if not h:
            continue
        if h in seen:
            continue
        seen.add(h)
        unique.append(item)
    return unique
