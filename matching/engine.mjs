/** Deterministic similarity only. Price outcomes never enter the ranking. */
export const categories = {
  weather: 'Weather', production_policy: 'Production policy', sanctions: 'Sanctions',
  conflict: 'Conflict', strategic_stocks: 'Emergency stocks', demand_shock: 'Demand shock'
};
export const mechanisms = {
  landfall: 'Storm landfall', output_cut: 'Production reduction', output_increase: 'Production increase',
  output_hold: 'Production target unchanged', production_target: 'Production target set · direction unclassified', producer_cooperation: 'Producer cooperation',
  sanctions_restriction: 'Energy sanctions', price_cap: 'Oil price cap',
  physical_attack: 'Attack on oil facilities', armed_conflict: 'Armed conflict',
  stock_release: 'Emergency stock release', pandemic_declaration: 'Pandemic declaration'
};
const mechanismCategory = {landfall:'weather',output_cut:'production_policy',output_increase:'production_policy',
  output_hold:'production_policy',production_target:'production_policy',producer_cooperation:'production_policy',sanctions_restriction:'sanctions',
  price_cap:'sanctions',physical_attack:'conflict',armed_conflict:'conflict',stock_release:'strategic_stocks',pandemic_declaration:'demand_shock'};
export const impacts={supply_constraint:'Possible supply constraint',supply_expansion:'Possible supply expansion',demand_contraction:'Possible demand contraction',mixed:'Mixed supply and demand exposure',unknown:'Unknown'};
const clean = text => String(text ?? '').toLowerCase().normalize('NFKC').replace(/[^\p{L}\p{N} ]/gu, ' ').replace(/\s+/g, ' ').trim();
const tokens = text => new Set(clean(text).split(' ').filter(w => w && !['global','participating','producers','members','market','oil','of','the'].includes(w)));
export function validDay(value) {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0,10) === value;
}
export function validateQuery(q) {
  if (!q || !Object.hasOwn(categories,q.category)) throw Error('Choose a supported event category.');
  if (!['brent','wti'].includes(q.market)) throw Error('Only Brent and WTI are supported.');
  if (!validDay(q.occurred) || !validDay(q.publicDate)) throw Error('Enter valid occurrence and public-information dates.');
  if (!q.title?.trim() || q.title.length > 240 || typeof q.location !== 'string' || q.location.length > 160) throw Error('Enter an event description (up to 240 characters) and a shorter location.');
  if (q.mechanism && mechanismCategory[q.mechanism] !== q.category) throw Error('Choose an event detail that belongs to this category.');
  if (q.severity && !['low','moderate','high'].includes(q.severity)) throw Error('Unsupported severity label.');
  if (q.impact && !Object.hasOwn(impacts,q.impact)) throw Error('Choose a supported supply/demand channel.');
  if (q.windSpeed != null && (q.category!=='weather' || typeof q.windSpeed!=='number' || !Number.isFinite(q.windSpeed) || q.windSpeed<0 || q.windSpeed>250)) throw Error('Storm wind must be 0–250 mph, or left unknown.');
  return q;
}
export function rankMatches(query, events) {
  const q = validateQuery(query);
  const allQueryWords=tokens(q.location);
  const specificWords=new Set([...allQueryWords].filter(w=>!['us','eu','g7'].includes(w)));
  const queryWords=specificWords.size?specificWords:allQueryWords;
  return events.filter(e => e.category === q.category && e.affected_commodities.includes(q.market) &&
      e.id !== q.excludeId && e.occurred.date < q.publicDate &&
      e.reactions.anchor && e.reactions.anchor < q.publicDate)
    .map(e => {
      let score = 5; // category 3, supported commodity 2; never a probability
      const reasons = ['Same event category', `${q.market === 'brent' ? 'Brent' : 'WTI'} is in the sourced event scope`];
      const gaps = [];
      let severityMatch=false,severityConflict=false;
      let mechanismMatch = false, locationMatch = false;
      if (q.mechanism && e.features.mechanism === q.mechanism) {
        score += 4; mechanismMatch = true; reasons.push(`Same event detail: ${mechanisms[q.mechanism]}`);
      } else if (q.mechanism && e.features.mechanism) {
        gaps.push(`Different event detail: ${mechanisms[e.features.mechanism]}; broad category resemblance only`);
      } else gaps.push('Event detail was not supplied or is unavailable');
      const common = [...tokens(e.geography)].filter(w => queryWords.has(w));
      if (common.length) {
        score += Math.round(200 * common.length / queryWords.size) / 100; locationMatch = true; reasons.push(`Location wording overlaps: ${common.join(', ')}`);
      } else gaps.push(q.location ? 'No recorded location wording overlaps' : 'Location was not supplied');
      const severity=e.features.severity;
      const severityTime=severity?Date.parse(severity.published_at):NaN;
      const knownSeverity=severity && severity.scale==='advisory_maximum_sustained_wind_mph' && Number.isFinite(severity.value) && Number.isFinite(severityTime) && new Date(severityTime).toISOString().slice(0,10)<q.publicDate;
      if(q.windSpeed!=null && knownSeverity){
        const difference=Math.abs(q.windSpeed-severity.value);
        severityMatch=difference<=30;severityConflict=difference>30;
        if(severityMatch){score+=difference<=15?3:1;reasons.push(`Comparable advisory wind: ${severity.value} mph versus your ${q.windSpeed} mph`);}
        else gaps.push(`Advisory wind differs by ${difference} mph; excluded from the comparable cohort`);
        gaps.push('Wind alone does not measure flooding, outages or economic severity');
      }else gaps.push('Comparable severity is unknown or was not supplied; no severity points awarded');
      const impact=e.features.impact||'unknown';
      if(q.impact && q.impact!=='unknown' && impact===q.impact){score+=3;reasons.push(`Same hypothesised channel: ${impacts[impact]}`);}
      else if(q.impact && q.impact!=='unknown')gaps.push('Supply/demand channels differ or are unknown; no impact points awarded');
      if(q.impact && ((q.impact==='supply_constraint' && impact==='supply_expansion') || (q.impact==='supply_expansion' && impact==='supply_constraint')))return null;
      if (e.first_public.status === 'not_established') gaps.push('First public disclosure is unestablished; price window uses the later supporting publication');
      if (e.first_public.precision !== 'minute') gaps.push('No precise first-public clock is recorded');
      // Known opposite policy actions cannot become attractive matches through
      // a shared meeting venue or a large historical price move.
      const opposite = ['output_cut','output_increase','output_hold'];
      if (opposite.includes(q.mechanism) && opposite.includes(e.features.mechanism) && !mechanismMatch) return null;
      const similarity = severityConflict?'Weak':mechanismMatch && locationMatch ? 'Closer' : mechanismMatch ? 'Partial' : 'Weak';
      return {event:e,score,reasons,gaps,similarity,severityMatch,knownSeverity:!!knownSeverity,locationMatch,locationRequired:queryWords.size>0,mechanismMatch};
    }).filter(Boolean).sort((a,b) => b.score-a.score || a.event.id.localeCompare(b.event.id,'en'));
}
export function visibleReactions(match, query, verifiedOnly=false) {
  return match.event.reactions.markets[query.market].map(row => {
    const primary = row.verification === 'primary_EIA';
    const available = row.end_date && row.end_date < query.publicDate;
    const status = !available ? 'not_available_at_query_date' : verifiedOnly && !primary ? 'primary_verification_required' : row.status;
    return {...row,status, absolute_change:status==='ok'?row.absolute_change:null,
      change_percent:status==='ok'?row.change_percent:null};
  });
}
export function evidenceStrength(match, rows) {
  const usable = rows.filter(r => r.status === 'ok');
  const primary = usable.length === 5 && usable.every(r => r.verification === 'primary_EIA');
  const time = match.event.first_public.precision === 'minute' && match.event.first_public.status !== 'not_established';
  // Current library cannot earn Strong: it has no comparable severity scale
  // and no original daily price publication times. Do not make up confidence.
  return primary && time && match.similarity === 'Closer'
    ? {label:'Moderate', explanation:'Closer event detail/location and primary EIA prices; severity and original price publication times remain unknown.'}
    : {label:'Limited', explanation:'Price verification, event timing, severity or match detail is incomplete. Similarity points are not odds of a repeat.'};
}
