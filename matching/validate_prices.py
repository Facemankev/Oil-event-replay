"""Audit pinned seeds and optionally reconcile against live, authenticated EIA."""
import argparse
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from historical import prices as p

ROOT = Path(__file__).resolve().parents[1]


def differences(seed, primary):
    """Compare explicit observations; never classify absent weekdays as holidays."""
    left = {d: v for d, v, _ in seed}
    right = {d: v for d, v, _ in primary}
    common = sorted(left.keys() & right.keys())
    changes = [{"date": d, "seed": left[d], "primary": right[d]} for d in common if left[d] != right[d]]
    return {"shared_dates": len(common), "equal_values": sum(left[d] == right[d] for d in common),
            "discrepancies": changes, "missing_from_seed": sorted(right.keys() - left.keys()),
            "missing_from_primary": sorted(left.keys() - right.keys()),
            "interpretation": "Differences may be revisions or seed errors; cause and historical revision time are not established."}


def audit(attempt_primary=False, db_path=None):
    snapshots = [p.seed_snapshot(m) for m in p.SERIES]
    report = {"schema_version": 1, "status": "not_attempted", "verified": False,
              "method": "Exact Decimal values by EIA series and observation date; inclusive seed coverage.",
              "primary_reconciliation_succeeded": False, "primary_endpoint": p.ENDPOINT, "api_key_configured": bool(os.environ.get("EIA_API_KEY")),
              "series": {}, "limitations": [
                  "Seed mirrors are secondary EIA-derived data until primary reconciliation succeeds.",
                  "Absent weekdays are not automatically missing prices: holidays and publication schedules are unverified.",
                  "A present-day EIA reconciliation cannot establish original publication times or historical vintages."]}
    for s in snapshots:
        rows = s["rows"]; days = {d for d, _, _ in rows}
        start, end = date.fromisoformat(rows[0][0]), date.fromisoformat(rows[-1][0])
        weekdays = [start + timedelta(days=i) for i in range((end-start).days+1)]
        report["series"][s["market"]] = {
            "eia_series": p.SERIES[s["market"]][1], "seed_sha256": hashlib.sha256(s["payload"]).hexdigest(),
            "numeric_count": sum(v is not None for _, v, _ in rows), "first": rows[0][0], "last": rows[-1][0],
            "explicit_missing": [d for d, v, _ in rows if v is None],
            "absent_weekdays_unclassified": [d.isoformat() for d in weekdays if d.weekday()<5 and d.isoformat() not in days],
            "primary_comparison": None}
    sets = [{d for d, v, _ in s["rows"] if v is not None} for s in snapshots]
    report["cross_series"] = {"shared_numeric_dates": len(sets[0] & sets[1]),
        "brent_only_dates": sorted(sets[0]-sets[1]), "wti_only_dates": sorted(sets[1]-sets[0])}
    if db_path:
        db = p.readonly_db(db_path)
        try:
            report["database"] = {"integrity": db.execute("PRAGMA integrity_check").fetchone()[0],
                "snapshots": db.execute("SELECT count(*) FROM price_snapshots").fetchone()[0],
                "versions": db.execute("SELECT count(*) FROM price_observations").fetchone()[0],
                "additional_versions": db.execute("SELECT count(*) FROM price_observations").fetchone()[0] - db.execute("SELECT count(*) FROM price_current").fetchone()[0]}
        finally:
            db.close()
    if attempt_primary:
        try:
            key = os.environ.get("EIA_API_KEY")
            if not key:
                raise p.DataError("EIA_API_KEY is not configured. Full primary reconciliation did not run.")
            primary = [p.fetch_eia(s["market"], s["rows"][0][0], s["rows"][-1][0], key) for s in snapshots]
            # Import into a NEW audit database only; preserve existing databases.
            audit_path = ROOT / "work/eia-reconciliation.sqlite"
            db = p.open_db(audit_path)
            try:
                p.import_snapshots(db, snapshots + primary)
            finally:
                db.close()
            for s, fetched in zip(snapshots, primary):
                report["series"][s["market"]]["primary_comparison"] = differences(s["rows"], fetched["rows"])
                report["series"][s["market"]]["primary_sha256"] = hashlib.sha256(fetched["payload"]).hexdigest()
            comparisons = [s["primary_comparison"] for s in report["series"].values()]
            exact = all(not c["discrepancies"] and not c["missing_from_seed"] and not c["missing_from_primary"] for c in comparisons)
            report.update(status="reconciled" if exact else "reconciled_with_differences", verified=exact,
                          primary_reconciliation_succeeded=True,
                          primary_retrieved_at=[s["retrieved_at"] for s in primary])
        except (p.DataError, OSError, sqlite3.Error):
            report.update(status="blocked", blocker="EIA_API_KEY is not configured; no authenticated reconciliation ran." if not report["api_key_configured"] else "EIA response or network failure. No full primary reconciliation succeeded; no substitution accepted.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-primary", action="store_true")
    parser.add_argument("--db")
    parser.add_argument("--output", default="matching/validation-report.json")
    args = parser.parse_args()
    report = audit(args.attempt_primary, args.db)
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status": report["status"], "verified": report["verified"],
                      "counts": {m: s["numeric_count"] for m, s in report["series"].items()}}, indent=2))
    # Blocked verification must be machine-readable as failure, while the
    # independent prototype may still be built explicitly with provisional data.
    return 2 if args.attempt_primary and not report["verified"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
