# Web-Scraper für die sozialwissenschaftliche Forschung

Ein konfigurierbarer Scraper, der **klassische Webseiten und News-Seiten** nach
**Themen, Phrasen und einzelnen Wörtern** durchsucht und die Treffer
**strukturiert für quantitative und qualitative Analyse** speichert
(CSV, JSON, Supabase-Datenbank).

Du brauchst **keine Programmierkenntnisse** und musst **nichts auf deinem PC
installieren**. Ein Suchlauf wird per Knopfdruck auf GitHub gestartet.

> **Social Media** ist (noch) nicht Teil des Projekts. Der Code ist aber
> modular: weitere Quellen lassen sich später als eigenes Modul ergänzen.

---

## Inhaltsverzeichnis

1. [Vorab-Setup-Checkliste](#1-vorab-setup-checkliste)
2. [Warum GitHub Actions statt Vercel?](#2-warum-github-actions-statt-vercel)
3. [Projektstruktur](#3-projektstruktur)
4. [Quickstart in 10 Minuten](#4-quickstart-in-10-minuten)
5. [GitHub Actions Secrets einrichten (Schritt für Schritt)](#5-github-actions-secrets-einrichten-schritt-für-schritt)
6. [Bedienungsanleitung](#6-bedienungsanleitung)
7. [Ergebnisse ansehen und weiterverwerten](#7-ergebnisse-ansehen-und-weiterverwerten)
8. [Lokale Nutzung am eigenen PC (optional)](#8-lokale-nutzung-am-eigenen-pc-optional)
9. [Rechtliches & Forschungsethik](#9-rechtliches--forschungsethik)
10. [Technische Entscheidungen (kurz begründet)](#10-technische-entscheidungen-kurz-begründet)

---

## 1. Vorab-Setup-Checkliste

Alles, was du **einmalig** brauchst, bevor irgendetwas läuft. Reihenfolge einhalten.

| # | Was | Kostenlos? | Link |
|---|-----|-----------|------|
| 1 | **GitHub-Account** (hast du wahrscheinlich schon) | ✅ kostenlos | https://github.com/signup |
| 2 | **Dieses Repository** (ist bereits deins) | ✅ kostenlos | dein Repo |
| 3 | **Supabase-Account** (Datenbank) | ✅ kostenloser „Free"-Plan reicht | https://supabase.com |
| 4 | **Brave Search API-Account** (Suche) | ✅ Free-Plan: ~2.000 Suchen/Monat, 1 Anfrage/Sek. | https://brave.com/search/api/ |
| 5 | *(Alternative zu 4)* **SerpAPI** (Google-Ergebnisse) | ⚠️ Free: 100 Suchen/Monat, danach kostenpflichtig | https://serpapi.com |

**Wichtig zum Verständnis:**
- Du musst **kein Python installieren** und **nichts klonen**, solange du den
  Scraper über GitHub Actions startest (empfohlen). Punkt 8 erklärt die
  optionale lokale Nutzung.
- **Empfehlung Such-API: Brave.** Großzügiger kostenloser Plan, einfache
  Anmeldung, datenschutzfreundlich. SerpAPI liefert echte Google-Ergebnisse,
  ist aber im Free-Plan stark begrenzt.
- **Kostenhinweis:** GitHub Actions ist für öffentliche Repos kostenlos und für
  private Repos großzügig im Freikontingent (2.000 Minuten/Monat). Ein normaler
  Suchlauf dauert wenige Minuten.

---

## 2. Warum GitHub Actions statt Vercel?

Kurz und ehrlich, warum **GitHub Actions** hier die richtige Wahl ist – und
warum **Vercel hier nicht passt**:

- **Vercel ist für Webseiten/APIs gebaut**, die auf Besucher *reagieren* und
  nach kurzer Zeit (Sekunden) automatisch abgeschaltet werden. Ein Suchlauf, der
  viele Seiten nacheinander mit Wartezeiten (Rate-Limiting) abruft, **läuft zu
  lange** für diese kurzen Zeitfenster.
- **GitHub Actions ist für genau solche „Aufgaben" (Jobs) gebaut**: ein Skript
  starten, durchlaufen lassen (bis zu 6 Stunden möglich), Ergebnis ablegen,
  fertig. Das ist exakt dein Nutzungsmodell („einmaliger Suchlauf").
- **Ein Ort für alles:** Code, der „Run"-Knopf, deine Keyword-Config und die
  Geheimnisse (Secrets) liegen alle an einem Platz – in GitHub. Kein zweiter
  Dienst, kein zusätzliches Deployment.
- **Editierbar im Browser:** Du änderst Keywords direkt auf github.com und
  startest den Lauf mit einem Klick – ganz ohne lokale Installation.

---

## 3. Projektstruktur

```
Web-Scraper-Veroli-/
├── README.md                     <- diese Anleitung
├── requirements.txt              <- Liste der Python-Pakete (automatisch installiert)
├── .gitignore                    <- schützt Geheimnisse/Exporte vor dem Hochladen
├── .env.example                  <- Vorlage für lokale Secrets (kopieren -> .env)
│
├── config/
│   ├── search_config.yaml        <- DEINE Keywords (die EINZIGE Datei, die du editierst)
│   └── search_config.example.yaml<- Sicherungs-Vorlage
│
├── src/                          <- der modulare Programmcode
│   ├── main.py                   <- Startpunkt (verbindet alle Module)
│   ├── config.py                 <- liest Config + Secrets
│   ├── search.py                 <- Suche über Brave/SerpAPI + Start-URLs
│   ├── fetcher.py                <- lädt Seiten (robots.txt + Rate-Limiting)
│   ├── extract.py                <- Haupttext sauber extrahieren + Sprache erkennen
│   ├── storage.py                <- speichert in Supabase
│   ├── export.py                 <- schreibt CSV/JSON
│   └── analyze.py                <- Häufigkeitsauswertung
│
├── sql/
│   └── schema.sql                <- Datenbank-Tabelle für Supabase (einmal einfügen)
│
├── .github/workflows/
│   └── scrape.yml                <- der „Run workflow"-Knopf (GitHub Actions)
│
└── exports/                      <- hier landen lokale CSV/JSON-Dateien
```

---

## 4. Quickstart in 10 Minuten

Von null bis zum ersten erfolgreichen Suchlauf. Jeder Schritt einzeln.

### Schritt 1 — Supabase-Projekt anlegen (≈3 Min.)
1. Gehe zu **https://supabase.com** und klicke **„Start your project"** → mit
   GitHub anmelden.
2. Klicke **„New project"**. Vergib einen Namen (z. B. `scraper`) und ein
   **Datenbank-Passwort** (notieren). Region: nimm eine in Europa (z. B.
   `Central EU (Frankfurt)`).
3. Warte ~1 Minute, bis das Projekt bereit ist.

### Schritt 2 — Datenbank-Tabelle anlegen (≈1 Min.)
1. Klicke im Supabase-Projekt links auf **„SQL Editor"**.
2. Klicke **„New query"**.
3. Öffne in deinem Repo die Datei **`sql/schema.sql`**, kopiere den **gesamten**
   Inhalt und füge ihn ins SQL-Fenster ein.
4. Klicke unten rechts auf **„Run"**. Es sollte „Success" erscheinen.

### Schritt 3 — Supabase-Zugangsdaten kopieren (≈1 Min.)
1. Klicke links auf das Zahnrad **„Project Settings"** → **„API"**.
2. Kopiere dir zwei Werte (gleich brauchst du sie für die Secrets):
   - **Project URL** (z. B. `https://abcd.supabase.co`) → das wird `SUPABASE_URL`
   - **service_role**-Key (unter „Project API keys", auf „Reveal" klicken) →
     das wird `SUPABASE_KEY`
   > Der `service_role`-Key darf **nur** als GitHub-Secret verwendet werden,
   > **niemals** öffentlich teilen oder in den Code schreiben.

### Schritt 4 — Brave Search API-Key holen (≈2 Min.)
1. Gehe zu **https://brave.com/search/api/** → **„Get started"** / anmelden.
2. Wähle den **Free**-Plan.
3. Erstelle einen **API Key** und kopiere ihn → das wird `BRAVE_API_KEY`.

### Schritt 5 — Secrets in GitHub eintragen (≈2 Min.)
Folge dem nächsten Abschnitt **[5. GitHub Actions Secrets einrichten](#5-github-actions-secrets-einrichten-schritt-für-schritt)**
und lege diese drei Secrets an:
`BRAVE_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.

### Schritt 6 — Keywords eintragen (≈1 Min.)
1. Öffne im Repo **`config/search_config.yaml`** und klicke das **Stift-Symbol**
   (Edit).
2. Trage deine Suchbegriffe ein (siehe [Bedienungsanleitung](#6-bedienungsanleitung)).
3. Klicke **„Commit changes"**.

### Schritt 7 — Suchlauf starten (≈1 Min.)
1. Klicke im Repo oben auf den Reiter **„Actions"**.
2. Links auf **„Suchlauf starten (Scraper)"**.
3. Rechts auf **„Run workflow"** → (Anbieter `brave` lassen) → grüner Button
   **„Run workflow"**.
4. Klicke auf den laufenden Eintrag, um live den Fortschritt zu sehen.

### Schritt 8 — Ergebnisse ansehen
- **In Supabase:** Projekt → **„Table Editor"** → Tabelle `scrape_results`.
- **Als Datei:** Auf der Lauf-Seite ganz unten unter **„Artifacts"** →
  **„scraper-ergebnisse"** herunterladen (enthält CSV + JSON).

🎉 **Fertig.**

---

## 5. GitHub Actions Secrets einrichten (Schritt für Schritt)

Secrets sind „Tresore" für deine API-Keys. Sie sind **nicht öffentlich
sichtbar** und tauchen **nie im Code** auf.

1. Öffne dein Repo auf **github.com**.
2. Klicke oben auf den Reiter **„Settings"** (ganz rechts).
3. In der linken Leiste: **„Secrets and variables"** → **„Actions"**.
4. Klicke den grünen Button **„New repository secret"**.
5. Lege **nacheinander** diese Secrets an (jeweils Name + Wert, dann
   „Add secret"):

   | Name (genau so schreiben) | Wert |
   |---------------------------|------|
   | `BRAVE_API_KEY`           | dein Brave-API-Key |
   | `SUPABASE_URL`            | deine Supabase Project URL |
   | `SUPABASE_KEY`            | dein Supabase `service_role`-Key |

   *(Nur falls du SerpAPI statt Brave nutzt, zusätzlich:* `SERPAPI_API_KEY` *)*

6. Fertig. Die Secrets werden vom Workflow automatisch verwendet – du musst sie
   nirgends in den Code eintragen.

> **Tipp:** Tippfehler im Namen sind der häufigste Fehler. Die Namen müssen
> **exakt** so heißen wie oben (Großschreibung beachten).

---

## 6. Bedienungsanleitung

### Wie trage ich Keywords ein?

Du bearbeitest **nur eine Datei**: `config/search_config.yaml`.
Im GitHub-Browser: Datei öffnen → Stift-Symbol → ändern → „Commit changes".

Es gibt vier Arten, nach etwas zu suchen:

```yaml
# Einzelne Schlagwörter (jeweils eine eigene Suche)
keywords:
  - "Klimawandel"
  - "Energiewende"

# Exakte Phrasen (genaue Wortfolge)
phrases:
  - "soziale Gerechtigkeit"

# Themenfelder mit Synonymen (Treffer werden dem Thema zugeordnet)
topics:
  - name: "migration"
    terms:
      - "Migration"
      - "Zuwanderung"
      - "Geflüchtete"

# Feste Start-URLs (werden immer zusätzlich abgerufen)
start_urls:
  - "https://www.beispielseite.de/artikel"
```

**Regeln:** Mit **Leerzeichen** einrücken (keine Tabs), jeder Listenpunkt
beginnt mit `  - `, Text mit Sonderzeichen in `"Anführungszeichen"`.

Wichtige Einstellungen unten in derselben Datei (`settings:`):
- `max_results_per_query`: wie viele Treffer pro Suchbegriff (Standard 10)
- `search_language`: Sprache der Suche (`de`, `en`, …)
- `request_delay_seconds`: Wartezeit zwischen Abrufen (Höflichkeit; ≥ 1.0)
- `min_text_length`: Mindestlänge des Haupttexts (filtert leere Seiten)
- `frequency_analysis`: Häufigkeitsauswertung am Ende (`true`/`false`)

### Wie starte ich einen Lauf?
Reiter **„Actions"** → **„Suchlauf starten (Scraper)"** → **„Run workflow"** →
grüner **„Run workflow"**-Button. (Siehe Quickstart Schritt 7.)

### Wo landen die Daten?
1. In der **Supabase-Tabelle** `scrape_results` (dauerhaft, durchsuchbar).
2. Als **CSV + JSON** im Lauf unter **„Artifacts"** zum Herunterladen.

### Wie exportiere ich CSV/JSON?
Passiert **automatisch** bei jedem Lauf. Download: Lauf-Seite → unten
**„Artifacts"** → **„scraper-ergebnisse"**. Die CSV ist semikolon-getrennt
(öffnet sauber in deutschem Excel) und UTF-8-kodiert.

---

## 7. Ergebnisse ansehen und weiterverwerten

**Wie sehe ich meine Ergebnisse?** Drei Wege, je nach Zweck:

**a) Schnell durchklicken — Supabase Table Editor**
Supabase-Projekt → **„Table Editor"** → Tabelle **`scrape_results`**. Du kannst
filtern (z. B. nach `trigger_keyword` oder `run_name`), sortieren und einzelne
Volltexte ansehen. Gut für einen schnellen Überblick.

**b) Eigene Abfragen — Supabase SQL Editor**
Für quantitative Auswertung, z. B. Treffer pro Keyword:
```sql
select trigger_keyword, count(*) as treffer
from scrape_results
group by trigger_keyword
order by treffer desc;
```

**c) Für die Analyse exportieren — CSV/JSON**
Lade das **Artifact** herunter (CSV + JSON). Direkt importierbar in:

- **R**
  ```r
  daten <- read.csv2("scraper-ergebnisse.csv", encoding = "UTF-8")
  ```
- **Python / pandas**
  ```python
  import pandas as pd
  daten = pd.read_csv("scraper-ergebnisse.csv", sep=";")
  ```
- **MAXQDA**: Import → „Strukturierte Daten / Excel-/CSV-Tabelle". Jede Zeile =
  ein Dokument; die Spalte `full_text` enthält den Analysetext, die übrigen
  Spalten (`trigger_keyword`, `domain`, `published_date` …) sind Variablen.

Zusätzlich gibt es eine **`*_haeufigkeiten.csv`** mit Treffern und Nennungen
pro Keyword – ideal als schneller quantitativer Überblick.

---

## 8. Lokale Nutzung am eigenen PC (optional)

Nur falls du den Scraper doch lokal laufen lassen willst (nicht nötig für den
empfohlenen GitHub-Actions-Weg). Du brauchst Python 3.11+.

```bash
# 1. Python-Pakete installieren
pip install -r requirements.txt

# 2. Vorlage für Secrets kopieren und ausfüllen
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
# -> .env mit einem Texteditor öffnen und deine Keys eintragen

# 3. Keywords eintragen in config/search_config.yaml

# 4. Suchlauf starten (EIN Befehl)
python -m src.main
```

---

## 9. Rechtliches & Forschungsethik

> Kurzüberblick, **keine Rechtsberatung.** Im Zweifel: Ethikkommission /
> Datenschutzbeauftragte:r deiner Einrichtung fragen.

- **DSGVO / Personenbezug.** Auch öffentlich zugängliche Webtexte können
  **personenbezogene Daten** enthalten (Namen, Meinungen, Zitate). Sobald du
  diese verarbeitest, gilt die DSGVO. Empfehlungen: Datenminimierung (nur
  erheben, was du brauchst), klare Forschungs-Zweckbindung, sichere Speicherung
  (Supabase-Zugriff über Secrets), und – wo möglich – **Pseudonymisierung/
  Anonymisierung** vor der Analyse. Kläre die Rechtsgrundlage (häufig
  Art. 6 Abs. 1 lit. e/f i. V. m. § 27 BDSG „wissenschaftliche Forschung").
- **Urheberrecht an Texten.** Webtexte sind i. d. R. urheberrechtlich
  geschützt. Für Text and Data Mining zu **wissenschaftlichen** Zwecken gibt es
  in der EU/DE Schranken (**§ 60d UrhG**, EU-DSM-Richtlinie). Diese erlauben das
  Erheben/Auswerten für Forschung, aber **nicht** die ungefragte
  **Weiterveröffentlichung** der Volltexte. Behandle die Volltext-Datenbank als
  internes Forschungsmaterial.
- **Plattform-AGB / Nutzungsbedingungen.** Manche Seiten untersagen
  automatisiertes Auslesen in ihren AGB. Der Scraper respektiert standardmäßig
  **`robots.txt`** und nutzt eine **Such-API** statt Massen-Crawling. Prüfe bei
  sensiblen Quellen zusätzlich deren Nutzungsbedingungen.
- **Rate-Limiting / faire Nutzung.** Standardmäßig liegt eine Wartezeit zwischen
  den Abrufen (`request_delay_seconds`). Bitte nicht auf 0 setzen – das schützt
  die Server der Anbieter und dich.
- **Forschungsethik.** Dokumentiere deine Suchstrategie (Keywords, Zeitpunkt,
  `run_name`) für **Reproduzierbarkeit**. Reflektiere mögliche Verzerrungen
  (z. B. welche Domains die Such-API bevorzugt). Bei personenbezogenen oder
  sensiblen Themen ggf. **Ethikvotum** einholen.

---

## 10. Technische Entscheidungen (kurz begründet)

- **Python** – Standard in der computational social science, riesiges Ökosystem,
  gut lesbar.
- **Such-API (Brave/SerpAPI) statt blindem Crawlen** – rechtlich/ethisch
  sauberer, bessere Trefferqualität, planbare Kosten. Modular: weitere Provider
  (später z. B. Social Media) lassen sich als eigene Funktion ergänzen.
- **trafilatura** für die Volltext-Extraktion – trennt Haupttext zuverlässig von
  Navigation/Werbung und liefert Metadaten (Titel, Datum); in der Forschung
  etabliert.
- **langdetect** für automatische Sprach-Erkennung.
- **Supabase (Postgres)** als Speicher – echte SQL-Datenbank mit komfortablem
  Web-Dashboard, kostenloser Plan, ohne eigenen Server. Die Spalte `url` ist
  eindeutig → automatische **Deduplizierung** per „Upsert". Zusätzlich werden
  inhaltliche Duplikate über einen **Content-Hash** erkannt.
- **GitHub Actions** als Ausführungsort (statt Vercel) – passt zum
  Aufgaben-Modell „einmaliger Lauf", Browser-Bedienung, Secrets-Verwaltung,
  Datei-Download – alles an einem Ort (siehe Abschnitt 2).
- **CSV (Semikolon, UTF-8) + JSON** – direkt nutzbar in R, pandas und MAXQDA.
- **Secrets über `.env` (lokal) bzw. GitHub Actions Secrets (Cloud)** – Keys
  bleiben aus dem Code heraus und werden nie ins Repo committet (`.gitignore`).

---

*Aufbau bewusst modular gehalten: Jedes Modul in `src/` macht genau eine Sache.
Neue Quellen ergänzt du, indem du ein weiteres Modul (analog zu `search.py`)
hinzufügst und in `main.py` einbindest.*
