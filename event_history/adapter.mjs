/** HIST-1 read-only bridge for LIVE-1 and the existing optional history component. */
import {eventHref} from '../ripple/history.mjs';

function validate(report) {
  if (report?.schema_version !== 1 || report.contract !== 'HIST-1/read-only/1' ||
      report.point_in_time_safe !== false || !Array.isArray(report.view_historical_events)) {
    throw new Error('Unsupported historical evidence contract');
  }
}

export function historicalDetail(report, id) {
  validate(report);
  return report.view_historical_events.find(event => event.id === id) ?? null;
}

export function existingHistoricalLink(report, id, market) {
  const detail = historicalDetail(report, id);
  const supported = detail?.existing_UI_routes.some(route => route.id === id && route.market === market);
  return supported ? eventHref(id, market) : null;
}

export function liveResearchSummary(report) {
  validate(report);
  return {
    contract: report.contract,
    historical_events: report.event_count,
    coverage: report.coverage,
    action: 'No Action',
    qualified_as_of_cases: 0,
    read_only: true,
    three_answers: {
      what_happened: 'Historical research is available across six market groups.',
      likely_outcome: 'Uncertain. Selected past reactions are descriptive and do not predict a repeat.',
      suggested_action: 'No Action. Verify current evidence, original availability, prices and costs first.'
    },
    limitation: 'This is a historical library, not a connected live source, new UI deployment or paper execution permission.'
  };
}
