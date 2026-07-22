"""Main question generation orchestrator.

Pipeline
--------
1. Türkiye odaklı genişletilmiş konu kataloğundan (turkiye_data.py) her
   çalıştırmada bir dilim seç — az soru biriken kategoriler önceliklenir,
   kalıcı bir "cursor" ile aynı başlıklar sürekli tekrar taranmaz.
2. Her başlık için: REST özet + ham wikitext (infobox) + (örneklem için)
   ilişkili maddeler + bir seviye alt kategori taraması.
3. Metinden ve infobox'tan tipli fact'ler çıkar.
4. Tip-duyarlı çeldiriciler üret.
5. Zorluk tahmini + kalite puanı hesapla; düşük kaliteli soruları ele
   (otomatik doğrulama).
6. Deduplicate: SHA-256 tam eşleşme + Levenshtein yakın-kopya (bu turun
   içinde VE aynı kategorideki mevcut havuzla karşılaştırarak).
7. Mevcut questions.json ile birleştir (asla eski soru silinmez).
8. questions.json ve src/data/questions.ts olarak dışa aktar.

Çalıştırma: python python/build.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from analyzer import classify_topic, estimate_difficulty, extract_facts, is_turkey_related, quality_score
from deduplicate import filter_against_existing, filter_near_duplicates, filter_unique, question_hash
from distractor import generate_distractors
from exporter import export, load_existing, merge
from infobox import infobox_facts
from source_fetcher import (
    clean_text,
    fetch_article,
    fetch_category_members,
    fetch_random_titles,
    fetch_related_links,
    fetch_subcategories,
    fetch_wikitext,
)
from turkiye_data import SECTIONS, plaka_facts

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = ROOT / "questions.json"
OUTPUT_TS = ROOT / "src" / "data" / "questions.ts"
STATE_FILE = Path(__file__).resolve().parent / ".crawl_state.json"

QUALITY_THRESHOLD = 55  # 0-100; bunun altındaki sorular otomatik elenir

# Her çalıştırmada bölüm başına işlenecek en fazla başlık sayısı.
# (Wikipedia'yı nazikçe kullanmak + cron çalıştırma süresini makul tutmak için)
SEEDS_PER_SECTION = 6
CATEGORY_MEMBERS_PER_SECTION = 8
CATEGORY_FETCH_POOL = 40  # API'den çekilecek ham havuz — rotasyonun anlamlı olması için
SECTIONS_PER_RUN = 6
SUBCATEGORY_SAMPLE_SECTIONS = 2
RELATED_LINKS_SAMPLE = 3

# ---------------------------------------------------------------------------
# Kalıcı tarama durumu (cursor) — aynı başlıklar sürekli tekrar taranmasın
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"seed_cursor": {}, "category_cursor": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"seed_cursor": {}, "category_cursor": {}}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # durum dosyası yazılamazsa üretim akışını bozmasın


def _rotating_slice(items: list[str], cursor: int, count: int) -> tuple[list[str], int]:
    """items listesinden cursor'dan başlayarak (wrap-around ile) count kadar
    eleman alır; yeni cursor'u da döndürür. Böylece her çalıştırma listenin
    farklı bir diliminden geçer, hep aynı ilk N eleman işlenmez."""
    if not items:
        return [], 0
    n = len(items)
    cursor = cursor % n
    out = [items[(cursor + i) % n] for i in range(min(count, n))]
    new_cursor = (cursor + len(out)) % n
    return out, new_cursor


def is_valid_article(data: dict) -> bool:
    """Return False for disambiguation pages, stubs, and non-Turkish topics."""
    desc = data.get("description", "").lower()
    extract = data.get("extract", "")

    bad_desc = ("anlam ayrımı", "disambig", "liste", "list of", "redirect", "şablon")
    if any(b in desc for b in bad_desc):
        return False
    if len(extract) < 80:
        return False
    return True


def build_question(fact, category: str, difficulty: str, q_id: str, source: str) -> dict | None:
    """Build a validated question dict or return None if quality check fails."""
    correct = fact.value.strip()

    if len(correct) < 2 or len(correct) > 200:
        return None
    non_latin = sum(1 for c in correct if ord(c) > 0x024F)
    if non_latin > len(correct) * 0.5:
        return None
    if "bilinme" in correct.lower():
        return None

    distractors = generate_distractors(correct, kind=fact.kind, count=3)
    if len(set(distractors)) < 3:
        return None
    if any(d.strip().lower() == correct.lower() for d in distractors):
        return None
    if any("bilinm" in d.lower() or "kayıt" in d.lower() for d in distractors):
        return None

    q_text = fact.predicate
    if not q_text.endswith("?"):
        q_text = q_text.rstrip(".") + "?"

    score = quality_score(q_text, correct, distractors, fact.kind)
    if score < QUALITY_THRESHOLD:
        return None

    return {
        "id": q_id,
        "hash": question_hash(q_text, correct),
        "category": category,
        "difficulty": difficulty,
        "question": q_text,
        "correctAnswer": correct,
        "distractors": distractors,
        "source": source,
        "qualityScore": score,
    }


def process_title(
    title: str,
    seq: int,
    generated: list[dict],
    fetch_infobox: bool = True,
    require_turkey_check: bool = False,
) -> None:
    """Fetch an article (summary + optionally wikitext infobox) and append
    any valid questions to *generated*.

    require_turkey_check=True: küratörlü olmayan kaynaklardan (rastgele
    madde, ilişkili madde taraması) gelen başlıklar için — makale gerçekten
    Türkiye odaklı değilse sessizce atlanır. Küratörlü seed/kategori
    listeleri zaten güvenilir olduğundan bu kontrol onlara uygulanmaz.
    """
    data = fetch_article(title)
    if not is_valid_article(data):
        return

    real_title = data["title"]
    extract = clean_text(data["extract"])
    description = data.get("description", "")

    if require_turkey_check and not is_turkey_related(real_title, extract, description):
        return

    category = classify_topic(extract, title=real_title)
    facts = extract_facts(extract, subject=real_title, description=description)

    if fetch_infobox:
        wikitext = fetch_wikitext(real_title)
        if wikitext:
            facts = facts + infobox_facts(wikitext, real_title)

    source = f"tr.wikipedia.org/wiki/{real_title.replace(' ', '_')}"
    for i, fact in enumerate(facts):
        difficulty = estimate_difficulty(fact)
        q_id = f"gen-{seq:05d}-{i}"
        q = build_question(fact, category, difficulty, q_id, source)
        if q:
            generated.append(q)


def process_static_plaka_facts(generated: list[dict], seq: int) -> None:
    """Wikipedia gerektirmeyen, doğrudan doğrulanmış statik plaka kodu
    sorularını havuza ekler (kind='plaka')."""
    for i, item in enumerate(plaka_facts()):
        correct = item["correct"]
        distractors = random.sample(item["distractor_pool"], min(3, len(item["distractor_pool"])))
        if len(set(distractors)) < 3 or any(d == correct for d in distractors):
            continue
        q_text = item["question"]
        score = quality_score(q_text, correct, distractors, "plaka")
        if score < QUALITY_THRESHOLD:
            continue
        generated.append({
            "id": f"plaka-{seq:05d}-{i}",
            "hash": question_hash(q_text, correct),
            "category": "Türkiye Coğrafyası",
            "difficulty": "Kolay",
            "question": q_text,
            "correctAnswer": correct,
            "distractors": distractors,
            "source": "static:il-plaka-kodlari",
            "qualityScore": score,
        })


def export_to_ts(items: list[dict]) -> None:
    """Write questions.json content to src/data/questions.ts."""
    lines = ['import type { Question } from \'@/types\';\n', '\nexport const questions: Question[] = [\n']
    for item in items:
        q_escaped = item["question"].replace("\\", "\\\\").replace("'", "\\'")
        a_escaped = item["correctAnswer"].replace("\\", "\\\\").replace("'", "\\'")
        lines.append("  {\n")
        lines.append(f"    id: '{item['id']}',\n")
        lines.append(f"    hash: '{item['hash'][:16]}',\n")
        lines.append(f"    category: '{item['category']}',\n")
        lines.append(f"    difficulty: '{item['difficulty']}',\n")
        lines.append(f"    question: '{q_escaped}',\n")
        lines.append(f"    correctAnswer: '{a_escaped}',\n")
        dists = item["distractors"]
        d0 = dists[0].replace("\\", "\\\\").replace("'", "\\'")
        d1 = dists[1].replace("\\", "\\\\").replace("'", "\\'")
        d2 = dists[2].replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"    distractors: ['{d0}', '{d1}', '{d2}'],\n")
        if item.get("source"):
            src_escaped = str(item["source"]).replace("\\", "\\\\").replace("'", "\\'")
            lines.append(f"    source: '{src_escaped}',\n")
        lines.append("  },\n")
    lines.append("];\n")

    OUTPUT_TS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_TS.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Kategori dengesi: az soru biriken bölümleri bu çalıştırmada önceliklendir
# ---------------------------------------------------------------------------

def plan_sections_for_run(existing: list[dict]) -> list:
    counts: dict[str, int] = {}
    for q in existing:
        counts[q.get("category", "")] = counts.get(q.get("category", ""), 0) + 1
    # Az soru biriken bölüm önce gelsin (dengeli dağılım)
    ranked = sorted(SECTIONS, key=lambda sec: counts.get(sec.label, 0))
    return ranked[:SECTIONS_PER_RUN]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    generated: list[dict] = []
    seq = random.randint(1, 99999)
    state = load_state()
    seed_cursor: dict = state.setdefault("seed_cursor", {})
    category_cursor: dict = state.setdefault("category_cursor", {})

    existing_for_plan = load_existing(OUTPUT_JSON)
    run_sections = plan_sections_for_run(existing_for_plan)
    print(f"Bu turda işlenecek {len(run_sections)} bölüm: "
          f"{', '.join(sec.label for sec in run_sections)}")

    # 0. Wikipedia gerektirmeyen statik, doğrulanmış plaka kodu soruları
    process_static_plaka_facts(generated, seq)

    idx = 0
    for section_i, sec in enumerate(run_sections):
        idx += 1
        # a) Seed makaleler — rotasyonlu dilim
        cursor = seed_cursor.get(sec.label, 0)
        titles, new_cursor = _rotating_slice(sec.seeds, cursor, SEEDS_PER_SECTION)
        seed_cursor[sec.label] = new_cursor
        print(f"  [{sec.label}] {len(titles)} seed başlık işleniyor…")
        for j, title in enumerate(titles):
            process_title(title, seq * 1000 + idx * 100 + j, generated)

        # b) Kategori üyeleri (rotasyonlu). API'den ihtiyaçtan büyük bir
        #    havuz çekiyoruz (CATEGORY_FETCH_POOL), çünkü aksi halde
        #    cmlimit zaten sonucu sınırladığından cursor rotasyonu hiçbir
        #    işe yaramaz — her çalıştırmada aynı ilk üyeler gelirdi.
        for cat_name in sec.wiki_categories:
            cursor2 = category_cursor.get(cat_name, 0)
            members = fetch_category_members(cat_name, count=CATEGORY_FETCH_POOL)
            if not members:
                continue
            picked, new_cursor2 = _rotating_slice(members, cursor2, CATEGORY_MEMBERS_PER_SECTION)
            category_cursor[cat_name] = new_cursor2
            print(f"    Kategori '{cat_name}': {len(picked)}/{len(members)} madde (rotasyonlu)")
            for k, title in enumerate(picked):
                process_title(title, seq * 2000 + idx * 100 + k, generated, fetch_infobox=False)

        # c) Alt kategori taraması (yalnızca birkaç bölüm için — "kategori altı")
        if section_i < SUBCATEGORY_SAMPLE_SECTIONS and sec.wiki_categories:
            for cat_name in sec.wiki_categories[:1]:
                subcats = fetch_subcategories(cat_name, count=5)
                for sc in subcats[:3]:
                    sub_members = fetch_category_members(sc, count=6)
                    for m, title in enumerate(sub_members):
                        process_title(title, seq * 3000 + idx * 100 + m, generated, fetch_infobox=False)

        # d) İlişkili maddeler (bu bölümün ilk birkaç seed'inin bağlantıları).
        #    Küratörlü değil — Türkiye-odaklılık kontrolü zorunlu.
        for title in titles[:RELATED_LINKS_SAMPLE]:
            for r, linked in enumerate(fetch_related_links(title, count=5)):
                process_title(
                    linked, seq * 4000 + idx * 100 + r, generated,
                    fetch_infobox=False, require_turkey_check=True,
                )

    # e) Rastgele makaleler (ekstra çeşitlilik). Küratörlü değil —
    #    Türkiye-odaklılık kontrolü zorunlu, aksi halde konu dışı sorular
    #    havuza sızabilir.
    random_titles = fetch_random_titles(10)
    print(f"Ek çeşitlilik için {len(random_titles)} rastgele madde işleniyor…")
    for k, title in enumerate(random_titles):
        process_title(
            title, seq * 9000 + k, generated,
            fetch_infobox=False, require_turkey_check=True,
        )

    state["seed_cursor"] = seed_cursor
    state["category_cursor"] = category_cursor
    save_state(state)

    # Deduplicate: bu turun içinde + mevcut havuzla (aynı kategori bucket'ı)
    unique = filter_unique(generated)
    unique = filter_near_duplicates(unique)
    unique = filter_against_existing(unique, existing_for_plan)

    existing = load_existing(OUTPUT_JSON)
    merged = merge(existing, unique)

    export(OUTPUT_JSON, merged)
    export_to_ts(merged)

    new_count = len(merged) - len(existing)
    print(f"✓ Bu turda eklenen yeni soru: {new_count}. Toplam havuz: {len(merged)}.")
    print(f"  {OUTPUT_JSON.name} ve {OUTPUT_TS.relative_to(ROOT)} güncellendi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
