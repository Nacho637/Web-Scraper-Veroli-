"""Export-Modul: schreibt die Treffer als CSV und JSON.

Beide Formate sind direkt importierbar in:
  - R            (read.csv / jsonlite)
  - Python/pandas (pd.read_csv / pd.read_json)
  - MAXQDA       (Import strukturierter Daten / CSV)

Nur Standardbibliothek (csv, json) - keine schweren Zusatzpakete noetig.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict
from datetime import datetime

from .extract import Document

FIELDNAMES = [
    "title",
    "url",
    "domain",
    "language",
    "published_date",
    "run_name",
    "trigger_keyword",
    "trigger_type",
    "topic",
    "content_hash",
    "scraped_at",
    "full_text",
]


def _timestamped_name(run_name: str, ext: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in run_name)
    return f"{safe}_{stamp}.{ext}"


def export_documents(
    documents: list[Document], run_name: str, out_dir: str = "exports"
) -> tuple[str, str]:
    """Schreibt CSV + JSON und gibt die beiden Dateipfade zurueck."""
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for doc in documents:
        row = asdict(doc)
        row["run_name"] = run_name
        rows.append(row)

    # --- CSV (Semikolon-getrennt: oeffnet sauber in deutschem Excel) ----
    csv_path = os.path.join(out_dir, _timestamped_name(run_name, "csv"))
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # --- JSON -------------------------------------------------------------
    json_path = os.path.join(out_dir, _timestamped_name(run_name, "json"))
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)

    return csv_path, json_path
