"""Build a static matching catalogue from the existing, separate SQLite stores."""
import argparse
from datetime import timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from historical import prices
from world_events import events, research

ROOT = Path(__file__).resolve().parents[1]
HORIZONS = (1, 3, 7, 14, 30)
# Explicit classifications of statements already in the reviewed event records.
# Severity has no comparable, sourced scale in this seed and stays null.
MECHANISMS = {
    **{key: "landfall" for key in ("gustav-2008-louisiana", "ike-2008-galveston", "sandy-2012-new-jersey", "harvey-2017-texas", "laura-2020-louisiana", "ida-2021-louisiana")},
    "opec-2014-target": "output_hold", "opec-2016-algiers": "production_target",
    "opec-2016-vienna": "production_target", "opec-2016-cooperation": "producer_cooperation",
    "opec-2020-april": "output_cut", "opec-2020-june": "output_cut",
    "opec-2021-july": "output_increase", "opec-2022-october": "output_cut",
    **{key: "sanctions_restriction" for key in ("eu-2012-iran", "us-2018-jcpoa", "us-2018-iran-reimposition", "eu-2022-oil-embargo")},
    "g7-2022-oil-cap": "price_cap", "saudi-2019-abqaiq": "physical_attack",
    "russia-2022-invasion": "armed_conflict", "israel-2023-october": "armed_conflict",
    "iea-2022-emergency-release": "stock_release", "who-2020-pandemic": "pandemic_declaration"}


def reactions(event, series):
    anchor, evidence, note = research.comparison_anchor(event)
    result = {"anchor": anchor.isoformat() if anchor else None, "alignment_note": note,
              "evidence_id": evidence["id"], "markets": {}}
    for market in ("brent", "wti"):
        data = series[market]
        rows = sorted(data["observations"], key=lambda x: x["date"])
        # Unlike EVT-1's cross-market shared calendar, each benchmark uses its
        # own actual reporting dates. These are observation days, not a proven
        # exchange trading calendar. Explicit missing reports block a horizon.
        before = [r for r in rows if anchor and r["date"] < anchor.isoformat()]
        after = [r for r in rows if anchor and r["date"] > anchor.isoformat()]
        baseline = before[-1] if before else None
        windows = []
        for n in HORIZONS:
            window = after[:n]
            status = "ok"
            if not anchor: status = "publication_time_unknown"
            elif not baseline or baseline["value"] is None: status = "baseline_unavailable"
            elif (anchor-events.day(baseline["date"])).days > 14: status = "baseline_too_old"
            elif len(window) != n: status = "insufficient_observations"
            elif any(r["value"] is None for r in window): status = "explicit_missing_observation"
            elif (events.day(window[-1]["date"])-anchor).days > n*4+14: status = "calendar_gap_too_large"
            used = ([baseline] if baseline else []) + window
            sources = {r["snapshot_id"]: data["sources"][r["snapshot_id"]] for r in used}
            primary = bool(used) and all(s["source_kind"] == "eia" for s in sources.values())
            item = {"days": n, "status": status, "verification": "primary_EIA" if primary else "provisional_seed",
                    "baseline_date": baseline["date"] if baseline else None,
                    "end_date": window[-1]["date"] if window else None, "baseline": None,
                    "end": None, "absolute_change": None, "change_percent": None,
                    "observations": used, "sources": sources, "point_in_time_safe": False}
            if status == "ok":
                first, last = Decimal(baseline["value"]), Decimal(window[-1]["value"])
                item.update(baseline=str(first), end=str(last), absolute_change=str(last-first),
                            change_percent=research.pct(first, last))
            windows.append(item)
        result["markets"][market] = windows
    return result


def build(price_db, event_db):
    db = prices.readonly_db(price_db)
    try:
        series = {m: prices.query(db, m, "2006-01-01", "2100-01-01") for m in prices.SERIES}
    finally: db.close()
    db = events.read_db(event_db)
    try: records = events.list_events(db)
    finally: db.close()
    items = []
    for e in records:
        mechanism = MECHANISMS.get(e["id"])
        items.append({**e, "features": {"mechanism": mechanism, "severity": None,
            "basis": "Manual classification from this record's title, description and evidence; severity is not recorded on a comparable scale."},
            "reactions": reactions(e, series)})
    return {"schemaVersion": 1, "methodology": "category-commodity-mechanism-location-v1",
            "event_set_sha256": events.digest(records), "events": items,
            "price_counts": {m: s["coverage"]["count"] for m, s in series.items()},
            "price_sources": {m: s["sources"] for m, s in series.items()},
            "calendar_note": "1/3/7/14/30 reported observation days after the supporting-publication day; anchor day excluded. No filling. Exchange trading calendar not verified.",
            "point_in_time_safe": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prices-db", default="work/matching-prices.sqlite")
    p.add_argument("--events-db", default="work/matching-events.sqlite")
    p.add_argument("--output", default="matching/catalog.json")
    args = p.parse_args()
    data = build(args.prices_db, args.events_db)
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":"), allow_nan=False)+"\n")
    print(json.dumps({"events": len(data["events"]), "prices": data["price_counts"],
                      "catalog_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))


if __name__ == "__main__": main()
