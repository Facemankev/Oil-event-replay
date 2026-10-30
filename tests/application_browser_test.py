"""Real browser engines; iPhone settings are emulation, never physical-device proof."""
import argparse, hashlib, json, threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser',choices=['chromium','webkit'],default='chromium')
parser.add_argument('--base-url',help='Public deployed site ROOT, without /app/')
args=parser.parse_args()
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def translate_path(self,path):
        return super().translate_path(path.removeprefix('/review'))
server=None
if args.base_url: base=args.base_url.rstrip('/')
else:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/review'
results=[]
if args.base_url:
    import urllib.request
    with urllib.request.urlopen(base+'/app/preview-build.json',timeout=30) as response:manifest=json.load(response)
    for name,expected in manifest['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,('Deployed source differs from checkout',name)
    assert 'app/home.mjs' in manifest['files'] and 'trading/core.mjs' in manifest['files']

with sync_playwright() as p:
    engine=getattr(p,args.browser)
    browser=engine.launch(**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
    profiles=[('desktop',{'viewport':{'width':1440,'height':1000}}),('iphone',p.devices['iPhone 13'])]
    for name,options in profiles:
        # Chromium's mobile context can use the same viewport/touch settings.
        context=browser.new_context(**options)
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/index.html')
        page.get_by_role('navigation').get_by_role('link',name='Application home',exact=True).click()
        expect(page.locator('#event')).to_have_value('harvey-2017-texas')
        expect(page.locator('#event-title')).to_contain_text('Harvey')
        page.locator('#evidence-link').click()
        expect(page.locator('#event')).to_have_value('harvey-2017-texas')
        expect(page.locator('#first-public')).to_contain_text('2017-08-25')
        expect(page.locator('#evidence a').first).to_have_attribute('href',__import__('re').compile('https://'))
        page.locator('#matching-link').click()
        expect(page.locator('#example')).to_have_value('harvey-2017-texas')
        expect(page.locator('#cohort-count')).to_contain_text('2 comparable events')
        assert page.locator('#results [data-event="harvey-2017-texas"]').count()==0
        assert page.locator('#results [data-event="ida-2021-louisiana"]').count()==0
        expect(page.locator('#opportunities tr')).to_have_count(10)
        page.locator('#opportunities tr[data-market="wti"][data-days="3"] button').click()
        expect(page.locator('#market')).to_have_value('wti')
        expect(page.locator('#summary-horizon')).to_have_value('3')
        for scheme in ['light','dark']:
            page.emulate_media(color_scheme=scheme,reduced_motion='reduce')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(name,scheme,'matching')
        page.locator('#practice-link').click()
        expect(page.locator('#research-context')).to_contain_text('Harvey')
        expect(page.locator('#research-context')).to_contain_text('WTI · 3 observation days')
        expect(page.locator('#research-context')).to_contain_text('separate 2016 Brent exercise')
        expect(page.locator('#welcome')).to_be_visible()
        assert page.locator('#mode option[value=current]').is_disabled()
        page.locator('#research-context button').click()
        expect(page.locator('#research-context button')).to_contain_text('no virtual order placed')
        page.click('#start');expect(page.locator('#summary')).to_contain_text('Virtual cash £50.00')
        expect(page.locator('#journal')).to_be_empty()
        expect(page.locator('#reason')).to_have_value(__import__('re').compile('Research only:.*Harvey'))
        page.click('#buy');expect(page.locator('#summary')).to_contain_text('Virtual cash £45.00')
        page.click('#next');expect(page.locator('#clock')).to_contain_text('2016-05-26')
        expect(page.locator('#positions')).to_contain_text('Value £5.07')
        with page.expect_download() as event:page.click('#backup')
        backup=json.loads(Path(event.value.path()).read_text())
        assert backup['journal'][0]['quote']['fx']['rate']==.6805
        assert 'Harvey' in backup['journal'][0]['reason']
        page.locator('#positions button').click();expect(page.locator('#summary')).to_contain_text('Virtual cash £50.07')
        page.reload();expect(page.locator('#summary')).to_contain_text('Virtual cash £50.07')
        for route in ['/app/','/event-research.html?event=harvey-2017-texas','/history.html','/paper.html']:
            page.goto(base+route)
            if '/app/' in route:expect(page.locator('#event')).to_be_enabled()
            for scheme in ['light','dark']:
                page.emulate_media(color_scheme=scheme)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(name,scheme,route)
            assert all(box['height']>=44 for box in page.locator('.app-nav a').evaluate_all('(els)=>els.map(e=>({height:e.getBoundingClientRect().height}))'))
        page.goto(base+'/app/?event=not-a-real-event')
        expect(page.locator('#load-status')).to_contain_text('requested event was not found')
        page.route('**/cohort-catalog.json',lambda r:r.fulfill(status=503,body='unavailable'))
        page.reload();expect(page.locator('#load-status')).to_contain_text('Cannot load')
        expect(page.locator('#matching-link')).not_to_be_visible();expect(page.locator('#retry')).to_be_visible()
        page.unroute('**/cohort-catalog.json');page.click('#retry');expect(page.locator('#event')).to_be_enabled()
        page.route('**/cohort-catalog.json',lambda r:r.fulfill(content_type='application/json',body=json.dumps({'schemaVersion':1,'events':[]})))
        page.reload();expect(page.locator('#load-status')).to_contain_text('No historical events')
        expect(page.locator('#event')).to_be_disabled()
        page.unroute('**/cohort-catalog.json')
        assert not errors,errors
        results.append({'profile':name,'browser':args.browser,'end_to_end':'passed','errors':errors,'physical_device':False})
        context.close()
    # Safari storage denial must not create a fake persistent account or prevent practice.
    context=browser.new_context(viewport={'width':375,'height':812})
    context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Denied','SecurityError')}})")
    page=context.new_page();page.goto(base+'/paper.html')
    expect(page.locator('#storage-status')).to_contain_text('memory for this tab only')
    page.click('#start');page.click('#buy');expect(page.locator('#summary')).to_contain_text('Virtual cash £45.00')
    with page.expect_download() as event:page.click('#backup')
    assert len(json.loads(Path(event.value.path()).read_text())['journal'])==1
    context.close()
    context=browser.new_context();page=context.new_page()
    page.route('**/gbp-usd-brexit-source.csv',lambda r:r.fulfill(status=503,body='unavailable'))
    page.goto(base+'/paper.html');expect(page.locator('#message')).to_contain_text('Cannot start')
    expect(page.locator('#start')).to_be_disabled();context.close()
    browser.close()
if server:server.shutdown()
out=ROOT/'work/application';out.mkdir(parents=True,exist_ok=True)
(out/f'{args.browser}-{"deployed" if args.base_url else "local"}.json').write_text(json.dumps({'base':base,'results':results,'storage_denial':'passed','missing_fx':'passed','physical_device_tested':False},indent=2)+'\n')
print(f'PASS: {args.browser} desktop/iPhone profiles, full dashboard/evidence/matching/practice flow, subdirectory links, persistence/export, failures and storage denial. Physical iPhone NOT tested.')
