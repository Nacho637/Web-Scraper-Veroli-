"""Laedt Webseiten herunter - hoeflich und regelkonform.

Beachtet:
  - robots.txt jeder Webseite (kann in der Config abgeschaltet werden)
  - Rate-Limiting (Wartezeit zwischen Abrufen)
  - einen ehrlichen User-Agent (sagt, wer wir sind)
"""

from __future__ import annotations

import time
import urllib.robotparser as robotparser
from urllib.parse import urlparse

import requests

USER_AGENT = (
    "SocialScienceResearchScraper/1.0 "
    "(+https://github.com/; akademische Forschung; Kontakt via Repo)"
)


class Fetcher:
    """Kapselt das Herunterladen inkl. robots.txt-Pruefung und Wartezeit."""

    def __init__(self, delay_seconds: float = 2.0, respect_robots: bool = True):
        self.delay_seconds = delay_seconds
        self.respect_robots = respect_robots
        self._robots_cache: dict[str, robotparser.RobotFileParser | None] = {}
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    # --- robots.txt -------------------------------------------------------
    def _is_allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        if base not in self._robots_cache:
            rp = robotparser.RobotFileParser()
            rp.set_url(f"{base}/robots.txt")
            try:
                rp.read()
                self._robots_cache[base] = rp
            except Exception:
                # robots.txt nicht lesbar -> vorsichtig sein, aber nicht blockieren.
                self._robots_cache[base] = None

        rp = self._robots_cache[base]
        if rp is None:
            return True
        return rp.can_fetch(USER_AGENT, url)

    # --- Rate-Limiting ----------------------------------------------------
    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_request_time = time.time()

    # --- oeffentliche Methode --------------------------------------------
    def fetch(self, url: str) -> str | None:
        """Gibt das HTML der Seite zurueck - oder None, wenn nicht erlaubt/fehlgeschlagen."""
        if not self._is_allowed(url):
            print(f"    robots.txt verbietet Abruf - uebersprungen: {url}")
            return None

        self._wait()
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "text" not in ctype:
                print(f"    Keine Textseite ({ctype}) - uebersprungen: {url}")
                return None
            return resp.text
        except requests.RequestException as exc:
            print(f"    Abruf fehlgeschlagen ({exc.__class__.__name__}): {url}")
            return None
