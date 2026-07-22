"""Infobox (bilgi kutusu) ayrıştırıcı.

Wikipedia REST summary API sadece kısa bir "extract" verir; makalenin
sağ üstündeki yapılandırılmış "bilgi kutusu" (infobox) alanlarına
(nüfus, yüzölçümü, kuruluş, rakım, vali/başkan...) erişmek için ham
wikitext üzerinde çalışmamız gerekir. Bu modül basit ama sağlam bir
{{...}} şablon ayrıştırıcısı içerir — tam bir MediaWiki parser değildir,
yalnızca "anahtar = değer" satırlarını çıkarmaya yeter.
"""
from __future__ import annotations

import re

from analyzer import Fact

# Infobox içinde aradığımız anahtarlar -> (kind, soru kalıbı). Kalıp içindeki
# {suf} yerine _genitive_suffix() ile üretilen ünlü-uyumlu iyelik eki gelir
# (ör. "Ankara'nın", "İzmir'in", "Bursa'nın", "Konya'nın").
_FIELD_MAP: dict[str, tuple[str, str]] = {
    "nüfus": ("population", "{subject}{suf} nüfusu yaklaşık kaçtır?"),
    "nufus": ("population", "{subject}{suf} nüfusu yaklaşık kaçtır?"),
    "yüzölçümü": ("area", "{subject}{suf} yüzölçümü kaç km²'dir?"),
    "yuzolcumu": ("area", "{subject}{suf} yüzölçümü kaç km²'dir?"),
    "rakım": ("elevation", "{subject} kaç metre rakımdadır?"),
    "rakim": ("elevation", "{subject} kaç metre rakımdadır?"),
    "kuruluş": ("year", "{subject} hangi yıl kurulmuştur?"),
    "kurulus_tarihi": ("year", "{subject} hangi yıl kurulmuştur?"),
    "plaka": ("plaka", "{subject} ilinin plaka kodu kaçtır?"),
    "plakakodu": ("plaka", "{subject} ilinin plaka kodu kaçtır?"),
    "telefonkodu": ("phone", "{subject} ilinin telefon alan kodu kaçtır?"),
    "başkan": ("person", "{subject} belediye başkanı kimdir?"),
    "vali": ("person", "{subject} ilinin valisi kimdir?"),
    "uzunluk": ("length", "{subject}{suf} uzunluğu kaç km'dir?"),
    "yükseklik": ("elevation", "{subject}{suf} yüksekliği kaç metredir?"),
}

_GENITIVE_MAP = {
    "a": "nın", "ı": "nın", "e": "nin", "i": "nin",
    "o": "nun", "u": "nun", "ö": "nün", "ü": "nün",
}


def _genitive_suffix(word: str) -> str:
    """Türkçe ünlü uyumuna göre iyelik eki üretir (basitleştirilmiş):
    'Ankara' -> "'nın", 'İzmir' -> "'in", 'Konya' -> "'nın" gibi. Kelimenin
    SON ünlüsüne bakar; ünsüzle bitenlerde 'n' düşürülür (İzmir -> 'in)."""
    last_vowel = None
    for ch in reversed(word.strip()):
        cl = ch.lower().replace("İ", "i")
        if cl in _GENITIVE_MAP:
            last_vowel = cl
            break
    suf = _GENITIVE_MAP.get(last_vowel, "nin")
    ends_with_vowel = bool(word) and word.strip()[-1].lower() in "aeıioöuü"
    return "'" + suf if ends_with_vowel else "'" + suf[1:]  # ünsüzle bitince 'n' düşer

_TEMPLATE_START = re.compile(r"\{\{\s*(bilgi kutusu|infobox)[^\n|]*", re.IGNORECASE)


def _find_infobox_block(wikitext: str) -> str | None:
    """{{Bilgi kutusu ...}} şablonunu, iç içe {{ }} sayımıyla (balanced-brace)
    güvenli biçimde çıkarır."""
    m = _TEMPLATE_START.search(wikitext)
    if not m:
        return None
    start = m.start()
    depth = 0
    i = start
    n = len(wikitext)
    while i < n - 1:
        two = wikitext[i:i + 2]
        if two == "{{":
            depth += 1
            i += 2
            continue
        if two == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return wikitext[start:i]
            continue
        i += 1
    return None


def _clean_value(v: str) -> str:
    v = re.sub(r"<ref[^>]*>.*?</ref>", "", v, flags=re.DOTALL)
    v = re.sub(r"<ref[^/]*/>", "", v)
    v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", v)  # wikilinks
    v = re.sub(r"\{\{[^}]*\}\}", "", v)  # nested templates
    v = re.sub(r"'''?", "", v)
    v = re.sub(r"<[^>]+>", "", v)
    v = re.sub(r"\s+", " ", v).strip(" .,;")
    return v.strip()


def parse_infobox(wikitext: str) -> dict[str, str]:
    """Wikitext içinden bilgi kutusu alan/değer çiftlerini döndürür."""
    block = _find_infobox_block(wikitext)
    if not block:
        return {}
    # Kapanış }} işaretini at, yoksa son alanın değerine yapışır
    if block.endswith("}}"):
        block = block[:-2]

    fields: dict[str, str] = {}
    # "| anahtar = değer" satırları — değer bir sonraki "| " ya da satır sonuna kadar
    parts = re.split(r"\n\s*\|", block)
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        key_norm = re.sub(r"[^a-zçğıöşü]", "", key.strip().lower())
        value = _clean_value(value)
        if key_norm and value and len(value) < 150:
            fields[key_norm] = value
    return fields


def infobox_facts(wikitext: str, subject: str) -> list[Fact]:
    """Infobox alanlarını, mevcut analyzer.Fact ile uyumlu fact listesine
    çevirir. Belirsiz/uzun/boş değerler elenir."""
    fields = parse_infobox(wikitext)
    facts: list[Fact] = []
    seen_values: set[str] = set()

    for key_norm, value in fields.items():
        for map_key, (kind, template) in _FIELD_MAP.items():
            map_key_norm = re.sub(r"[^a-zçğıöşü]", "", map_key.lower())
            if key_norm != map_key_norm:
                continue
            # Sayısal alanlar (nüfus, yüzölçümü, rakım) için ilk sayı grubunu al
            if kind in ("population", "area", "elevation", "length", "year", "phone"):
                num_match = re.search(r"[\d.,]+", value)
                if not num_match:
                    continue
                value_clean = num_match.group(0).strip(".,")
            else:
                value_clean = value

            if not value_clean or value_clean in seen_values:
                continue
            if len(value_clean) < 1 or len(value_clean) > 60:
                continue
            seen_values.add(value_clean)
            predicate = template.format(subject=subject, suf=_genitive_suffix(subject))
            facts.append(Fact(
                subject=subject,
                kind=kind,
                predicate=predicate,
                value=value_clean,
                raw=f"infobox:{map_key}={value}",
            ))
            break  # bu alan için eşleşme bulundu, sıradaki fielda geç

    return facts
