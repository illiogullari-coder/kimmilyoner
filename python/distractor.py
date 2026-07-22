"""Distractor generator: produces plausible wrong answers from the same category."""
from __future__ import annotations

import random


def generate_distractors(correct: str, category_pool: list[str], count: int = 3) -> list[str]:
    pool = [p for p in category_pool if p != correct and p.strip()]
    random.shuffle(pool)
    distractors = pool[:count]
    while len(distractors) < count:
        placeholder = f"Bilinmeyen {len(distractors)+1}"
        if placeholder not in distractors:
            distractors.append(placeholder)
    return distractors
