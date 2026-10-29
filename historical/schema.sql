PRAGMA foreign_keys = ON;
CREATE TABLE price_series (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, eia_series TEXT NOT NULL UNIQUE,
 unit TEXT NOT NULL CHECK(unit='USD/barrel'), source_url TEXT NOT NULL,
 licence TEXT NOT NULL
);
CREATE TABLE price_snapshots (
 id TEXT PRIMARY KEY, series_id TEXT NOT NULL REFERENCES price_series(id),
 source_kind TEXT NOT NULL CHECK(source_kind IN ('seed','eia')),
 source_url TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 source_revision TEXT NOT NULL, source_retrieved_on TEXT,
 sha256 TEXT NOT NULL, payload BLOB NOT NULL
);
CREATE TABLE price_observations (
 snapshot_id TEXT NOT NULL REFERENCES price_snapshots(id),
 observation_date TEXT NOT NULL, value TEXT, missing_code TEXT,
 CHECK((value IS NULL AND missing_code IS NOT NULL) OR
       (value IS NOT NULL AND missing_code IS NULL)),
 PRIMARY KEY(snapshot_id,observation_date)
);
CREATE INDEX price_observation_date ON price_observations(observation_date,snapshot_id);
CREATE TABLE price_import_runs (
 id INTEGER PRIMARY KEY, imported_at TEXT NOT NULL, summary_json TEXT NOT NULL
);
-- Prefer primary EIA over the secondary seed; never discard prior versions.
-- "retrieved_at" is our knowledge time, NOT the original publication timestamp.
CREATE VIEW price_current AS
 SELECT * FROM (
  SELECT o.*,s.series_id,s.source_kind,s.source_url,s.retrieved_at,
   s.source_revision,s.sha256,s.source_retrieved_on,
   ROW_NUMBER() OVER (
    PARTITION BY s.series_id,o.observation_date
    ORDER BY CASE s.source_kind WHEN 'eia' THEN 2 ELSE 1 END DESC,
     s.retrieved_at DESC,s.rowid DESC
   ) AS position
  FROM price_observations o JOIN price_snapshots s ON o.snapshot_id=s.id
 ) WHERE position=1;
PRAGMA user_version = 1;
