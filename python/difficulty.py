"""Difficulty estimator based on text complexity and fact rarity."""
from __future__ import annotations

from analyzer import Fact

DIFFICULTY_LADDER = [
    "Kolay", "Normal", "Orta", "Zor", "Çok Zor",
    "Uzman", "Profesör", "Akademisyen", "Final",
]


def estimate_difficulty(fact: Fact) -> str:
    length = len(fact.raw)
    rarity = sum(1 for ch in fact.value if not ch.isascii())
    score = length // 40 + rarity
    idx = min(score, len(DIFFICULTY_LADDER) - 1)
    return DIFFICULTY_LADDER[idx]
