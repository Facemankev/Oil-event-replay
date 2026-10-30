/** Public record identifiers only; never put free-text research in a URL. */
export const WINDOWS = Object.freeze([1, 3, 5, 10, 20]);
export const ROOT = new URL('../', import.meta.url);
export function readContext(search, events) {
  const params = new URLSearchParams(search);
  const requested = params.get('event') || '';
  const event = events.find(item => item.id === requested) || null;
  return {event, missing: !!requested && !event,
    market: params.get('market') === 'wti' ? 'wti' : 'brent',
    days: WINDOWS.includes(Number(params.get('days'))) ? Number(params.get('days')) : 5};
}
export function route(path, context = {}, root = ROOT) {
  const url = new URL(path, root);
  if (context.event?.id) url.searchParams.set('event', context.event.id);
  if (['brent', 'wti'].includes(context.market)) url.searchParams.set('market', context.market);
  if (WINDOWS.includes(context.days)) url.searchParams.set('days', context.days);
  return url;
}
export async function loadJSON(url, kind, timeout = 15000, validate = data => data.schemaVersion === 1 && Array.isArray(data.events)) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, {signal: controller.signal, credentials: 'same-origin'});
    if (!response.ok) throw Error(`${kind} unavailable (HTTP ${response.status})`);
    const data = await response.json();
    if (!validate(data)) throw Error(`Unsupported ${kind}`);
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw Error(`${kind} took too long to load. Check your connection and retry.`);
    throw error;
  } finally { clearTimeout(timer); }
}
