"""Text analyzer: extracts key facts and candidate statements from raw encyclopedic text."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Fact:
    subject: str
    predicate: str
    value: str
    raw: str


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def extract_facts(text: str, subject: str = "") -> list[Fact]:
    facts: list[Fact] = []
    for sentence in split_sentences(text):
        if "=" in sentence or "bir" in sentence.lower():
            value = _find_value(sentence)
            if value:
                facts.append(Fact(subject=subject, predicate=sentence[:60], value=value, raw=sentence))
        if re.search(r"\b(19|20)\d{2}\b", sentence):
            year = re.search(r"\b(19|20)\d{2}\b", sentence)
            facts.append(Fact(subject=subject, predicate="yıl", value=year.group(0), raw=sentence))
    return facts


def _find_value(sentence: str) -> str:
    match = re.search(r":\s*([^,;.]+)", sentence)
    if match:
        return match.group(1).strip()
    return ""


def classify_topic(text: str) -> str:
    lowered = text.lower()
    keywords = {
        "Osmanlı Devleti": ["osmanlı", "padişah", "sultan", "devlet-i aliyye"],
        "Türkiye Cumhuriyeti": ["cumhuriyet", "cumhurbaşkanı", "meclis"],
        "Türkiye coğrafyası": ["dağ", "nehir", "göl", "ova", "bölge"],
        "Türk tarihi": ["tarih", "savaş", "antlaşma", "kongre"],
        "Türk kültürü": ["gelenek", "kültür", "halk", "müzik"],
        "Spor - Futbol": ["futbol", "lig", "takım", "gol"],
    }
    for category, words in keywords.items():
        if any(w in lowered for w in words):
            return category
    return "Türk tarihi"
