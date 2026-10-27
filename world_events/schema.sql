PRAGMA foreign_keys=ON;
CREATE TABLE world_event_versions (
 event_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
 content_sha256 TEXT NOT NULL, recorded_at_utc TEXT NOT NULL,
 category TEXT NOT NULL, occurrence_date TEXT NOT NULL,
 first_public_at TEXT, first_public_date TEXT,
 payload TEXT NOT NULL,
 PRIMARY KEY(event_id,revision)
);
CREATE INDEX world_events_date ON world_event_versions(occurrence_date,event_id);
CREATE INDEX world_events_category ON world_event_versions(category,event_id);
CREATE TABLE world_event_import_runs (
 id INTEGER PRIMARY KEY, imported_at_utc TEXT NOT NULL,
 dataset_sha256 TEXT NOT NULL, inserted INTEGER NOT NULL, reused INTEGER NOT NULL
);
CREATE VIEW world_events_current AS
 SELECT v.* FROM world_event_versions v
 WHERE v.revision=(SELECT max(revision) FROM world_event_versions WHERE event_id=v.event_id);
PRAGMA user_version=1301;
