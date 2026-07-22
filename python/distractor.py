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


def _numeric_distractors(correct: str, count: int, spread: float) -> list[str]:
    """Doğru cevabın SAYISAL kısmını bulup (binlik ayraç/birim korunarak)
    ±spread oranında rastgele sapan, biçimi doğru cevaba benzeyen
    çeldiriciler üretir. Örn. '5.782.285' -> '6.412.930', '4.998.104' gibi."""
    m = re.search(r"[\d.,]+", correct)
    if not m:
        return []
    num_str = m.group(0)
    prefix, suffix = correct[:m.start()], correct[m.end():]
    digits_only = re.sub(r"[.,]", "", num_str)
    if not digits_only.isdigit():
        return []
    value = int(digits_only)
    # Orijinal biçimde nokta/virgül kullanılmış mı — basit binlik ayraç tespiti
    uses_dot_thousands = "." in num_str and len(num_str.split(".")[-1]) == 3

    seen: set[int] = {value}
    out: list[str] = []
    attempts = 0
    while len(out) < count and attempts < 30:
        attempts += 1
        factor = 1 + random.uniform(-spread, spread)
        candidate = max(1, int(round(value * factor)))
        if candidate in seen:
            continue
        seen.add(candidate)
        cand_str = f"{candidate:,}".replace(",", ".") if uses_dot_thousands else str(candidate)
        out.append(f"{prefix}{cand_str}{suffix}")
    return out


PHONE_AREA_CODE_POOL = [str(c) for c in range(212, 494) if c not in (0,)][:60]


def _kind_pool_distractors(correct: str, kind: str, count: int) -> list[str]:
    """kind'a özgü, sayısal-uygun çeldirici üretimi. Boş dönerse çağıran
    taraf GENERIC_POOL'a düşer (ama artık numeric kind'lar için asla
    kişi/şehir ismi karışmaz)."""
    if kind == "population":
        return _numeric_distractors(correct, count, spread=0.4)
    if kind in ("area", "length"):
        return _numeric_distractors(correct, count, spread=0.35)
    if kind == "elevation":
        return _numeric_distractors(correct, count, spread=0.3)
    if kind == "phone":
        candidates = [c for c in PHONE_AREA_CODE_POOL if c != correct.strip()]
        random.shuffle(candidates)
        return candidates[:count]
    if kind == "plaka":
        candidates = [f"{i:02d}" for i in range(1, 82) if f"{i:02d}" != correct.strip()]
        random.shuffle(candidates)
        return candidates[:count]
    return []


def generate_distractors(correct: str, kind: str = "general", count: int = 3) -> list[str]:
    """Return *count* plausible wrong answers for *correct* given its *kind*."""
    correct = correct.strip()

    # 1) kind'a özgü SAYISAL çeldirici üretimi (nüfus/alan/rakım/telefon/plaka)
    #    — bunlar asla kişi/şehir isim havuzuna düşmemeli.
    kind_specific = _kind_pool_distractors(correct, kind, count)
    if len(set(kind_specific)) >= count:
        return kind_specific[:count]

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
    elif kind in ("population", "area", "elevation", "length", "phone", "plaka"):
        # Sayısal üretim yetersiz kaldıysa (ör. metin sayı içermiyordu) —
        # kişi/şehir ismi karıştırmak yerine soruyu tamamen elemeyi tercih et.
        pool = []
    else:
        pool = GENERIC_POOL

    candidates = [p for p in pool if p.strip().lower() != correct.strip().lower()]
    random.shuffle(candidates)
    distractors = list(dict.fromkeys(kind_specific + candidates))[:count]

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
