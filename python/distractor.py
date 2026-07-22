"""Distractor generator: produces plausible wrong answers by type.

The old version sampled from a flat pool of Turkish city names regardless of
what the correct answer was — giving distractors like "Diyarbakır / Konya /
Samsun" for a question whose answer is a year like "1923". This version
builds type-aware distractor pools so the wrong answers are always *plausible*.
"""
from __future__ import annotations

import random
import re


# ---------------------------------------------------------------------------
# Type-specific distractor pools
# ---------------------------------------------------------------------------

YEAR_POOL = [
    "1071", "1299", "1453", "1683", "1789", "1826", "1839", "1876",
    "1908", "1919", "1920", "1921", "1922", "1923", "1924", "1925",
    "1928", "1930", "1934", "1938", "1950", "1960", "1963", "1971",
    "1980", "1982", "1990", "1999", "2001", "2007", "2010", "2013",
    "2016", "2018", "2020", "2023",
]

PERSON_POOL = [
    "Mustafa Kemal Atatürk", "İsmet İnönü", "Celal Bayar", "Adnan Menderes",
    "Süleyman Demirel", "Bülent Ecevit", "Turgut Özal", "Tansu Çiller",
    "Recep Tayyip Erdoğan", "Abdullah Gül", "Ahmet Davutoğlu",
    "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman", "Yavuz Sultan Selim",
    "Abdülhamid II", "II. Mahmud", "III. Selim",
    "Mehmet Akif Ersoy", "Nazım Hikmet", "Sabahattin Ali", "Yunus Emre",
    "Mevlana Celaleddin Rumi", "Hacı Bektaş-ı Veli", "Ahmet Yesevi",
    "Fatih Terim", "Şenol Güneş", "Hakan Şükür", "Arda Turan",
    "Naim Süleymanoğlu", "Rıza Kayaalp", "Taha Akgül",
    "Mimar Sinan", "Mimar Kemaleddin", "Sedefkâr Mehmed Ağa",
]

CITY_POOL = [
    "Adana", "Ankara", "Antalya", "Bursa", "Denizli", "Diyarbakır",
    "Edirne", "Erzurum", "Eskişehir", "Gaziantep", "İstanbul", "İzmir",
    "Kahramanmaraş", "Kayseri", "Konya", "Malatya", "Manisa", "Mersin",
    "Muğla", "Sakarya", "Samsun", "Trabzon", "Van",
]

COUNTRY_POOL = [
    "Almanya", "Amerika Birleşik Devletleri", "Azerbaycan", "Bulgaristan",
    "Fransa", "Gürcistan", "İngiltere", "İran", "Irak", "İspanya",
    "İsveç", "İtalya", "Japonya", "Kazakistan", "Kıbrıs", "Mısır",
    "Özbekistan", "Rusya", "Suriye", "Suudi Arabistan", "Türkmenistan",
    "Ukrayna", "Yunanistan",
]

GENERIC_POOL = PERSON_POOL + CITY_POOL


def _is_year(value: str) -> bool:
    return bool(re.fullmatch(r"\d{3,4}", value.strip()))


def _is_person(value: str) -> bool:
    # Two+ capitalized Turkish words
    return bool(re.fullmatch(
        r"[A-ZÇĞİÖŞÜ][a-zçğışöü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğışöü]+)+",
        value.strip(),
    ))


def generate_distractors(correct: str, kind: str = "general", count: int = 3) -> list[str]:
    """Return *count* plausible wrong answers for *correct* given its *kind*."""
    correct = correct.strip()

    # Choose pool by kind + heuristics
    if kind == "year" or _is_year(correct):
        pool = YEAR_POOL
    elif kind == "person" or _is_person(correct):
        pool = PERSON_POOL
    elif kind == "location":
        pool = CITY_POOL
    elif kind == "description":
        # For description answers we can't easily generate plausibles,
        # so we deliberately skip — caller should omit question if pool < 3
        pool = []
    else:
        pool = GENERIC_POOL

    candidates = [p for p in pool if p.strip().lower() != correct.strip().lower()]
    random.shuffle(candidates)
    distractors = candidates[:count]

    # Pad with generated placeholders only as last resort
    fallbacks = [
        f"Bilinmiyor", f"Kayıt dışı", f"Tarihsel olarak belirsiz"
    ]
    i = 0
    while len(distractors) < count and i < len(fallbacks):
        if fallbacks[i] not in distractors:
            distractors.append(fallbacks[i])
        i += 1

    return distractors[:count]
