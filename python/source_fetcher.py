"""Encyclopedic source fetcher for Turkish knowledge content."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

USER_AGENT = "KimBilgi/1.0 (educational quiz; contact: dev@example.com)"
TIMEOUT = 20


def fetch_article(title: str) -> str:
    url = (
        "https://tr.wikipedia.org/api/rest_v1/page/summary/"
        + urllib.parse.quote(title)
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("extract", "")
    except Exception:
        return ""


def fetch_raw_titles(seed: int) -> list[str]:
    url = (
        "https://tr.wikipedia.org/w/api.php?action=query&list=random"
        "&rnnamespace=0&rnlimit=500&format=json&rnlimit=500"
        f"&rnseed={seed}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [item["title"] for item in data.get("query", {}).get("random", [])]
    except Exception:
        return []


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text
