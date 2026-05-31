"""Web-Scraper fuer die sozialwissenschaftliche Forschung.

Modular aufgebaut:
  config   -> liest die Konfiguration und die Secrets
  search   -> findet URLs ueber eine Such-API (Brave/SerpAPI) + Start-URLs
  fetcher  -> laedt Webseiten (robots.txt + Rate-Limiting)
  extract  -> trennt Haupttext von Navigation/Werbung, erkennt Sprache
  storage  -> speichert die Treffer in Supabase
  export   -> schreibt CSV/JSON fuer R, pandas, MAXQDA
  analyze  -> einfache Haeufigkeitsauswertung
  main     -> verbindet alles und gibt Fortschritt aus
"""

__version__ = "1.0.0"
