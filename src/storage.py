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
            print(f"  WARNUNG: Speichern in Supabase fehlgeschlagen: {exc}")
            print("  -> Die Daten sind trotzdem als CSV/JSON exportiert worden.")
            return 0
