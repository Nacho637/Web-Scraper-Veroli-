-- ===========================================================================
--  SUPABASE-DATENBANK-SCHEMA fuer den Web-Scraper
--
--  WO EINFUEGEN?
--  1. Gehe zu https://supabase.com und oeffne dein Projekt.
--  2. Klicke links auf "SQL Editor".
--  3. Klicke "New query", fuege den GESAMTEN Inhalt dieser Datei ein.
--  4. Klicke unten rechts auf "Run".
--  Fertig - die Tabelle wird angelegt. Du musst das nur EINMAL machen.
-- ===========================================================================

-- Tabelle, in der jeder gefundene Treffer (ein Artikel/eine Seite) landet.
create table if not exists public.scrape_results (
    id              bigint generated always as identity primary key,

    -- Inhalt des Treffers
    title           text,                 -- Titel der Seite
    url             text not null,         -- vollstaendige Adresse
    domain          text,                  -- Domain, z. B. "tagesschau.de"
    full_text       text,                  -- bereinigter Haupttext
    language        text,                  -- erkannte Sprache (z. B. "de")
    published_date  text,                  -- Veroeffentlichungsdatum (falls gefunden)

    -- Forschungs-Metadaten (welche Suche hat den Treffer ausgeloest?)
    run_name        text,                  -- Name des Suchlaufs (aus der Config)
    trigger_keyword text,                  -- Begriff/Phrase, der den Treffer fand
    trigger_type    text,                  -- "keyword" | "phrase" | "topic" | "start_url"
    topic           text,                  -- Themenfeld (falls aus "topics")

    -- Technische Felder
    content_hash    text,                  -- Fingerabdruck des Textes (Deduplizierung)
    scraped_at      timestamptz default now()  -- Zeitpunkt des Scrapings
);

-- Verhindert doppelte Eintraege derselben URL.
-- Dadurch funktioniert das "Upsert" (einfuegen oder aktualisieren) im Code.
create unique index if not exists scrape_results_url_unique
    on public.scrape_results (url);

-- Beschleunigt Auswertungen nach Keyword / Lauf / Domain.
create index if not exists scrape_results_keyword_idx on public.scrape_results (trigger_keyword);
create index if not exists scrape_results_run_idx     on public.scrape_results (run_name);
create index if not exists scrape_results_domain_idx  on public.scrape_results (domain);

-- ---------------------------------------------------------------------------
-- Hinweis zu Sicherheit (Row Level Security):
-- Diese Tabelle wird vom Scraper mit dem "service_role"-Schluessel
-- beschrieben, der RLS umgeht. Fuer ein reines Forschungs-Backend ist das ok.
-- Wenn du die Daten NICHT oeffentlich lesbar machen willst, lass RLS aktiviert
-- (Standard bei Supabase) und greife nur ueber den service_role-Key oder das
-- Dashboard zu.
-- ---------------------------------------------------------------------------
alter table public.scrape_results enable row level security;
