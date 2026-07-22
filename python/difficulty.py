"""Difficulty estimation — thin shim kept for backward compatibility.
The real logic now lives in analyzer.estimate_difficulty().
"""
from __future__ import annotations

from analyzer import Fact, estimate_difficulty  # noqa: F401 – re-exported

DIFFICULTY_LADDER = [
    "Kolay", "Normal", "Orta", "Zor", "Çok Zor",
    "Uzman", "Profesör", "Akademisyen", "Final",
]
