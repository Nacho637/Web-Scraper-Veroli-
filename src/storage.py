"""Speicher-Modul: schreibt Treffer in die Supabase-Datenbank.

Verwendet ein "Upsert" auf der Spalte 'url': Wird dieselbe URL erneut
gefunden, wird der vorhandene Eintrag aktualisiert statt doppelt angelegt
(Deduplizierung auf Datenbank-Ebene).

Supabase ist optional: Ist kein Key gesetzt, ueberspringt der Scraper das
Speichern und exportiert nur die lokalen CSV/JSON-Dateien.
"""

from __future__ import annotations

from dataclasses import asdict

from .config import Secrets
from .extract import Document


class StorageError(Exception):
    """Klarer Fehler beim Speichern in Supabase (mit Tipp zur Behebung)."""


class SupabaseStore:
    def __init__(self, secrets: Secrets):
        self.enabled = secrets.has_supabase
        self.client = None
        if self.enabled:
            from supabase import create_client

            self.client = create_client(secrets.supabase_url, secrets.supabase_key)

    def save_many(self, documents: list[Document], run_name: str) -> int:
        """Speichert alle Dokumente. Gibt die Anzahl gespeicherter Zeilen zurueck."""
        if not self.enabled or not documents:
            return 0

        rows = []
        for doc in documents:
            row = asdict(doc)
            row["run_name"] = run_name
            rows.append(row)

        try:
            # on_conflict="url" -> doppelte URLs aktualisieren statt einfuegen.
            self.client.table("scrape_results").upsert(
                rows, on_conflict="url"
            ).execute()
            return len(rows)
        except Exception as exc:
            raise StorageError(_diagnose(exc)) from exc


def _diagnose(exc: Exception) -> str:
    """Macht aus einem technischen Supabase-Fehler eine verstaendliche Erklaerung."""
    msg = str(exc)
    low = msg.lower()

    if "row-level security" in low or "row level security" in low or "violates row" in low:
        return (
            "Supabase hat das Schreiben durch 'Row Level Security' (RLS) blockiert.\n"
            "  Ursache: Es wurde wahrscheinlich der ANON-Key benutzt, oder RLS ist "
            "ohne passende Policy aktiv.\n"
            "  LOESUNG: Trage als Secret SUPABASE_KEY den 'service_role'-Key ein "
            "(Supabase -> Project Settings -> API -> service_role -> Reveal).\n"
            f"  Originalmeldung: {msg}"
        )
    if "no unique or exclusion constraint" in low or "on conflict" in low:
        return (
            "Der Datenbank fehlt der eindeutige Index auf der Spalte 'url'.\n"
            "  LOESUNG: Fuehre sql/schema.sql im Supabase SQL-Editor erneut aus.\n"
            f"  Originalmeldung: {msg}"
        )
    if "could not find the table" in low or "does not exist" in low or "pgrst205" in low:
        return (
            "Die Tabelle 'scrape_results' wurde nicht gefunden.\n"
            "  LOESUNG: Fuehre sql/schema.sql im Supabase SQL-Editor aus.\n"
            f"  Originalmeldung: {msg}"
        )
    if "invalid api key" in low or "jwt" in low or "unauthorized" in low or "401" in low:
        return (
            "Der Supabase-Schluessel (SUPABASE_KEY) wird abgelehnt.\n"
            "  LOESUNG: Pruefe SUPABASE_URL und SUPABASE_KEY in den GitHub-Secrets "
            "(keine Leerzeichen, service_role-Key verwenden).\n"
            f"  Originalmeldung: {msg}"
        )
    return f"Speichern in Supabase fehlgeschlagen. Originalmeldung: {msg}"
