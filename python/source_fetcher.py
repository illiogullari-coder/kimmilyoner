"""Encyclopedic source fetcher for Turkish knowledge content."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "KimBilgi/1.0 (educational quiz; contact: dev@example.com)"
TIMEOUT = 20


def fetch_article(title: str) -> dict:
    """Fetch the full extract of a Turkish Wikipedia article.
    Returns dict with 'extract', 'title', and 'description' keys.
    """
    url = (
        "https://tr.wikipedia.org/api/rest_v1/page/summary/"
        + urllib.parse.quote(title, safe="")
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "title": data.get("title", title),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
            }
    except Exception:
        return {"title": title, "extract": "", "description": ""}


def fetch_random_titles(count: int = 20) -> list[str]:
    """Return random Turkish Wikipedia article titles."""
    url = (
        "https://tr.wikipedia.org/w/api.php"
        "?action=query"
        "&list=random"
        "&rnnamespace=0"
        f"&rnlimit={min(count, 500)}"
        "&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [item["title"] for item in data.get("query", {}).get("random", [])]
    except Exception:
        return []


def fetch_category_members(category: str, count: int = 30) -> list[str]:
    """Return article titles from a Turkish Wikipedia category."""
    url = (
        "https://tr.wikipedia.org/w/api.php"
        "?action=query"
        "&list=categorymembers"
        f"&cmtitle=Kategori:{urllib.parse.quote(category)}"
        f"&cmlimit={count}"
        "&cmnamespace=0"
        "&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            members = data.get("query", {}).get("categorymembers", [])
            return [m["title"] for m in members]
    except Exception:
        return []


def clean_text(text: str) -> str:
    # Remove parenthetical references, extra whitespace
    text = re.sub(r"\([^)]{0,60}\)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_subcategories(category: str, count: int = 15) -> list[str]:
    """Bir kategorinin ALT kategorilerini döndürür (kategori altı taraması).
    Örn: 'Türkiye'nin_illeri' -> ['Adana ile ilgili maddeler', ...] gibi
    alt-kategori adları. Boşluksuz 'Kategori:' öneki olmadan döner."""
    url = (
        "https://tr.wikipedia.org/w/api.php"
        "?action=query"
        "&list=categorymembers"
        f"&cmtitle=Kategori:{urllib.parse.quote(category)}"
        f"&cmlimit={count}"
        "&cmtype=subcat"
        "&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            members = data.get("query", {}).get("categorymembers", [])
            # Başlıklar "Kategori:XYZ" biçiminde gelir; önekini temizle
            return [
                m["title"].split(":", 1)[-1]
                for m in members
                if m.get("title")
            ]
    except Exception:
        return []


def fetch_wikitext(title: str) -> str:
    """Bir makalenin ham wikitext'ini döndürür (infobox ayrıştırma için).
    Başarısız olursa boş string döner — çağıran taraf zaten bunu
    zararsızca yok sayar (infobox.parse_infobox boş dict döner)."""
    url = (
        "https://tr.wikipedia.org/w/api.php"
        "?action=query"
        "&prop=revisions"
        "&rvslots=main"
        "&rvprop=content"
        "&formatversion=2"
        f"&titles={urllib.parse.quote(title, safe='')}"
        "&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", [])
            if not pages:
                return ""
            revisions = pages[0].get("revisions", [])
            if not revisions:
                return ""
            return revisions[0].get("slots", {}).get("main", {}).get("content", "")
    except Exception:
        return ""


def fetch_related_links(title: str, count: int = 10) -> list[str]:
    """Bir makaleden dışa giden bağlantıları döndürür ('ilişkili maddeler'
    taraması için ek başlık kaynağı)."""
    url = (
        "https://tr.wikipedia.org/w/api.php"
        "?action=query"
        "&prop=links"
        "&plnamespace=0"
        f"&pllimit={count}"
        f"&titles={urllib.parse.quote(title, safe='')}"
        "&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", [])
            if not pages:
                return []
            links = pages[0].get("links", [])
            return [l["title"] for l in links if l.get("title")]
    except Exception:
        return []


# Backward compat alias used by old generate_questions.py
def fetch_raw_titles(seed: int = 1) -> list[str]:  # noqa: ARG001 – seed ignored
    return fetch_random_titles(20)
