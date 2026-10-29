"""Historical spot prices: Python stdlib only; no broker or hosted database."""
import argparse
import csv
import hashlib
import io
import json
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sqlite3
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
LICENCE = ("EIA public-domain data; acknowledge U.S. Energy Information Administration "
           "and publication date. Protected third-party materials and EIA marks are excluded. "
           "https://www.eia.gov/about/copyrights_reuse.php")
SERIES = {
    "brent": ("Europe Brent Spot Price FOB", "RBRTE", "https://www.eia.gov/dnav/pet/hist/RBRTED.htm"),
    "wti": ("Cushing, OK WTI Spot Price FOB", "RWTC", "https://www.eia.gov/dnav/pet/hist/RWTCD.htm"),
}
MISSING = {"", ".", "-", "--", "NA", "N/A", "W", "null"}
MAX_PAYLOAD = 20 * 1024 * 1024

class DataError(ValueError):
    pass

def iso_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise DataError("Expected an ISO date (YYYY-MM-DD)")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise DataError("Invalid calendar date") from exc
    return value

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")

def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() != timedelta(0):
            raise ValueError()
        return parsed.isoformat(timespec="microseconds")
    except (ValueError, AttributeError) as exc:
        raise DataError("Expected an explicit UTC retrieval timestamp") from exc

def number(value):
    if value is None or str(value).strip() in MISSING:
        return None, str(value).strip() if value is not None else "null"
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", text):
        raise DataError("Invalid numeric observation")
    try:
        n = Decimal(text)
    except InvalidOperation as exc:
        raise DataError("Invalid numeric observation") from exc
    # Zero and negative spot prices are legitimate observations, not missing data.
    if not n.is_finite() or abs(n) > Decimal("1000000000") or n.as_tuple().exponent < -12:
        raise DataError("Nonfinite or unsupported numeric observation")
    return format(n.normalize(), "f"), None

def validate_rows(rows, start=None, end=None, retrieved_at=None):
    result = {}
    for day, value in rows:
        iso_day(day)
        if start and day < start or end and day > end:
            raise DataError("Observation outside requested range")
        if retrieved_at and day > retrieved_at[:10]:
            raise DataError("Observation lies after retrieval date")
        parsed = number(value)
        if day in result and result[day] != parsed:
            raise DataError("Conflicting duplicate date: " + day)
        result[day] = parsed
    if not result:
        raise DataError("No observations returned; no database changes applied")
    return [(day, *result[day]) for day in sorted(result)]

def parse_csv(payload, **kwargs):
    if len(payload) > MAX_PAYLOAD:
        raise DataError("Source exceeds size limit")
    try:
        reader = csv.reader(io.StringIO(payload.decode("utf-8-sig")), strict=True)
        if next(reader, None) != ["Date", "Price"]:
            raise DataError("CSV must contain exactly Date,Price columns")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != 2:
                raise DataError("CSV row must have exactly two fields")
            rows.append((row[0].strip(), row[1].strip()))
        return validate_rows(rows, **kwargs)
    except (UnicodeError, csv.Error) as exc:
        raise DataError("Malformed UTF-8 CSV") from exc

