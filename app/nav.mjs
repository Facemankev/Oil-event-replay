import {ROOT, route, readContext} from './context.mjs';
const nav = document.createElement('nav');
nav.className = 'app-nav'; nav.setAttribute('aria-label', 'Market Ripple application');
const destinations = [['Application home','app/'],['Event evidence','event-research.html'],
  ['Historical matches','matching/'],['Paper practice','paper.html'],['Price history','history.html'],['Original dashboard','index.html']];
const links = destinations.map(([label,path]) => {
  const a = document.createElement('a'); a.textContent = label; a.dataset.route = path;
  nav.append(a); return a;
});
function update(context) {
  for (const link of links) {
    link.href = route(link.dataset.route, context).href;
    if (new URL(link.href).pathname === location.pathname ||
      new URL(link.href).pathname.replace(/\/$/, '/index.html') === location.pathname) link.setAttribute('aria-current','page');
    else link.removeAttribute('aria-current');
  }
}
const params = new URLSearchParams(location.search);
const id = params.get('event');
// Data modules validate membership before displaying/using any record.
update({...readContext(location.search, []), event: id && /^[a-z0-9-]{1,100}$/.test(id) ? {id} : null});
document.querySelector('main').prepend(nav);
window.addEventListener('mr:context', event => update(event.detail));
const base = ROOT.href;
const diagnostic = document.createElement('details'); diagnostic.className='app-diagnostics';
const summary=document.createElement('summary'); summary.textContent='Preview help and device checks'; diagnostic.append(summary);
const p=document.createElement('p');
p.textContent='Open this URL directly in Safari or your desktop browser. If a private preview asks you to sign in, use the ChatGPT account that owns it. A sign-in page or loop before this application opens belongs to preview access, not the research data. Do not share sign-in cookies or tokens.'; diagnostic.append(p);
const code=document.createElement('p');code.textContent=`Application base: ${base} · Browser time: ${new Date().toISOString()}. For a bug report, record the visible error, route, iOS/browser version and whether it occurs before or after sign-in. Never send account backups or credentials.`; diagnostic.append(code);
document.querySelector('main').append(diagnostic);
