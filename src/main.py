"""Haupt-Programm: startet einen kompletten Suchlauf.

Aufruf (ein einziger Befehl):
    python -m src.main
    python -m src.main --config config/search_config.yaml

Ablauf:
    1. Config + Secrets laden
    2. Suchbegriffe -> URLs (Such-API + Start-URLs)
    3. URLs herunterladen (robots.txt + Rate-Limiting)
    4. Haupttext extrahieren, Sprache erkennen
    5. Deduplizieren
    6. In Supabase speichern (falls konfiguriert)
    7. CSV/JSON exportieren
    8. Optional: Haeufigkeitsauswertung
"""

from __future__ import annotations

import argparse
import sys

from . import analyze, export
from .config import ConfigError, load_search_config, load_secrets
from .extract import Document, extract_document
from .fetcher import Fetcher
from .search import build_search_tasks, run_search, start_url_hits
from .storage import SupabaseStore


def _banner(text: str) -> None:
    print("\n" + "=" * 64)
    print(f"  {text}")
    print("=" * 64)


def run(config_path: str) -> int:
    _banner("Web-Scraper fuer sozialwissenschaftliche Forschung")

    # --- 1) Konfiguration laden ------------------------------------------
    try:
        cfg = load_search_config(config_path)
        secrets = load_secrets()
    except ConfigError as exc:
        print(f"\nFEHLER in der Konfiguration:\n  {exc}\n")
        return 1

    print(f"  Lauf-Name:        {cfg.run_name}")
    print(f"  Such-Anbieter:    {secrets.search_provider}")
    print(f"  Supabase aktiv:   {'ja' if secrets.has_supabase else 'nein (nur Datei-Export)'}")
    print(f"  Keywords:         {len(cfg.keywords)}")
    print(f"  Phrasen:          {len(cfg.phrases)}")
    print(f"  Themenfelder:     {len(cfg.topics)}")
    print(f"  Feste Start-URLs: {len(cfg.start_urls)}")

    # --- 2) Suchbegriffe -> Treffer-URLs ---------------------------------
    _banner("Schritt 1/4: Such-API abfragen")
    tasks = build_search_tasks(cfg)
    all_hits = list(start_url_hits(cfg))

    for i, task in enumerate(tasks, start=1):
        label = f"{task.trigger_type}: {task.trigger_keyword}"
        print(f"  [{i}/{len(tasks)}] Suche nach {label} ...", flush=True)
        try:
            hits = run_search(task, secrets, cfg)
            print(f"        -> {len(hits)} Treffer-URLs")
            all_hits.extend(hits)
        except Exception as exc:
            print(f"        WARNUNG: Suche fehlgeschlagen: {exc}")

    # URLs schon hier deduplizieren (gleiche URL nur einmal herunterladen).
    seen_urls: set[str] = set()
    unique_hits = []
    for hit in all_hits:
        if hit.url not in seen_urls:
            seen_urls.add(hit.url)
            unique_hits.append(hit)

    print(f"\n  Insgesamt {len(unique_hits)} eindeutige URLs zum Abrufen.")
    if not unique_hits:
        print("  Keine URLs gefunden - bitte Keywords pruefen. Abbruch.")
        return 0

    # --- 3) + 4) Herunterladen und Text extrahieren ----------------------
    _banner("Schritt 2/4: Seiten herunterladen und Text extrahieren")
    fetcher = Fetcher(
        delay_seconds=cfg.settings.request_delay_seconds,
        respect_robots=cfg.settings.respect_robots_txt,
    )

    documents: list[Document] = []
    seen_hashes: set[str] = set()

    for i, hit in enumerate(unique_hits, start=1):
        print(f"  [{i}/{len(unique_hits)}] {hit.url}", flush=True)
        html = fetcher.fetch(hit.url)
        if not html:
            continue

        doc = extract_document(
            html=html,
            url=hit.url,
            trigger_keyword=hit.trigger_keyword,
            trigger_type=hit.trigger_type,
            topic=hit.topic,
            min_text_length=cfg.settings.min_text_length,
            fallback_title=hit.title,
        )
        if not doc:
            print("        -> kein ausreichender Haupttext - uebersprungen")
            continue

        # Deduplizierung nach Inhalt (gleicher Text auf anderer URL).
        if doc.content_hash in seen_hashes:
            print("        -> inhaltliches Duplikat - uebersprungen")
            continue
        seen_hashes.add(doc.content_hash)

        documents.append(doc)
        print(f"        -> OK: '{(doc.title or '(ohne Titel)')[:60]}' "
              f"[{doc.language}], {len(doc.full_text)} Zeichen")

    print(f"\n  {len(documents)} verwertbare Dokumente gesammelt.")
    if not documents:
        print("  Nichts zu speichern. Abbruch.")
        return 0

    # --- 5) Speichern in Supabase ----------------------------------------
    _banner("Schritt 3/4: In Supabase speichern")
    store = SupabaseStore(secrets)
    if store.enabled:
        saved = store.save_many(documents, cfg.run_name)
        print(f"  {saved} Datensaetze in Supabase gespeichert/aktualisiert.")
    else:
        print("  Supabase nicht konfiguriert - uebersprungen (nur Datei-Export).")

    # --- 6) Export CSV/JSON ----------------------------------------------
    _banner("Schritt 4/4: CSV/JSON exportieren")
    csv_path, json_path = export.export_documents(documents, cfg.run_name)
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")

    # --- 7) Haeufigkeitsauswertung ---------------------------------------
    if cfg.settings.frequency_analysis:
        rows = analyze.keyword_frequencies(documents)
        freq_path = analyze.export_frequencies(rows, cfg.run_name)
        analyze.print_frequencies(rows)
        print(f"\n  Haeufigkeiten-CSV: {freq_path}")

    _banner(f"Fertig! {len(documents)} Treffer gespeichert.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Web-Scraper fuer sozialwissenschaftliche Forschung."
    )
    parser.add_argument(
        "--config",
        default="config/search_config.yaml",
        help="Pfad zur Such-Konfiguration (Standard: config/search_config.yaml)",
    )
    args = parser.parse_args()
    sys.exit(run(args.config))


if __name__ == "__main__":
    main()