def open_db(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, isolation_level=None, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
            db.close()
            raise DataError("Refusing to migrate an unrelated SQLite database")
        try:
            db.executescript("BEGIN IMMEDIATE;\n" +
                             (Path(__file__).with_name("schema.sql")).read_text() + "\nCOMMIT;")
        except Exception:
            db.close()
            raise
    elif version != 1:
        db.close()
        raise DataError("Unsupported schema version")
    return db

def readonly_db(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    if db.execute("PRAGMA user_version").fetchone()[0] != 1:
        db.close()
        raise DataError("Unsupported schema version")
    return db

def seed_snapshot(market, retrieved_at=None):
    manifest = json.loads((ROOT / "historical" / "seeds.json").read_text())[market]
    payload = (ROOT / manifest["path"]).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != manifest["sha256"]:
        raise DataError("Seed hash mismatch; review and update its provenance manifest explicitly")
    retrieved_at = timestamp(retrieved_at or utc_now())
    rows = parse_csv(payload, retrieved_at=retrieved_at)
    if len(rows) != manifest["rows"]:
        raise DataError("Seed row-count mismatch")
    return dict(market=market, kind="seed", source_url=manifest["source_url"],
                revision=manifest["revision"], source_retrieved_on="2026-10-27",
                retrieved_at=retrieved_at, payload=payload, rows=rows)

def import_snapshots(db, snapshots):
    # Validate every snapshot before starting a single atomic, cross-series write.
    for item in snapshots:
        if item["market"] not in SERIES or item["kind"] not in {"seed", "eia"}:
            raise DataError("Unsupported source/series")
        item["retrieved_at"] = timestamp(item["retrieved_at"])
        item["rows"] = validate_rows([(d, v if v is not None else missing)
                                      for d, v, missing in item["rows"]],
                                     retrieved_at=item["retrieved_at"])
        if len(item["payload"]) > MAX_PAYLOAD * 10:
            raise DataError("Snapshot too large")
    summaries = []
    db.execute("BEGIN IMMEDIATE")
    try:
        for item in snapshots:
            market = item["market"]
            name, eia, url = SERIES[market]
            db.execute("INSERT OR IGNORE INTO price_series VALUES(?,?,?,?,?,?)",
                       (market, name, eia, "USD/barrel", url, LICENCE))
            digest = hashlib.sha256(item["payload"]).hexdigest()
            identity = hashlib.sha256(json.dumps([market, item["kind"], item["source_url"], digest, item["retrieved_at"], item["rows"]]).encode()).hexdigest()
            counts = dict(series=market, source_kind=item["kind"], snapshot_id=identity,
                          inserted=0, revised=0, unchanged=0, ignored_lower_priority=0,
                          numeric_rows=sum(r[1] is not None for r in item["rows"]),
                          missing_rows=sum(r[1] is None for r in item["rows"]))
            latest = db.execute("SELECT * FROM price_snapshots WHERE series_id=? AND source_kind=? ORDER BY retrieved_at DESC,rowid DESC LIMIT 1", (market,item["kind"])).fetchone()
            same_latest = bool(latest and latest["source_url"] == item["source_url"] and latest["sha256"] == digest and
                               set(item["rows"]).issubset({tuple(r) for r in db.execute("SELECT observation_date,value,missing_code FROM price_observations WHERE snapshot_id=?",(latest["id"],))}))
            if same_latest or db.execute("SELECT 1 FROM price_snapshots WHERE id=?", (identity,)).fetchone():
                counts["snapshot_id"] = latest["id"] if same_latest else identity
                counts["unchanged"] = len(item["rows"])
                counts["snapshot_reused"] = True
                summaries.append(counts)
                continue
            old = {r["observation_date"]: r for r in db.execute(
                "SELECT * FROM price_current WHERE series_id=?", (market,))}
            db.execute("INSERT INTO price_snapshots VALUES(?,?,?,?,?,?,?,?,?)",
                       (identity, market, item["kind"], item["source_url"], item["retrieved_at"],
                        item["revision"], item.get("source_retrieved_on"), digest, item["payload"],
                        ))
            db.executemany("INSERT INTO price_observations VALUES(?,?,?,?)",
                           [(identity, day, value, missing) for day, value, missing in item["rows"]])
            for day, value, missing in item["rows"]:
                prior = old.get(day)
                if not prior:
                    counts["inserted"] += 1
                elif ((prior["source_kind"] == "eia" and item["kind"] == "seed") or
                      (prior["source_kind"] == item["kind"] and prior["retrieved_at"] > item["retrieved_at"])):
                    counts["ignored_lower_priority"] += 1
                elif prior["value"] == value and prior["missing_code"] == missing:
                    counts["unchanged"] += 1
                else:
                    counts["revised"] += 1
            counts["snapshot_reused"] = False
            summaries.append(counts)
        db.execute("INSERT INTO price_import_runs(imported_at,summary_json) VALUES(?,?)",
                   (utc_now(), json.dumps(summaries, sort_keys=True)))
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
    return summaries

def query(db, market, start, end, as_of=None):
    if market not in SERIES:
        raise DataError("Unknown series")
    iso_day(start); iso_day(end)
    if start > end:
        raise DataError("Start date must precede end date")
    parameters = [market]
    cutoff = ""
    if as_of:
        cutoff = " AND s.retrieved_at <= ?"
        parameters.append(timestamp(as_of))
    # Rank BEFORE filtering values, so explicit source missing/retracted values
    # suppress older numeric values rather than reviving them silently.
    sql = """
      WITH ranked AS (
        SELECT o.*,s.series_id,s.source_kind,s.source_url,s.retrieved_at,
               s.source_revision,s.sha256,s.source_retrieved_on,
          ROW_NUMBER() OVER(PARTITION BY o.observation_date ORDER BY
            CASE s.source_kind WHEN 'eia' THEN 2 ELSE 1 END DESC,
            s.retrieved_at DESC,s.rowid DESC) AS position
        FROM price_observations o JOIN price_snapshots s ON o.snapshot_id=s.id
        WHERE s.series_id=?""" + cutoff + """
      ) SELECT * FROM ranked WHERE position=1 AND observation_date BETWEEN ? AND ?
      ORDER BY observation_date"""
    selected = [dict(r) for r in db.execute(sql, parameters + [start, end])]
    numeric = [r for r in selected if r["value"] is not None]
    sources = {}
    for r in selected:
        sources[r["snapshot_id"]] = {k: r[k] for k in
            ("source_kind", "source_url", "retrieved_at", "source_revision", "sha256", "source_retrieved_on")}
    return dict(series=market, name=SERIES[market][0], eia_series=SERIES[market][1],
                original_source_url=SERIES[market][2], unit="USD/barrel", basis="Daily spot benchmark; not executable trade P&L",
                requested_range=[start, end],
                coverage=dict(count=len(numeric), first=numeric[0]["observation_date"] if numeric else None,
                              last=numeric[-1]["observation_date"] if numeric else None,
                              explicit_missing=len(selected)-len(numeric)),
                as_of=as_of, point_in_time_safe=False,
                known_at_note="Retrieval time is our knowledge time, not original EIA publication time; historical vintages before ingestion are unknown.",
                licence=LICENCE, sources=sources,
                observations=[dict(date=r["observation_date"], value=r["value"],
                                   missing_code=r["missing_code"], snapshot_id=r["snapshot_id"]) for r in selected])

def export(db, target, start="2006-01-01", end=None):
    end = end or date.today().isoformat()
    data = dict(schemaVersion=1, series=[query(db, s, start, end) for s in SERIES])
    # Short per-series references avoid repeating 64-character snapshot hashes
    # on every static row; the full identities remain in the source dictionary.
    for series in data["series"]:
        refs = {identity: "s" + str(i) for i, identity in enumerate(sorted(series["sources"]))}
        series["sources"] = {refs[identity]: {**meta, "snapshot_id":identity}
                             for identity,meta in series["sources"].items()}
        for row in series["observations"]:
            row["snapshot_id"] = refs[row["snapshot_id"]]
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(data, separators=(",", ":"), allow_nan=False) + "\n")
    temporary.replace(target)
    return {s["series"]: s["coverage"] for s in data["series"]}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def download(url):
    try:
        with urllib.request.build_opener(NoRedirect()).open(url, timeout=45) as response:
            body = response.read(MAX_PAYLOAD + 1)
            if len(body) > MAX_PAYLOAD:
                raise DataError("EIA response exceeds size limit")
            return body
    except Exception:
        # urllib exceptions can contain the complete URL with the API key.
        raise DataError("EIA request failed; check network access, free API key and quota. No fallback imported.") from None

def redact_credentials(value, api_key):
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key.lower() in {"api_key", "apikey"}
                      else redact_credentials(item, api_key)) for key,item in value.items()}
    if isinstance(value, list):
        return [redact_credentials(item, api_key) for item in value]
    if isinstance(value, str):
        return value.replace(api_key, "[REDACTED]")
    return value

