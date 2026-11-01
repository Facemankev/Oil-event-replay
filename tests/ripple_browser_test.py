"""Two-screen historical replay in real browser engines; device profiles are emulation."""
import argparse, hashlib, json, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
KEY='market-ripple-ripple-practice-v1'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser',choices=['chromium','webkit'],default='chromium')
parser.add_argument('--base-url',help='Public preview root, without /ripple/')
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
mode='deployed' if args.base_url else 'local'
out=ROOT/'work/ripple'/args.browser/mode;out.mkdir(parents=True,exist_ok=True)
results=[]
with sync_playwright() as p:
    browser=getattr(p,args.browser).launch(**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
    for profile,settings in [('desktop',{'viewport':{'width':1440,'height':1000}}),('iphone',p.devices['iPhone 13'])]:
        context=browser.new_context(**settings)
        context.add_init_script("localStorage.setItem('market-ripple-practice-v2','parent-account-sentinel')")
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        if args.base_url:
            response=page.goto(base+'/app/preview-build.json');assert response.ok
            manifest=response.json()
            assert {'ripple/ui.mjs','ripple/model.mjs','ripple/paths.mjs','ripple/data.json','ripple/chart.mjs'}.issubset(manifest['files'])
            for name,checksum in manifest['files'].items():
                path=(ROOT/name).resolve();assert path.is_relative_to(ROOT)
                assert hashlib.sha256(path.read_bytes()).hexdigest()==checksum,('Deployed source differs',name)
        page.goto(base+'/ripple/')
        expect(page.locator('#ripples ol')).to_have_count(2)
        expect(page.locator('#opportunity-state')).to_contain_text('No sufficiently supported opportunities')
        expect(page.locator('#screen-opportunities')).to_be_visible();expect(page.locator('#screen-decision')).not_to_be_visible()
        assert page.locator('#ripples li').count()==6
        assert not page.locator('#opportunity-evidence').is_visible()
        page.locator('#screen-opportunities details summary').click()
        expect(page.locator('#opportunity-evidence')).to_contain_text('2 non-overlapping five-day')
        expect(page.locator('#opportunity-evidence')).to_contain_text('1 usable full historical path')
        assert page.locator('#opportunity-evidence a[href*="32852"]').count()==0
        page.locator('#screen-opportunities details summary').click()
        page.locator('.main-action').click()
        expect(page.locator('#action-title')).to_have_text('No Action')
        expect(page.locator('#price')).to_have_text('£40.13')
        expect(page.locator('#replay-date')).to_contain_text('28 Aug 2017')
        assert all(d<='2017-08-28' for d in json.loads(page.locator('#price-chart').get_attribute('data-observed-dates')))
        page.locator('#inspect').evaluate("e=>{e.value='0';e.dispatchEvent(new Event('input'))}")
        expect(page.locator('#inspection')).to_contain_text('14 Aug 2017')
        # Inspection of a prior point must not supply the virtual fill.
        def reject(dialog):
            assert '2017-08-28' in dialog.message and '40.126632' in dialog.message
            dialog.dismiss()
        page.once('dialog',reject);page.click('#buy')
        expect(page.locator('#position-value')).to_have_text('£50.00')
        page.once('dialog',lambda d:d.accept());page.click('#buy')
        expect(page.locator('#action-title')).to_have_text('Hold')
        expect(page.locator('#cash')).to_contain_text('Cash £45.00')
        assert page.locator('#price-chart [data-entry-date="2017-08-28"]').count()==1
        for index in range(4):
            page.click('#next');expect(page.locator('#action-title')).to_have_text('Hold')
        page.click('#next');expect(page.locator('#replay-date')).to_contain_text('5 Sept 2017')
        expect(page.locator('#action-title')).to_have_text('Review Sell')
        expect(page.locator('#action-reason')).to_contain_text('5-step review horizon')
        assert '2017-09-04' not in json.loads(page.locator('#price-chart').get_attribute('data-observed-dates'))
        assert page.locator('#decision-evidence a[href*="32852"]').count()==0
        page.click('#dismiss');expect(page.locator('#dismiss')).to_be_disabled()
        expect(page.locator('#review-response')).to_contain_text('dismissed')
        assert page.locator('#sell').is_visible()
        for theme in ['light','dark']:
            page.emulate_media(color_scheme=theme,reduced_motion='reduce')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(profile,theme)
            for selector in ['#next','#sell','#nav-opportunities']:
                assert page.locator(selector).bounding_box()['height']>=44
            page.screenshot(path=str(out/f'{profile}-{theme}-decision.png'),full_page=True)
        page.once('dialog',lambda d:d.accept());page.click('#sell')
        expect(page.locator('#position-value')).to_have_text('£50.14')
        expect(page.locator('#action-title')).to_have_text('No Action')
        page.locator('summary',has_text='Keep or reset this practice').click()
        with page.expect_download() as event:page.click('#backup')
        backup=json.loads(Path(event.value.path()).read_text())
        entry=backup['entries']['1']
        assert entry['entry_price_gbp']==51.87*.7736
        assert entry['exit_criteria']['horizon']==5
        assert entry['outcome']['known_at']=='2017-09-05'
        assert any(any(reply['choice']=='dismissed' for reply in r['responses']) for r in backup['suggestions'])
        assert any(any(reply['choice']=='accepted_paper_sell' for reply in r['responses']) for r in backup['suggestions'])
        count=len(backup['suggestions']);page.reload()
        expect(page.locator('#position-value')).to_have_text('£50.14')
        assert page.locator('#review-log tr').count()==count
        page.locator('#nav-opportunities').click();expect(page.locator('#screen-opportunities')).to_be_visible()
        for theme in ['light','dark']:
            page.emulate_media(color_scheme=theme)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/f'{profile}-{theme}-opportunities.png'),full_page=True)
        page.go_back();expect(page.locator('#screen-decision')).to_be_visible()
        page.go_forward();expect(page.locator('#screen-opportunities')).to_be_visible()
        page.locator('.main-action').click()
        page.locator('summary',has_text='Keep or reset this practice').click()
        bad=json.loads(json.dumps(backup));bad['entries']['1']['entry_price_gbp']=999
        page.set_input_files('#restore',{'name':'bad.json','mimeType':'application/json','buffer':json.dumps(bad).encode()})
        expect(page.locator('#status')).to_contain_text('Restore rejected')
        expect(page.locator('#position-value')).to_have_text('£50.14')
        page.once('dialog',lambda d:d.accept());page.click('#reset')
        expect(page.locator('#replay-date')).to_contain_text('28 Aug 2017')
        page.once('dialog',lambda d:d.accept())
        page.set_input_files('#restore',{'name':'valid.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})
        expect(page.locator('#status')).to_contain_text('Verified backup restored')
        expect(page.locator('#position-value')).to_have_text('£50.14')
        assert page.evaluate("localStorage.getItem('market-ripple-practice-v2')")=='parent-account-sentinel'
        for viewport in [{'width':375,'height':812},{'width':844,'height':390}]:
            page.set_viewport_size(viewport);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors
        results.append({'profile':profile,'engine':args.browser,'engine_version':browser.version,'end_to_end':'passed','physical_device':False})
        context.close()
    context=browser.new_context(viewport={'width':375,'height':812})
    context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Denied','SecurityError')}})")
    page=context.new_page();page.goto(base+'/ripple/#decision')
    expect(page.locator('#storage')).to_contain_text('memory-only')
    page.once('dialog',lambda d:d.accept());page.click('#buy');expect(page.locator('#action-title')).to_have_text('Hold')
    context.close()
    context=browser.new_context();page=context.new_page()
    page.route('**/ripple/data.json',lambda r:r.fulfill(status=503,body='unavailable'))
    page.goto(base+'/ripple/');expect(page.locator('#status')).to_contain_text('Cannot load')
    expect(page.locator('#screen-opportunities')).not_to_be_visible();expect(page.locator('#retry')).to_be_visible()
    page.unroute('**/ripple/data.json');page.click('#retry');expect(page.locator('#ripples ol')).to_have_count(2)
    context.close();browser.close()
if server:server.shutdown()
(out/'report.json').write_text(json.dumps({'results':results,'base':base,'physical_device_tested':False,'storage_denial':'passed','data_failure_retry':'passed'},indent=2)+'\n')
print(f'PASS: {args.browser} two-screen ripple/replay, dated same-price chart, explicit buy, hold, justified sell review, outcomes/backup, future exclusions, optional research, mobile layouts; physical iPhone NOT tested')
