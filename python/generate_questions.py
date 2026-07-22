"""Main question generation orchestrator.

Pipeline
--------
1. Collect article titles from a curated seed list + random Wikipedia titles
   filtered to Turkish topics.
2. Fetch each article's summary (title + description + extract) from the
   Wikipedia REST API.
3. Filter out disambiguation, redirect, and non-Turkish articles.
4. Extract typed facts (years, founders, locations, descriptions).
5. Generate type-aware distractors.
6. Estimate difficulty.
7. Deduplicate (hash of normalized question + correct answer).
8. Merge with the existing pool in questions.json (never deletes old questions).
9. Export updated pool to questions.json.
10. Convert questions.json → src/data/questions.ts so the app uses the latest pool.

Run with: python python/build.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from analyzer import classify_topic, estimate_difficulty, extract_facts
from deduplicate import filter_unique, question_hash
from distractor import generate_distractors
from exporter import export, load_existing, merge
from source_fetcher import clean_text, fetch_article, fetch_category_members, fetch_random_titles

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = ROOT / "questions.json"
OUTPUT_TS = ROOT / "src" / "data" / "questions.ts"

# ---------------------------------------------------------------------------
# Curated Turkish seed topics (likely to yield clean, quiz-worthy facts)
# ---------------------------------------------------------------------------
SEED_TOPICS = [
    # History / Atatürk era
    "Anıtkabir", "İstiklal Marşı", "Lozan Antlaşması", "Sèvres Antlaşması",
    "Misak-ı Millî", "Amasya Genelgesi", "Erzurum Kongresi", "Sivas Kongresi",
    "Sakarya Meydan Savaşı", "Büyük Taarruz", "Harf İnkılabı", "Soyadı Kanunu",
    "Tekke ve Zaviyelerin Kapatılması", "Türk Dil Kurumu", "Türk Tarih Kurumu",
    # Ottoman
    "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman", "Yavuz Sultan Selim",
    "Abdülhamid II", "Topkapı Sarayı", "Süleymaniye Camii", "Selimiye Camii",
    "Mimar Sinan", "Osmanlı İmparatorluğu", "Tanzimat Fermanı",
    # Geography
    "Boğaziçi", "Çanakkale Boğazı", "Ağrı Dağı", "Erciyes Dağı", "Uludağ",
    "Kaçkar Dağları", "Fırat Nehri", "Dicle Nehri", "Van Gölü", "Tuz Gölü",
    "Marmara Denizi", "Karadeniz", "Ege Denizi", "Akdeniz", "Pamukkale",
    "Kapadokya", "Nemrut Dağı", "İshak Paşa Sarayı",
    # Culture / Arts
    "Mevlana Celaleddin Rumi", "Hacı Bektaş-ı Veli", "Yunus Emre",
    "Ahmet Yesevi", "Nasreddin Hoca", "Dede Korkut", "Âşık Veysel",
    "Neşet Ertaş", "Zeki Müren", "Müzeyyen Senar", "Sezen Aksu",
    "Mehmet Akif Ersoy", "Nazım Hikmet", "Sabahattin Ali", "Orhan Pamuk",
    "Yaşar Kemal", "Ömer Seyfettin",
    # Famous buildings / sites
    "Ayasofya", "Sultanahmet Camii", "Dolmabahçe Sarayı", "Galata Kulesi",
    "Kız Kulesi", "Efes", "Troya", "Hierapolis", "Aspendos", "Ani Harabeleri",
    "Çatalhöyük", "Gordion",
    # Sports
    "Naim Süleymanoğlu", "Hüseyin Akbaş", "Rıza Kayaalp", "Taha Akgül",
    "Hakan Şükür", "Arda Turan", "Fatih Terim", "Şenol Güneş",
    # Science / Economy
    "TÜBİTAK", "ASELSAN", "Baykar", "TAI", "TOGG",
    "İstanbul Üniversitesi", "Ankara Üniversitesi", "Orta Doğu Teknik Üniversitesi",
    "Boğaziçi Üniversitesi", "İstanbul Teknik Üniversitesi",
    # Food
    "İskender Kebap", "Adana Kebap", "Lahmacun", "Mantı", "Baklava",
    "Türk kahvesi", "Rakı", "Simit", "Künefe", "Pide",
    # Wikipedia categories (fetched separately)
]

# Wikipedia category names to pull members from
WIKI_CATEGORIES = [
    "Türk_tarihi",
    "Osmanlı_padişahları",
    "Türkiye_coğrafyası",
    "Türk_şairler",
    "Türk_besteciler",
    "Türkiye_şehirleri",
    "Türk_sporcular",
    "Türk_yazarlar",
    "Türk_mimarisi",
    "Türkiye_müzeleri",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_valid_article(data: dict) -> bool:
    """Return False for disambiguation pages, stubs, and non-Turkish topics."""
    title = data.get("title", "")
    desc = data.get("description", "").lower()
    extract = data.get("extract", "")

    # Skip disambiguation / redirect / list pages
    bad_desc = ("anlam ayrımı", "disambig", "liste", "list of", "redirect", "şablon")
    if any(b in desc for b in bad_desc):
        return False

    # Skip very short extracts (stubs)
    if len(extract) < 80:
        return False

    return True


def build_question(fact, category: str, difficulty: str, q_id: str) -> dict | None:
    """Build a validated question dict or return None if quality check fails."""
    correct = fact.value.strip()

    # Answer quality checks
    if len(correct) < 2 or len(correct) > 200:
        return None
    # Reject Cyrillic / Arabic-heavy answers for 'description' kind
    # (they confuse Turkish readers)
    non_latin = sum(1 for c in correct if ord(c) > 0x024F)
    if non_latin > len(correct) * 0.5:
        return None
    # Reject generic "Bilinmeyen" placeholders bubbling up from old code
    if "bilinme" in correct.lower():
        return None

    distractors = generate_distractors(correct, kind=fact.kind, count=3)
    # Need 3 distinct distractors that don't match the correct answer
    if len(set(distractors)) < 3:
        return None
    if any(d.strip().lower() == correct.lower() for d in distractors):
        return None
    # Description-type fallback placeholders are not suitable for players
    if any("bilinm" in d.lower() or "kayıt" in d.lower() for d in distractors):
        return None

    q_text = fact.predicate
    if not q_text.endswith("?"):
        q_text = q_text.rstrip(".") + "?"

    return {
        "id": q_id,
        "hash": question_hash(q_text, correct),
        "category": category,
        "difficulty": difficulty,
        "question": q_text,
        "correctAnswer": correct,
        "distractors": distractors,
    }


def process_title(title: str, seq: int, generated: list[dict]) -> None:
    """Fetch an article and append any valid questions to *generated*."""
    data = fetch_article(title)
    if not is_valid_article(data):
        return

    real_title = data["title"]
    extract = clean_text(data["extract"])
    description = data.get("description", "")
    category = classify_topic(extract, title=real_title)
    facts = extract_facts(extract, subject=real_title, description=description)

    for i, fact in enumerate(facts):
        difficulty = estimate_difficulty(fact)
        q_id = f"gen-{seq:05d}-{i}"
        q = build_question(fact, category, difficulty, q_id)
        if q:
            generated.append(q)


def export_to_ts(items: list[dict]) -> None:
    """Write questions.json content to src/data/questions.ts."""
    lines = ['import type { Question } from \'@/types\';\n', '\nexport const questions: Question[] = [\n']
    for item in items:
        distractors_js = json.dumps(item["distractors"], ensure_ascii=False)
        # Format as valid TS with no trailing comma issues
        q_escaped = item["question"].replace("\\", "\\\\").replace("'", "\\'")
        a_escaped = item["correctAnswer"].replace("\\", "\\\\").replace("'", "\\'")
        lines.append("  {\n")
        lines.append(f"    id: '{item['id']}',\n")
        lines.append(f"    hash: '{item['hash'][:16]}',\n")
        lines.append(f"    category: '{item['category']}',\n")
        lines.append(f"    difficulty: '{item['difficulty']}',\n")
        lines.append(f"    question: '{q_escaped}',\n")
        lines.append(f"    correctAnswer: '{a_escaped}',\n")
        # Build distractors tuple
        dists = item["distractors"]
        d0 = dists[0].replace("\\", "\\\\").replace("'", "\\'")
        d1 = dists[1].replace("\\", "\\\\").replace("'", "\\'")
        d2 = dists[2].replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"    distractors: ['{d0}', '{d1}', '{d2}'],\n")
        lines.append("  },\n")
    lines.append("];\n")

    OUTPUT_TS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_TS.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    generated: list[dict] = []
    seq = random.randint(1, 99999)

    # 1. Curated seeds (first 40 this run, randomised so each run covers different ones)
    seed_sample = random.sample(SEED_TOPICS, min(40, len(SEED_TOPICS)))
    print(f"Processing {len(seed_sample)} seed topics…")
    for i, title in enumerate(seed_sample):
        process_title(title, seq * 1000 + i, generated)

    # 2. Category members
    cat_sample = random.sample(WIKI_CATEGORIES, min(4, len(WIKI_CATEGORIES)))
    for cat in cat_sample:
        members = fetch_category_members(cat, count=15)
        print(f"  Category '{cat}': {len(members)} members")
        for j, title in enumerate(members):
            process_title(title, seq * 2000 + j, generated)

    # 3. Random articles (extra diversity)
    random_titles = fetch_random_titles(15)
    print(f"Processing {len(random_titles)} random titles…")
    for k, title in enumerate(random_titles):
        process_title(title, seq * 3000 + k, generated)

    # 4. Deduplicate this run's output
    unique = filter_unique(generated)

    # 5. Merge with the existing pool (additive — never removes old questions)
    existing = load_existing(OUTPUT_JSON)
    merged = merge(existing, unique)

    # 6. Export
    export(OUTPUT_JSON, merged)
    export_to_ts(merged)

    new_count = len(merged) - len(existing)
    print(f"✓ New questions this run: {new_count}. Total pool: {len(merged)}.")
    print(f"  Wrote {OUTPUT_JSON.name} and {OUTPUT_TS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