def fetch_eia(market, start, end, api_key, fetcher=download, retrieved_at=None):
    from urllib.parse import urlencode
    iso_day(start); iso_day(end)
    if start > end or not api_key:
        raise DataError("EIA_API_KEY and a valid date range are required")
    retrieved_at = timestamp(retrieved_at or utc_now())
    offset, total, records, pages = 0, None, [], []
    while total is None or offset < total:
        parameters = {"frequency":"daily", "data[0]":"value",
                      "facets[series][0]":SERIES[market][1], "start":start, "end":end,
                      "sort[0][column]":"period", "sort[0][direction]":"asc",
                      "offset":offset, "length":5000}
        url = ENDPOINT + "?" + urlencode({**parameters, "api_key":api_key})
        try:
            raw = fetcher(url)
            if len(raw) > MAX_PAYLOAD:
                raise ValueError()
            body = json.loads(raw)
            response = body["response"]
            warning = body.get("warning")
            pagination_warning = (warning == "parameter out of range" and
                                  "5000" in str(body.get("description", "")))
            if body.get("error") or (warning and not pagination_warning) or response.get("frequency") != "daily":
                raise ValueError()
            count = int(response["total"])
            data = response["data"]
            if count < 1 or count > 100000 or not isinstance(data, list) or not 1 <= len(data) <= 5000:
                raise ValueError()
            if total is not None and count != total:
                raise ValueError()
            total = count
            if offset + len(data) > total:
                raise ValueError()
            for r in data:
                if r["series"] != SERIES[market][1] or r["units"] not in {"Dollars per Barrel", "$/BBL", "$/bbl"}:
                    raise ValueError()
                records.append((r["period"], r["value"]))
            # EIA echoes the key in request metadata. Retain sanitized response
            # pages, NEVER original credential-bearing response bytes.
            pages.append(redact_credentials(body, api_key))
            offset += len(data)
        except Exception:
            raise DataError("Invalid or failed EIA response; no import applied (details suppressed to protect credentials)") from None
    rows = validate_rows(records, start=start, end=end, retrieved_at=retrieved_at)
    if len(rows) != total:
        raise DataError("Duplicate or unstable EIA pagination; retry the complete request")
    payload = json.dumps(pages, sort_keys=True, separators=(",", ":")).encode()
    return dict(market=market, kind="eia", source_url=ENDPOINT + "?" + urlencode({
                    "frequency":"daily", "facets[series][0]":SERIES[market][1], "start":start, "end":end}),
                revision="sha256 of credential-redacted EIA response pages; source vintage not supplied",
                retrieved_at=retrieved_at, payload=payload, rows=rows)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="work/historical-prices.sqlite")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("backfill", "update"):
        p = commands.add_parser(name)
        p.add_argument("--source", choices=["seed", "eia"], default="seed")
        p.add_argument("--start", default="2006-01-01")
        p.add_argument("--end", default=date.today().isoformat())
        if name == "update":
            p.add_argument("--overlap-days", type=int, default=30)
    p = commands.add_parser("query")
    p.add_argument("--series", choices=list(SERIES), required=True)
    p.add_argument("--start", required=True); p.add_argument("--end", required=True)
    p.add_argument("--as-of")
    p = commands.add_parser("export")
    p.add_argument("--output", default="data/historical/prices.json")
    p.add_argument("--start", default="2006-01-01")
    p.add_argument("--end", default=date.today().isoformat())
    args = parser.parse_args(argv)
    try:
        if args.command in ("query", "export"):
            db = readonly_db(args.db)
        else:
            iso_day(args.start); iso_day(args.end)
            if args.start > args.end:
                raise DataError("Invalid date range")
            if args.command == "update" and not 1 <= args.overlap_days <= 3650:
                raise DataError("Overlap must be between 1 and 3650 days")
            starts = {s:args.start for s in SERIES}
            if args.command == "update" and Path(args.db).exists():
                existing = readonly_db(args.db)
                try:
                    for market in SERIES:
                        last = existing.execute("SELECT max(observation_date) FROM price_current WHERE series_id=?", (market,)).fetchone()[0]
                        if last:
                            starts[market] = max(args.start, (date.fromisoformat(last)-timedelta(days=args.overlap_days)).isoformat())
                finally:
                    existing.close()
            if args.source == "seed":
                snapshots = [seed_snapshot(s) for s in SERIES]
                for item in snapshots:
                    item["rows"] = [r for r in item["rows"] if starts[item["market"]] <= r[0] <= args.end]
                    if not item["rows"]:
                        raise DataError("No seed observations in requested range")
            else:
                api_key = os.environ.get("EIA_API_KEY", "")
                if not api_key:
                    raise DataError("Set EIA_API_KEY to a free EIA key for primary-source imports. Seed data is not substituted.")
                snapshots = [fetch_eia(s, starts[s], args.end, api_key) for s in SERIES]
            db = open_db(args.db)
        try:
            if args.command in ("backfill", "update"):
                result = dict(imports=import_snapshots(db, snapshots),
                              coverage={s:query(db,s,"0001-01-01","9999-12-31")["coverage"] for s in SERIES})
            elif args.command == "query":
                result = query(db,args.series,args.start,args.end,args.as_of)
            else:
                result = export(db,args.output,args.start,args.end)
            print(json.dumps(result,indent=2,allow_nan=False))
        finally:
            db.close()
        return 0
    except (DataError, OSError, sqlite3.Error) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
