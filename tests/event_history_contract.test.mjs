import {test} from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {historicalSeries, eventRoute} from '../ripple/history.mjs';
import {historicalDetail, existingHistoricalLink, liveResearchSummary} from '../event_history/adapter.mjs';

const report = JSON.parse(execFileSync('python3', ['-c', `
import json
from event_history.library import load_library
from event_history.engine import drilldown
d=load_library()
views=[drilldown(e,d,'2026-11-17T23:59:59Z') for e in d['events'] if e['id'] in ('harvey-2017-texas','nvidia-2023-q1-outlook')]
print(json.dumps(dict(schema_version=1,contract='HIST-1/read-only/1',point_in_time_safe=False,event_count=len(d['events']),coverage=[],view_historical_events=views)))
`], {encoding: 'utf8', maxBuffer: 8 * 1024 * 1024}));

test('new sourced oil drilldown works with the unchanged View historical events reader', () => {
  const event = historicalDetail(report, 'harvey-2017-texas');
  const result = historicalSeries(event, 'brent', '2017-09-01');
  assert(result.points.length > 0);
  assert(result.points.every(p => p.date <= '2017-09-01' && p.value !== null));
  assert(Object.values(result.sources).every(s => s.source_url.startsWith('https://www.eia.gov/')));
  assert.equal(eventRoute(existingHistoricalLink(report, event.id, 'brent')).id, event.id);
});

test('unsupported new markets are data-only and never generate a broken legacy route or fabricated chart', () => {
  const event = historicalDetail(report, 'nvidia-2023-q1-outlook');
  assert.equal(existingHistoricalLink(report, event.id, 'NVDA'), null);
  assert.equal(event.wider_asset_UI_enabled, false);
  assert(event.reactions.markets.NVDA.every(r => r.change_percent === null));
  assert.equal(historicalDetail(report, 'missing'), null);
});

test('LIVE-1 bridge retains three answers and no entry permission without changing input or accounts', () => {
  const before = JSON.stringify(report);
  const result = liveResearchSummary(report);
  assert.deepEqual(Object.keys(result.three_answers), ['what_happened', 'likely_outcome', 'suggested_action']);
  assert.equal(result.action, 'No Action');
  assert.equal(result.qualified_as_of_cases, 0);
  assert.equal(result.read_only, true);
  assert.equal(JSON.stringify(report), before);
  assert.throws(() => liveResearchSummary({...report, point_in_time_safe: true}), /contract/);
});
