"""Text analyzer: extracts structured facts from Turkish encyclopedic text.

Strategy
--------
Instead of hunting raw regex patterns in arbitrary Wikipedia text (which
produced >95% garbage with the old approach), we use the article's
*description* field from the REST summary API plus a curated set of
extractors that produce verifiable, quiz-ready facts.

The description is the short human-written subtitle that Wikipedia editors
maintain — it's almost always a clean, one-clause sentence like
  "Türk halk müzisyeni ve âşık"
  "İstanbul'da bulunan tarihi Osmanlı sarayı"
which makes it far more reliable than parsing the full extract.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

DIFFICULTY_LADDER = [
    "Kolay", "Normal", "Orta", "Zor", "Çok Zor",
    "Uzman", "Profesör", "Akademisyen", "Final",
]


@dataclass
class Fact:
    subject: str
    kind: str        # 'year' | 'person' | 'location' | 'description' | 'general'
    predicate: str   # full Turkish question string
    value: str       # correct answer
    raw: str         # original source sentence (for difficulty estimation)


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

_YEAR_RE = re.compile(r"\b(1[3-9]\d{2}|20[012]\d)\b")

# Founder/establisher patterns
_FOUNDER_PATTERNS = [
    re.compile(
        r"([A-ZÇĞİÖŞÜa-zçğışöü][\w\s]{2,40}?)\s+tarafından\s+(?:kuruldu|inşa edildi|yaptırıldı)",
        re.UNICODE,
    ),
    re.compile(
        r"kurucusu\s+([A-ZÇĞİÖŞÜ][\w\s]{2,40})",
        re.UNICODE,
    ),
]

# Birth year
_BIRTH_RE = re.compile(r"(?:d\.|doğum|doğdu)\s*[:\-]?\s*(\d{4})", re.IGNORECASE)
_DEATH_RE = re.compile(r"(?:ö\.|ölüm|öldü|vefat)\s*[:\-]?\s*(\d{4})", re.IGNORECASE)

# Population
_POP_RE = re.compile(
    r"nüfus[ua]?\s+([0-9][0-9.,\s]*(?:milyon|bin)?(?:\s*kişi)?)", re.UNICODE
)

# Area
_AREA_RE = re.compile(r"yüzölçümü\s+([0-9.,]+\s*km[²2]?)", re.UNICODE)

# Location
_LOC_RE = re.compile(
    r"([A-ZÇĞİÖŞÜ][a-zçğışöü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğışöü]+)?)\s+"
    r"(?:ili|ilçesi|şehri|kenti|bölgesi)"
    r"(?:'nde?|'nda?|'de?|'da?)?\s+"
    r"(?:bulunmaktadır|yer almaktadır|konumlanmaktadır)",
    re.UNICODE,
)


def _split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _year_fact(sent: str, subject: str) -> Fact | None:
    m = _YEAR_RE.search(sent)
    if not m:
        return None
    year = m.group(1)
    sl = sent.lower()
    if "kuruldu" in sl or "kurulmuş" in sl:
        pred = f"{subject} hangi yıl kuruldu?"
    elif "doğdu" in sl or "doğum" in sl:
        pred = f"{subject} hangi yıl doğdu?"
    elif "öldü" in sl or "vefat" in sl or "hayatını kaybetti" in sl:
        pred = f"{subject} hangi yıl hayatını kaybetti?"
    elif "ilan edildi" in sl:
        pred = f"{subject} hangi yıl ilan edildi?"
    elif "inşa" in sl or "yapıldı" in sl or "yaptırıldı" in sl:
        pred = f"{subject} hangi yıl inşa edildi?"
    elif "açıldı" in sl:
        pred = f"{subject} hangi yıl açıldı?"
    elif "kazandı" in sl:
        pred = f"{subject} bu başarıyı hangi yıl elde etti?"
    elif "kurul" in sl or "oluştur" in sl:
        pred = f"{subject} hangi yıl oluşturuldu?"
    else:
        return None  # vague year context — skip
    return Fact(subject=subject, kind="year", predicate=pred, value=year, raw=sent)


def _founder_fact(sent: str, subject: str) -> Fact | None:
    for pat in _FOUNDER_PATTERNS:
        m = pat.search(sent)
        if m:
            founder = m.group(1).strip()
            if 3 < len(founder) < 60:
                pred = f"{subject}'ı kim kurdu?"
                return Fact(subject=subject, kind="person", predicate=pred, value=founder, raw=sent)
    return None


def _pop_fact(sent: str, subject: str) -> Fact | None:
    m = _POP_RE.search(sent)
    if not m:
        return None
    pop = re.sub(r"\s+", " ", m.group(1)).strip()
    pred = f"{subject}'in nüfusu yaklaşık kaçtır?"
    return Fact(subject=subject, kind="population", predicate=pred, value=pop, raw=sent)


def _area_fact(sent: str, subject: str) -> Fact | None:
    m = _AREA_RE.search(sent)
    if not m:
        return None
    area = m.group(1).strip()
    pred = f"{subject}'in yüzölçümü nedir?"
    return Fact(subject=subject, kind="area", predicate=pred, value=area, raw=sent)


def _loc_fact(sent: str, subject: str) -> Fact | None:
    m = _LOC_RE.search(sent)
    if not m:
        return None
    loc = m.group(1).strip()
    pred = f"{subject} hangi ilde/şehirde bulunmaktadır?"
    return Fact(subject=subject, kind="location", predicate=pred, value=loc, raw=sent)


_EXTRACTORS = [_year_fact, _founder_fact, _pop_fact, _area_fact, _loc_fact]


def extract_facts(text: str, subject: str = "", description: str = "") -> list[Fact]:
    """Extract structured facts from article text and its short description."""
    facts: list[Fact] = []
    seen_values: set[str] = set()

    def _add(f: Fact | None) -> None:
        if f and f.value and f.value not in seen_values and len(f.value) >= 2:
            seen_values.add(f.value)
            facts.append(f)

    # — Primary: parse the full extract sentence by sentence
    for sent in _split(text):
        for ex in _EXTRACTORS:
            _add(ex(sent, subject))
            if len(facts) >= 6:
                break
        if len(facts) >= 6:
            break

    # — Secondary: if description is a short meaningful label, use it directly
    # as a "what is X?" question.  Filter out disambiguation pages, lists, etc.
    if description and 8 < len(description) < 120:
        bad = ("anlam ayrımı", "liste", "disambiguation", "redirect", "madde", "şablon")
        if not any(b in description.lower() for b in bad):
            pred = f"{subject} nedir / kimdir?"
            _add(Fact(
                subject=subject,
                kind="description",
                predicate=pred,
                value=description,
                raw=description,
            ))

    return facts


# ---------------------------------------------------------------------------
# Topic classifier
# ---------------------------------------------------------------------------

def is_turkey_related(title: str, extract: str, description: str = "") -> bool:
    """Rastgele Wikipedia maddeleri ve 'ilişkili maddeler' taraması gibi
    GÜVENSİZ (küratörlü olmayan) kaynaklardan gelen başlıkların gerçekten
    Türkiye odaklı olup olmadığını denetler. Küratörlü seed/kategori
    listelerinden gelen başlıklar zaten güvenilir kabul edilir ve bu
    kontrolden geçirilmez (bkz. generate_questions.py)."""
    combined = f"{title} {extract} {description}".lower()
    signals = (
        "türkiye", "türk ", "türkçe", "osmanlı", "anadolu", "atatürk",
        "cumhuriyet", "istanbul", "ankara", "izmir", "selçuklu", "göktürk",
        "tbmm", "kurtuluş savaşı", "il ", "ilçe", "vilayet", "boğaz",
    )
    return any(s in combined for s in signals)


def classify_topic(text: str, title: str = "") -> str:
    combined = (title + " " + text).lower()
    mapping: dict[str, list[str]] = {
        "İlk Türk Devletleri": ["hun imparatorluğu", "göktürk", "uygur kağanlığı", "karahanlı", "büyük selçuklu", "malazgirt", "harzemşah"],
        "Osmanlı Tarihi": ["osmanlı", "padişah", "sultan", "fatih", "kanuni", "yavuz", "devlet-i aliyye", "sadrazam"],
        "Kurtuluş Savaşı ve Cumhuriyet": ["kurtuluş savaşı", "kuva-yi milliye", "milli mücadele", "istiklal", "sakarya meydan", "cumhuriyet", "atatürk", "tbmm", "lozan"],
        "Türkiye Coğrafyası": ["anadolu", "boğaz", "dağ", "nehir", "göl", "ova", "yayla", "il ", "ilçe", "plaka"],
        "Ulaşım ve Altyapı": ["havalimanı", "liman", "demiryolu", "köprü", "tünel", "otoyol", "marmaray"],
        "Doğal ve Kültürel Miras": ["unesco", "milli park", "ören yeri", "antik kent", "harabe"],
        "Türk Mutfağı": ["yemek", "tarif", "kebap", "börek", "baklava", "lahmacun", "mutfak", "lezzet", "tatlı", "içecek"],
        "Türk Kültürü": ["gelenek", "görenek", "halk oyunu", "ebru", "hat sanatı", "tezhip", "minyatür", "çini", "âşık", "ozan", "nevruz", "hıdrellez"],
        "Türk Edebiyatı": ["destan", "divan", "roman", "şiir", "yazar", "şair", "edebiyat"],
        "Sanat, Sinema ve Müzik": ["sinema", "dizi", "tiyatro", "besteci", "müzisyen", "şarkıcı", "film", "oyuncu"],
        "Bilim ve Teknoloji": ["bilim", "teknoloji", "mühendis", "icat", "üniversite", "araştırma", "keşif", "mucit"],
        "Spor": ["futbol", "basketbol", "güreş", "olimpiyat", "şampiyona", "lig", "takım", "milli takım", "kulüp"],
        "İslam ve Dini Konular": ["islam", "kur'an", "kuran", "peygamber", "sahabe", "cami", "türbe", "bayram", "kandil"],
        "Ekonomi, Tarım ve Enerji": ["ekonomi", "enflasyon", "ihracat", "sanayi", "tarım", "banka", "borsa", "maden", "enerji", "turizm"],
        "Afet ve Sağlık": ["deprem", "afet", "afad", "kızılay", "sağlık", "hastalık", "salgın"],
        "Türk Tarihi": ["savaş", "antlaşma", "fetih", "tarih", "han", "hanlık"],
        "Sanat ve Mimari": ["mimari", "cami", "kale", "köprü", "saray", "müze", "galeri", "heykel"],
    }
    for category, words in mapping.items():
        if any(w in combined for w in words):
            return category
    return "Türk Tarihi"


# ---------------------------------------------------------------------------
# Kalite puanı — otomatik doğrulama sisteminin bir parçası
# ---------------------------------------------------------------------------

def quality_score(question: str, correct: str, distractors: list[str], kind: str) -> int:
    """0-100 arası bir kalite puanı. Şüpheli/düşük kaliteli sorular
    (belirsiz kısa cevaplar, tekrarlı/placeholder şıklar, aşırı uzun metin)
    daha düşük puan alır; generate_questions.py bunları bir eşik altında
    eleyebilir (otomatik doğrulama sistemi)."""
    score = 100

    if not question.endswith("?"):
        score -= 15
    qlen = len(question)
    if qlen < 12 or qlen > 220:
        score -= 20

    correct_l = correct.strip().lower()
    if len(correct.strip()) < 2:
        score -= 40
    if "bilinm" in correct_l or "belirsiz" in correct_l or "kayıt" in correct_l:
        score -= 50

    placeholder_hits = sum(
        1 for d in distractors
        if "bilinm" in d.lower() or "belirsiz" in d.lower() or "kayıt" in d.lower()
    )
    score -= placeholder_hits * 15

    if len(set(d.strip().lower() for d in distractors)) < len(distractors):
        score -= 25

    if any(d.strip().lower() == correct_l for d in distractors):
        score -= 100  # doğru cevap şıklarda tekrarlanmış — kabul edilemez

    # Sayısal tip sorularda cevap gerçekten sayı içeriyor mu?
    if kind in ("year", "population", "area", "elevation", "length", "phone", "plaka"):
        if not any(c.isdigit() for c in correct):
            score -= 30
        # Savunma amaçlı ikinci katman: sayısal bir soruda çeldiricilerden
        # biri hiç rakam içermiyorsa (ör. bir kişi/şehir ismi sızmışsa),
        # bu tip-uyuşmazlığı tek başına soruyu geçersiz kılar.
        non_numeric_distractors = sum(1 for d in distractors if not any(c.isdigit() for c in d))
        if non_numeric_distractors:
            score -= 60

    return max(0, min(100, score))


def estimate_difficulty(fact: Fact) -> str:
    """Estimate difficulty from text complexity and answer type."""
    length = len(fact.raw)
    if fact.kind == "description":
        # Description-based questions tend to be easier if the description is short
        score = max(0, (length - 30) // 20)
    elif fact.kind == "year":
        score = 1  # year questions: easy-medium
    elif fact.kind == "population":
        score = 4  # numeric answers harder
    else:
        score = length // 35

    # Boost difficulty for non-ASCII (e.g. Ottoman, Arabic, Cyrillic in answer)
    non_ascii = sum(1 for c in fact.value if ord(c) > 127 and not "\u00c0" <= c <= "\u024f")
    score += non_ascii // 3

    idx = min(score, len(DIFFICULTY_LADDER) - 1)
    return DIFFICULTY_LADDER[idx]
