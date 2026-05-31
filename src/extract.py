"""Extraktions-Modul: holt den sauberen Haupttext aus HTML.

Nutzt 'trafilatura' - eine in der Forschung etablierte Bibliothek, die
Navigation, Werbung, Kommentare etc. zuverlaessig entfernt und Metadaten
(Titel, Datum) mitliefert. Ausserdem: automatische Sprach-Erkennung und
ein Inhalts-Fingerabdruck fuer die Deduplizierung.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import py3langid as langid
import trafilatura


@dataclass
class Document:
    """Ein fertig aufbereiteter Treffer, bereit zum Speichern."""

    url: str
    domain: str
    title: str | None
    full_text: str
    language: str | None
    published_date: str | None
    content_hash: str
    scraped_at: str
    trigger_keyword: str
    trigger_type: str
    topic: str | None


def _domain(url: str) -> str:
    netloc = urlparse(url).netloc
    return netloc[4:] if netloc.startswith("www.") else netloc


def _detect_language(text: str) -> str | None:
    try:
        lang, _confidence = langid.classify(text)
        return lang
    except Exception:
        return None


def _content_hash(text: str) -> str:
    """Fingerabdruck des normalisierten Textes - gleicher Text = gleicher Hash."""
    normalized = " ".join(text.split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_document(
    html: str,
    url: str,
    trigger_keyword: str,
    trigger_type: str,
    topic: str | None,
    min_text_length: int,
    fallback_title: str | None = None,
) -> Document | None:
    """Macht aus rohem HTML ein sauberes Document - oder None, wenn zu duenn."""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not text or len(text) < min_text_length:
        return None

    # Metadaten (Titel, Datum) - so gut es geht aus der Seite lesen.
    title = fallback_title
    published = None
    try:
        meta = trafilatura.extract_metadata(html)
        if meta:
            title = meta.title or title
            published = meta.date
    except Exception:
        pass

    return Document(
        url=url,
        domain=_domain(url),
        title=title,
        full_text=text,
        language=_detect_language(text),
        published_date=published,
        content_hash=_content_hash(text),
        scraped_at=datetime.now(timezone.utc).isoformat(),
        trigger_keyword=trigger_keyword,
        trigger_type=trigger_type,
        topic=topic,
    )
