-- Design migration only. Not connected to the static website or production.
PRAGMA foreign_keys = ON;
CREATE TABLE sources (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL,
 licence TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 content_sha256 TEXT NOT NULL, upstream_revision TEXT,
 verification_status TEXT NOT NULL CHECK(verification_status IN ('secondary_checked','primary_checked','unverified'))
);
CREATE TABLE events (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, event_date TEXT NOT NULL,
 category TEXT NOT NULL CHECK(category IN ('war','epidemic','earthquake','hurricane','political_decision','ai_breakthrough','transport_disruption','infrastructure_attack')),
 description TEXT NOT NULL, occurred_at_utc TEXT, date_precision TEXT NOT NULL,
 source_id TEXT NOT NULL REFERENCES sources(id)
);
CREATE TABLE instruments (
 id TEXT PRIMARY KEY, name TEXT NOT NULL,
 asset_class TEXT NOT NULL CHECK(asset_class IN ('technology_share','stock_index','oil','gold','currency','cryptocurrency')),
 symbol TEXT, exchange TEXT, currency TEXT NOT NULL, unit TEXT NOT NULL, timezone TEXT NOT NULL, calendar TEXT NOT NULL
);
CREATE TABLE series (
 id TEXT PRIMARY KEY, instrument_id TEXT NOT NULL REFERENCES instruments(id),
 source_id TEXT NOT NULL REFERENCES sources(id), frequency TEXT NOT NULL,
 price_basis TEXT NOT NULL, adjustment_method TEXT NOT NULL,
 UNIQUE(instrument_id,source_id,frequency,price_basis,adjustment_method)
);
CREATE TABLE observations (
 series_id TEXT NOT NULL REFERENCES series(id), observation_date TEXT NOT NULL,
 value REAL NOT NULL, observed_at_utc TEXT,
 -- Distinct source snapshots create distinct series; never overwrite revisions.
 PRIMARY KEY(series_id,observation_date)
);
CREATE INDEX observations_date ON observations(observation_date,series_id);
CREATE INDEX events_category_date ON events(category,event_date);
CREATE TABLE research_runs (
 id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id),
 methodology_version TEXT NOT NULL, parameters_json TEXT NOT NULL,
 evidence_json TEXT NOT NULL, created_at TEXT NOT NULL
);
