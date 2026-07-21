"""Main question generation orchestrator.

Runs the full pipeline: fetch encyclopedic Turkish content, analyze,
generate distractors, estimate difficulty, deduplicate, export.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from analyzer import classify_topic, extract_facts
from deduplicate import filter_unique, question_hash
from difficulty import estimate_difficulty
from distractor import generate_distractors
from exporter import export, load_existing, merge
from source_fetcher import clean_text, fetch_article, fetch_raw_titles

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "questions.json"
SEED_TOPICS = [
    "Türkiye", "Ankara", "İstanbul", "Atatürk", "Osmanlı İmparatorluğu",
    "Kurtuluş Savaşı", "Galatasaray", "Nemrut Dağı", "Pamukkale",
    "Van Gölü", "Kızılırmak", "Kapadokya",
]
CATEGORY_POOL = [
    "Ankara", "İstanbul", "İzmir", "Bursa", "Antalya", "Konya", "Edirne",
    "Samsun", "Trabzon", "Erzurum", "Diyarbakır", "Gaziantep",
]


def build_question(fact, category: str, difficulty: str) -> dict | None:
    if not fact.value or len(fact.value) < 2:
        return None
    question_text = f"{fact.subject} ile ilgili: {fact.predicate}?"
    correct = fact.value
    distractors = generate_distractors(correct, CATEGORY_POOL, 3)
    if len(set(distractors)) < 3:
        return None
    return {
        "id": f"gen-{random.randint(100000, 999999)}",
        "hash": question_hash(question_text, correct),
        "category": category,
        "difficulty": difficulty,
        "question": question_text,
        "correctAnswer": correct,
        "distractors": distractors,
    }


def main() -> int:
    seed = random.randint(1, 100000)
    titles = fetch_raw_titles(seed) + SEED_TOPICS
    generated: list[dict] = []
    for title in titles[:30]:
        raw = fetch_article(title)
        text = clean_text(raw)
        if not text:
            continue
        category = classify_topic(text)
        facts = extract_facts(text, subject=title)
        for fact in facts:
            difficulty = estimate_difficulty(fact)
            q = build_question(fact, category, difficulty)
            if q:
                generated.append(q)
    unique = filter_unique(generated)
    existing = load_existing(OUTPUT)
    merged = merge(existing, unique)
    export(OUTPUT, merged)
    print(f"Generated {len(unique)} new questions. Total: {len(merged)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
