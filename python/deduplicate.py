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


def levenshtein(a: str, b: str) -> int:
    """Classic edit-distance DP. O(len(a)*len(b)) — fine for short quiz questions."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def similarity_ratio(a: str, b: str) -> float:
    """1.0 = identical, 0.0 = completely different (normalized edit distance)."""
    a, b = normalize(a), normalize(b)
    longest = max(len(a), len(b), 1)
    return 1 - (levenshtein(a, b) / longest)


def filter_near_duplicates(items: list[dict], threshold: float = 0.92) -> list[dict]:
    """Removes questions that are near-identical (paraphrases, punctuation-only
    variants) to one already accepted, even when their SHA-256 hashes differ.
    Runs after filter_unique(); O(n^2) so only sensible on the newly-fetched
    batch, not the whole historical pool (see generate_questions.py)."""
    accepted: list[dict] = []
    for item in items:
        text = item.get("question", "")
        is_dup = any(similarity_ratio(text, a.get("question", "")) >= threshold for a in accepted)
        if not is_dup:
            accepted.append(item)
    return accepted


def filter_against_existing(
    new_items: list[dict], existing: list[dict], threshold: float = 0.92
) -> list[dict]:
    """Yeni üretilen soruları, mevcut havuzdaki *aynı kategorideki* sorularla
    karşılaştırıp yakın-kopyaları eler. Tüm havuzla O(n²) karşılaştırma
    yapmak yerine kategoriye göre bölerek (bucket) maliyeti düşürür — havuz
    büyüse bile her kategori bucket'ı makul boyutta kalır."""
    by_category: dict[str, list[str]] = {}
    for ex in existing:
        by_category.setdefault(ex.get("category", ""), []).append(ex.get("question", ""))

    kept: list[dict] = []
    for item in new_items:
        cat = item.get("category", "")
        text = item.get("question", "")
        existing_texts = by_category.get(cat, [])
        is_dup = any(similarity_ratio(text, ex_text) >= threshold for ex_text in existing_texts)
        if not is_dup:
            kept.append(item)
    return kept
