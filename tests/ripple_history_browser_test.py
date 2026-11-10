"""Issue #25 list/detail, temporal and source safety. Profiles are emulation."""
import argparse, hashlib, json, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
KEY='market-ripple-ripple-practice-v1'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser',choices=['chromium','webkit'],default='chromium')
parser.add_argument('--base-url')
args=parser.parse_args()
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*unused):pass
    def translate_path(self,path):return super().translate_path(path.removeprefix('/check'))
server=None
if args.base_url:base=args.base_url.rstrip('/')
else:
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/check'
out=ROOT/'work/three-step'/args.browser/('deployed' if args.base_url else 'local');out.mkdir(parents=True,exist_ok=True)
results=[]
with sync_playwright() as p:
    browser=getattr(p,args.browser).launch(**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
    for profile,settings in [('desktop',{'viewport':{'width':1440,'height':1000}}),('iphone',p.devices['iPhone 13']),('ipad',p.devices['iPad (gen 7)'])]:
        context=browser.new_context(**settings);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        if args.base_url:
            response=page.goto(base+'/app/preview-build.json');assert response.ok
            manifest=response.json();assert 'ripple/history.mjs' in manifest['files']
            for name,checksum in manifest['files'].items():
                file=(ROOT/name).resolve();assert file.is_relative_to(ROOT)
                assert hashlib.sha256(file.read_bytes()).hexdigest()==checksum,name
        page.goto(base+'/ripple/')
        expect(page.locator('.three-answers dt')).to_have_text(['What happened?','Likely outcome?','Suggested action?'])
        expect(page.locator('#suggested-action')).to_have_text('No action')
        assert page.locator('#view-history').bounding_box()['y']<settings.get('viewport',{}).get('height',844)
        saved=page.evaluate(f'localStorage.getItem("{KEY}")')
        for theme in ['light','dark']:
            page.emulate_media(color_scheme=theme,reduced_motion='reduce')
            page.screenshot(path=str(out/f'{profile}-{theme}-card.png'),full_page=True)
        page.click('#view-history');expect(page.locator('#screen-history')).to_be_visible()
        expect(page.locator('#history-list li')).to_have_count(2)
        assert page.locator('#history-list svg').count()==0
        assert not page.locator('#history-evidence').is_visible()
        titles=page.locator('#history-list strong').all_text_contents()
        dates=[]
        for theme in ['light','dark']:
            page.emulate_media(color_scheme=theme);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/f'{profile}-{theme}-list.png'),full_page=True)
        for index in range(2):
            link=page.locator('#history-list a').nth(index);expect(link).to_be_visible()
            assert link.bounding_box()['height']>=44
            link.click();expect(page.locator('#history-event-title')).to_have_text(titles[index])
            expect(page.locator('#history-chart')).to_have_attribute('data-market','brent')
            brent=json.loads(page.locator('#history-chart').get_attribute('data-observed-dates'));dates.append(brent)
            assert brent and all(d<'2017-08-28' for d in brent)
            expect(page.locator('#history-event-source a')).to_have_attribute('href',__import__('re').compile(r'https://www.nhc.noaa.gov/'))
            assert page.locator('#history-chart [data-entry-date]').count()==0
            page.click('#history-wti');expect(page.locator('#history-chart')).to_have_attribute('data-market','wti')
            expect(page.locator('#history-chart-title')).to_have_text('WTI after this event')
            for theme in ['light','dark']:
                page.emulate_media(color_scheme=theme)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                for selector in ['#history-brent','#history-wti','#screen-event .back-link','#history-event-source a']:
                    assert page.locator(selector).first.bounding_box()['height']>=44
                if index==0:page.screenshot(path=str(out/f'{profile}-{theme}-detail.png'),full_page=True)
            page.locator('#screen-event a[href="#history"]').click()
            expect(page.locator('#screen-history')).to_be_visible()
        assert dates[0]!=dates[1]  # Separate event observations, not one reused chart.
        page.go_back();expect(page.locator('#screen-event')).to_be_visible()
        page.go_forward();expect(page.locator('#screen-history')).to_be_visible()
        page.locator('#screen-history a[href="#opportunities"]').click()
        expect(page.locator('#screen-opportunities')).to_be_visible()
        assert page.evaluate(f'localStorage.getItem("{KEY}")')==saved  # Research never trades/reviews.
        page.goto(base+'/ripple/#event/harvey-2017-texas/brent')
        expect(page.locator('#event-unavailable')).to_be_visible();expect(page.locator('#event-content')).not_to_be_visible()
        assert page.locator('#history-chart polyline').count()==0
        page.goto(base+'/ripple/#event/%/brent');expect(page.locator('#event-unavailable')).to_be_visible()
        for viewport in [{'width':375,'height':812},{'width':844,'height':390}]:
            page.set_viewport_size(viewport);page.goto(base+'/ripple/#history')
            expect(page.locator('#history-list li')).to_have_count(2)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors
        results.append({'profile':profile,'engine':args.browser,'version':browser.version,'passed':True,'physical_device':False});context.close()
    # Missing comparisons are an empty state, never a fabricated example.
    catalog=json.loads((ROOT/'matching/cohort-catalog.json').read_text())
    catalog['events']=[e for e in catalog['events'] if e['id']=='harvey-2017-texas']
    context=browser.new_context();page=context.new_page()
    page.route('**/matching/cohort-catalog.json',lambda r:r.fulfill(json=catalog))
    page.goto(base+'/ripple/#history');expect(page.locator('#history-empty')).to_be_visible()
    expect(page.locator('#history-list li')).to_have_count(0);context.close()
    # Text from research is rendered as text, not executable HTML.
    catalog=json.loads((ROOT/'matching/cohort-catalog.json').read_text())
    storm=next(e for e in catalog['events'] if e['id']=='gustav-2008-louisiana')
    storm['title']='<img src=x onerror=alert(1)>'
    for row in storm['reactions']['markets']['brent']:
        for point in row['observations']:point['value']=None
    context=browser.new_context();page=context.new_page()
    page.route('**/matching/cohort-catalog.json',lambda r:r.fulfill(json=catalog))
    page.goto(base+'/ripple/#event/gustav-2008-louisiana/brent')
    expect(page.locator('#history-event-title')).to_have_text(storm['title'])
    assert page.locator('#history-event-title img').count()==0
    expect(page.locator('#history-chart')).to_have_attribute('aria-label','No sourced observations available for this event and market.')
    assert page.locator('#history-chart polyline').count()==0
    context.close();browser.close()
if server:server.shutdown()
(out/'report.json').write_text(json.dumps({'results':results,'empty_state':'passed','unavailable_prices':'passed','unsafe_html':'passed','physical_device_tested':False},indent=2)+'\n')
print(f'PASS: {args.browser} three answers, separate sourced event charts, routing/back, no account mutation, cutoff, no-match/missing-price states, mobile/desktop/iPad, light/dark; no physical device tested')
