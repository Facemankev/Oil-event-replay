"""Additional sourced measurements; mechanism channels remain explicit hypotheses."""
import json
from pathlib import Path
from world_events import events

IMPACTS = {
    'landfall': 'mixed', 'output_cut': 'supply_constraint',
    'output_increase': 'supply_expansion', 'stock_release': 'supply_expansion',
    'sanctions_restriction': 'supply_constraint', 'price_cap': 'supply_constraint',
    'physical_attack': 'supply_constraint', 'armed_conflict': 'supply_constraint',
    'pandemic_declaration': 'demand_contraction',
}


def load(path):
    data = json.loads(Path(path).read_text())
    events.require(data.get('schema_version') == 1, 'Unsupported trait evidence')
    records = data['measurements']
    events.require(isinstance(records,list), 'Missing measurement list')
    seen = set()
    for record in records:
        events.require(record['event_id'] not in seen, 'Duplicate measurement event')
        seen.add(record['event_id'])
        events.require(events.digest({k:v for k,v in record.items() if k!='sha256'}) == record['sha256'], 'Measurement hash mismatch')
        events.require(record['scale'] == 'advisory_maximum_sustained_wind_mph', 'Unsupported severity scale')
        events.require(type(record['value']) is int and 0 <= record['value'] <= 250, 'Invalid sustained wind')
        events.https(record['url'])
        events.require(record['url'].startswith('https://www.nhc.noaa.gov/archive/'), 'Expected primary NHC archive')
        events.instant(record['published_at'])
        events.day(record['checked_on'])
    return {r['event_id']:r for r in records}


def attach(event, mechanism, records):
    measurement = records.get(event['id'])
    if measurement:
        events.require(measurement['event_sha256'] == events.digest(event), 'Event changed; re-review measurement')
        public = event['first_public']['at']
        events.require(public is not None, 'Measurement requires a clocked source context')
        lag = (events.instant(public)-events.instant(measurement['published_at'])).total_seconds()/3600
        events.require(0 <= lag <= 6, 'Measurement is not a contemporaneous pre/public-event advisory')
    return {'basis':'Mechanisms describe the existing event evidence. Severity uses only the linked contemporaneous NHC advisory wind measurement where available; economic severity remains unknown.', 'severity':measurement, 'impact':IMPACTS.get(mechanism,'unknown'),
            'impact_basis':'Mechanism-based exposure hypothesis, not measured oil output/demand or predicted price direction.'}
