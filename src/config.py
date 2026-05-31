"""Liest die Such-Konfiguration (YAML) und die Secrets (Umgebung/.env).

Trennt absichtlich zwei Dinge:
  - WAS gesucht wird  -> config/search_config.yaml  (oeffentlich, im Repo)
  - GEHEIME Keys      -> Umgebungsvariablen / .env    (nie im Repo)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

try:
    # Laedt eine lokale .env-Datei, falls vorhanden (nur fuer den eigenen PC).
    # Auf GitHub Actions gibt es keine .env -> dann kommen die Werte aus Secrets.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


class ConfigError(Exception):
    """Verstaendlicher Fehler, wenn etwas an der Konfiguration nicht stimmt."""


# ---------------------------------------------------------------------------
# Secrets (API-Keys) aus der Umgebung
# ---------------------------------------------------------------------------
@dataclass
class Secrets:
    search_provider: str
    brave_api_key: str | None
    serpapi_api_key: str | None
    supabase_url: str | None
    supabase_key: str | None

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)


def load_secrets() -> Secrets:
    """Liest die geheimen Schluessel aus den Umgebungsvariablen."""
    provider = os.getenv("SEARCH_PROVIDER", "brave").strip().lower()
    secrets = Secrets(
        search_provider=provider,
        brave_api_key=os.getenv("BRAVE_API_KEY"),
        serpapi_api_key=os.getenv("SERPAPI_API_KEY"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
    )

    # Freundliche Pruefung mit klarer Fehlermeldung.
    if provider == "brave" and not secrets.brave_api_key:
        raise ConfigError(
            "Kein BRAVE_API_KEY gefunden.\n"
            "  -> Lokal: trage ihn in die Datei .env ein.\n"
            "  -> GitHub Actions: trage ihn unter Settings -> Secrets -> Actions ein."
        )
    if provider == "serpapi" and not secrets.serpapi_api_key:
        raise ConfigError(
            "SEARCH_PROVIDER=serpapi gesetzt, aber kein SERPAPI_API_KEY gefunden."
        )
    if provider not in ("brave", "serpapi"):
        raise ConfigError(
            f"Unbekannter SEARCH_PROVIDER '{provider}'. Erlaubt: 'brave' oder 'serpapi'."
        )
    return secrets


# ---------------------------------------------------------------------------
# Such-Konfiguration aus der YAML-Datei
# ---------------------------------------------------------------------------
@dataclass
class Settings:
    max_results_per_query: int = 10
    search_language: str = "de"
    request_delay_seconds: float = 2.0
    respect_robots_txt: bool = True
    min_text_length: int = 200
    frequency_analysis: bool = True


@dataclass
class SearchConfig:
    run_name: str
    keywords: list[str] = field(default_factory=list)
    phrases: list[str] = field(default_factory=list)
    topics: list[dict[str, Any]] = field(default_factory=list)
    start_urls: list[str] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)


def load_search_config(path: str) -> SearchConfig:
    """Liest config/search_config.yaml und prueft sie auf typische Fehler."""
    if not os.path.exists(path):
        raise ConfigError(
            f"Konfigurationsdatei nicht gefunden: {path}\n"
            "  -> Lege sie an oder kopiere config/search_config.example.yaml."
        )

    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(
                "Die Config-Datei ist kein gueltiges YAML (Tippfehler bei "
                f"Einrueckung/Anfuehrungszeichen?). Details: {exc}"
            ) from exc

    settings_raw = raw.get("settings") or {}
    settings = Settings(
        max_results_per_query=int(settings_raw.get("max_results_per_query", 10)),
        search_language=str(settings_raw.get("search_language", "de")),
        request_delay_seconds=float(settings_raw.get("request_delay_seconds", 2.0)),
        respect_robots_txt=bool(settings_raw.get("respect_robots_txt", True)),
        min_text_length=int(settings_raw.get("min_text_length", 200)),
        frequency_analysis=bool(settings_raw.get("frequency_analysis", True)),
    )

    cfg = SearchConfig(
        run_name=str(raw.get("run_name", "unbenannter-lauf")),
        keywords=[s for s in (raw.get("keywords") or []) if s],
        phrases=[s for s in (raw.get("phrases") or []) if s],
        topics=[t for t in (raw.get("topics") or []) if t],
        start_urls=[s for s in (raw.get("start_urls") or []) if s],
        settings=settings,
    )

    if not (cfg.keywords or cfg.phrases or cfg.topics or cfg.start_urls):
        raise ConfigError(
            "Deine Config enthaelt keine Suchbegriffe. Trage mindestens ein "
            "keyword, eine phrase, ein topic oder eine start_url ein."
        )
    return cfg
