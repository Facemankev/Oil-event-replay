const $ = id => document.getElementById(id);
const labels = {harvey:'Harvey landfall — 2017',nvidia:'Nvidia earnings — 2024',biogen:'Biogen trial stop — 2019',fed:'Fed emergency cut — 2020',nvidia_board:'Nvidia board statement — 2026'};
const names = {oil:'Oil',technology_equities:'Technology / equities',gold:'Gold',pharmaceuticals:'Pharma / biotech',stock_indices:'Stock indices',currencies:'Currencies'};
export function percent(value) {
  if (value === null || value === undefined) return 'Unavailable';
  const n = Number(value);
  return Number.isFinite(n) ? `${n > 0 ? '+' : ''}${n.toFixed(2)}%` : 'Unavailable';
}
function node(tag, text) { const n = document.createElement(tag); n.textContent = text; return n; }
function link(text, url) {
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password || /(?:key|token|password|secret)=/i.test(parsed.search)) throw Error('Unsafe evidence link');
  const a = node('a', text); a.href = parsed.href; a.rel = 'noopener noreferrer'; return a;
}
function row(values) { const r = document.createElement('tr'); values.forEach(v => r.append(node('td',v))); return r; }
export function renderCase(data, key) {
  const c = data.cases.find(c => c.case === key);
  if (!c || c.action !== 'No Action') throw Error('Unsupported demonstration');
  $('what').textContent = c.three_answers.what_happened;
  $('when').textContent = `Occurrence: ${c.occurred_day || 'Not established'}. Supporting publication: ${c.supporting_publication_day}. Original historical receipt: unknown.`;
  $('event-source').replaceChildren('Evidence: ',link(c.sources[0].publisher,c.sources[0].url));
  $('meaning').textContent = c.three_answers.likely_outcome;
  const legacy = c.legacy_daily_cross_check;
  if (legacy) {
    $('reaction').textContent = `Recorded daily context, ${legacy.baseline_date} to ${legacy.first_close_date}: Nvidia ${percent(legacy.own_percent)}. ${legacy.peers.map(p=>`${p.symbol} ${percent(p.percent)}`).join('; ')}. Opposite peer directions challenge a blanket sector-decline story.`;
    $('price-source').replaceChildren('Retained secondary daily references; not live or exchange-print verification. ',link('Sources and limitations','https://github.com/Facemankev/Oil-event-replay/blob/08aea1b2464969c06f6e53bdc9cc02bef5ff0809/equities/README.md'));
  } else {
    const first = c.dated_reference_reactions[Object.keys(c.dated_reference_reactions)[0]].find(r=>r.days===5);
    $('reaction').textContent = first.change_percent === null ? 'The requested company/index price window is unavailable. A reported percentage is not substituted for missing prices.' : `Retrospective five-observation reference change: ${percent(first.change_percent)}, ${first.baseline_date} to ${first.end_date}. This is outside the earlier decision.`;
    $('price-source').textContent = 'Dated EIA/Fed reference data and explicit missing windows are listed below. Daily evidence does not prove the event caused a move.';
  }
  $('matches').replaceChildren(...c.comparable_events.map(m => node('li',`${m.title} (${m.publication_day}; ${m.instrument}). ${m.reasons.join('; ')}. Weaknesses: ${m.weaknesses.join('; ')}.`)));
  if (!c.comparable_events.length) $('matches').append(node('li','No comparable earlier cases passed the recorded category/episode checks.'));
  const stats = c.retrospective_cohort.current_vintage_reference;
  $('cohort').textContent = `${c.selected_episode_count} non-overlapping price-context episodes; ${stats.count} usable current-vintage paths; ${c.fully_as_of_qualified} original-as-of-qualified cases. ${stats.count ? `Descriptive median ${percent(stats.median)}, range ${percent(stats.minimum)} to ${percent(stats.maximum)}. ` : ''}This selected sample is not a forecast probability.`;
  $('sources').replaceChildren(...c.sources.map(s=>{const item=document.createElement('li');item.append(link(s.publisher,s.url),' — '+s.locator);return item;}));
  $('reactions').replaceChildren(...Object.entries(c.dated_reference_reactions).flatMap(([m,rs])=>rs.map(r=>row([`${m} / ${r.unit}`,String(r.days),r.baseline_date||'Unavailable',r.end_date||'Unavailable',percent(r.change_percent)]))));
  $('action').textContent = c.action;
  $('suggestion').textContent = c.three_answers.suggested_action;
  $('answers').hidden = false;
}
async function start() {
  try {
    const response = await fetch('demo.json');
    if (!response.ok) throw Error('Missing demonstration');
    const data = await response.json();
    if (data.schema_version!==1 || data.kind!=='reproducible_historical_process_demonstration' || !data.paper_only) throw Error('Wrong demonstration');
    $('case').replaceChildren(...data.cases.map(c=>{const o=node('option',labels[c.case]||c.title);o.value=c.case;return o;}));
    $('case').value='nvidia_board';$('case').disabled=false;
    $('case').addEventListener('change',()=>renderCase(data,$('case').value));
    renderCase(data,'nvidia_board');
    $('coverage-note').textContent=`£${data.cost_GBP} data/API charge in this pilot. ${data.coverage.events} library events, ${data.coverage.numeric_observations.toLocaleString()} numeric primary observations; ${data.coverage.new_FX_numeric.toLocaleString()} new EUR/USD and USD/JPY rates. Counts are source coverage, not independent trading opportunities.`;
    $('coverage').replaceChildren(...data.coverage.groups.map(g=>row([names[g.group],g.numeric_observations.toLocaleString(),String(g.retained_secondary_provider_rows),String(g.reported_reactions)])));
    $('load-status').textContent='Five reproducible historical cases. No supported paper entries.';
  } catch {
    $('answers').hidden=true;$('load-status').textContent='The sourced demonstration could not load. No recommendation or account action is available.';
  }
}
if (typeof document !== 'undefined') {
  for (const button of document.querySelectorAll('[data-theme]')) button.addEventListener('click',()=>{
    document.documentElement.dataset.theme=button.dataset.theme;
    for (const b of document.querySelectorAll('[data-theme]')) b.setAttribute('aria-pressed',String(b===button));
  });
  start();
}
