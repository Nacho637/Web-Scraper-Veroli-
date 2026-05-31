"""Such-Modul: findet URLs zu Suchbegriffen ueber eine Such-API.

Bewusst ueber eine offizielle Such-API (Brave oder SerpAPI) statt "blindem"
Crawlen des ganzen Webs:
  - rechtlich/ethisch sauberer (keine massenhaften ungefragten Zugriffe)
  - viel bessere Trefferqualitaet
  - planbare Kosten

Modular: Jeder Anbieter ist eine eigene Funktion. Weitere Quellen (z. B.
spaeter Social Media) lassen sich als zusaetzliche Provider ergaenzen.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import SearchConfig, Secrets


@dataclass
class SearchTask:
    """Ein einzelner Suchauftrag (ein Begriff)."""

    query: str          # der tatsaechlich gesuchte Text
    trigger_keyword: str  # was wir als ausloesenden Begriff speichern
    trigger_type: str   # "keyword" | "phrase" | "topic"
    topic: str | None = None


@dataclass
class SearchHit:
    """Ein Treffer der Such-API (noch ohne Volltext)."""

    url: str
    title: str | None
    trigger_keyword: str
    trigger_type: str
    topic: str | None = None


def build_search_tasks(cfg: SearchConfig) -> list[SearchTask]:
    """Wandelt die Config in eine flache Liste von Suchauftraegen um."""
    tasks: list[SearchTask] = []

    for kw in cfg.keywords:
        tasks.append(SearchTask(query=kw, trigger_keyword=kw, trigger_type="keyword"))

    for phrase in cfg.phrases:
        # Anfuehrungszeichen erzwingen exakte Phrasensuche bei der Such-API.
        tasks.append(
            SearchTask(
                query=f'"{phrase}"',
                trigger_keyword=phrase,
                trigger_type="phrase",
            )
        )

    for topic in cfg.topics:
        name = topic.get("name", "thema")
        for term in topic.get("terms", []):
            tasks.append(
                SearchTask(
                    query=term,
                    trigger_keyword=term,
                    trigger_type="topic",
                    topic=name,
                )
            )
    return tasks


# ---------------------------------------------------------------------------
# Anbieter: Brave Search API
# ---------------------------------------------------------------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _brave_search(query: str, api_key: str, count: int, language: str) -> list[dict]:
    resp = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
        params={"q": query, "count": count, "search_lang": language},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return (data.get("web") or {}).get("results", []) or []


# ---------------------------------------------------------------------------
# Anbieter: SerpAPI (Google-Ergebnisse)
# ---------------------------------------------------------------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _serpapi_search(query: str, api_key: str, count: int, language: str) -> list[dict]:
    resp = requests.get(
        "https://serpapi.com/search.json",
        params={
            "q": query,
            "num": count,
            "hl": language,
            "engine": "google",
            "api_key": api_key,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("organic_results", []) or []


def run_search(task: SearchTask, secrets: Secrets, cfg: SearchConfig) -> list[SearchHit]:
    """Fuehrt EINEN Suchauftrag aus und gibt die Treffer-URLs zurueck."""
    count = cfg.settings.max_results_per_query
    lang = cfg.settings.search_language
    hits: list[SearchHit] = []

    if secrets.search_provider == "brave":
        results = _brave_search(task.query, secrets.brave_api_key, count, lang)
        for r in results:
            hits.append(
                SearchHit(
                    url=r.get("url"),
                    title=r.get("title"),
                    trigger_keyword=task.trigger_keyword,
                    trigger_type=task.trigger_type,
                    topic=task.topic,
                )
            )
    else:  # serpapi
        results = _serpapi_search(task.query, secrets.serpapi_api_key, count, lang)
        for r in results:
            hits.append(
                SearchHit(
                    url=r.get("link"),
                    title=r.get("title"),
                    trigger_keyword=task.trigger_keyword,
                    trigger_type=task.trigger_type,
                    topic=task.topic,
                )
            )

    # Nur Treffer mit gueltiger URL behalten.
    return [h for h in hits if h.url and h.url.startswith("http")]


def start_url_hits(cfg: SearchConfig) -> list[SearchHit]:
    """Wandelt feste Start-URLs aus der Config in Treffer um."""
    return [
        SearchHit(
            url=url,
            title=None,
            trigger_keyword="(start_url)",
            trigger_type="start_url",
            topic=None,
        )
        for url in cfg.start_urls
    ]
