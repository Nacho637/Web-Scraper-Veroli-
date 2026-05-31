"""Analyse-Modul: einfache Haeufigkeitsauswertung pro Keyword.

Liefert eine schnelle quantitative Uebersicht:
  - wie viele Treffer pro ausloesendem Keyword
  - wie oft der Begriff im Volltext vorkommt (Gesamtzahl der Nennungen)
  - Anzahl unterschiedlicher Domains

Das Ergebnis wird als CSV exportiert und in der Konsole angezeigt.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict

from .extract import Document


def keyword_frequencies(documents: list[Document]) -> list[dict]:
    """Berechnet pro Keyword: Trefferzahl, Wort-Nennungen, Domains."""
    hits = defaultdict(int)
    mentions = defaultdict(int)
    domains = defaultdict(set)

    for doc in documents:
        kw = doc.trigger_keyword
        hits[kw] += 1
        domains[kw].add(doc.domain)
        # Einfache, case-insensitive Zaehlung der Nennungen im Volltext.
        mentions[kw] += doc.full_text.lower().count(kw.lower())

    rows = []
    for kw in sorted(hits, key=lambda k: hits[k], reverse=True):
        rows.append(
            {
                "keyword": kw,
                "treffer": hits[kw],
                "nennungen_im_text": mentions[kw],
                "anzahl_domains": len(domains[kw]),
            }
        )
    return rows


def export_frequencies(rows: list[dict], run_name: str, out_dir: str = "exports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in run_name)
    path = os.path.join(out_dir, f"{safe}_haeufigkeiten.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["keyword", "treffer", "nennungen_im_text", "anzahl_domains"],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def print_frequencies(rows: list[dict]) -> None:
    if not rows:
        return
    print("\n  Haeufigkeitsauswertung pro Keyword:")
    print(f"  {'Keyword':<28}{'Treffer':>8}{'Nennungen':>12}{'Domains':>10}")
    print("  " + "-" * 56)
    for r in rows:
        print(
            f"  {r['keyword'][:27]:<28}{r['treffer']:>8}"
            f"{r['nennungen_im_text']:>12}{r['anzahl_domains']:>10}"
        )
