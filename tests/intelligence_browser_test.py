"""INT-1 integration through the unchanged three-step UI; devices are profiles."""
import argparse,json,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser',choices=['chromium','webkit'],default='chromium')
args=parser.parse_args()
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*unused):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
out=ROOT/'work/intelligence'/args.browser;out.mkdir(parents=True,exist_ok=True)
results=[]
with sync_playwright() as p:
    browser=getattr(p,args.browser).launch(**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
    for name,settings in [('desktop',{'viewport':{'width':1440,'height':1000}}),('iphone',p.devices['iPhone 13'])]:
        context=browser.new_context(**settings);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/ripple/');expect(page.locator('#screen-opportunities')).to_be_visible(timeout=20000)
        expect(page.locator('.three-answers dt')).to_have_text(['What happened?','Likely outcome?','Suggested action?'])
        expect(page.locator('#suggested-action')).to_have_text('No action')
        page.click('#view-history');expect(page.locator('#screen-history')).to_be_visible()
        expect(page.locator('#history-list li')).to_have_count(2)
        page.locator('#history-list a').first.click();expect(page.locator('#screen-event')).to_be_visible()
        page.click('#nav-decision');expect(page.locator('#screen-decision')).to_be_visible()
        page.locator('#manual-practice > summary').click();page.fill('#amount','6')
        page.once('dialog',lambda d:d.accept());page.click('#buy')
        expect(page.locator('#status')).to_contain_text('Paper risk budget allows at most £5.00')
        expect(page.locator('#position-value')).to_have_text('£50.00')
        page.fill('#amount','5');page.once('dialog',lambda d:d.accept());page.click('#buy')
        expect(page.locator('#action-title')).to_have_text('Hold')
        for _ in range(5):page.click('#next')
        expect(page.locator('#action-title')).to_have_text('Review selling')
        expect(page.locator('#replay-date')).to_contain_text('5 Sept 2017')
        page.locator('summary',has_text='Keep or reset this practice').click()
        with page.expect_download() as downloaded:page.click('#backup')
        record=json.loads(Path(downloaded.value.path()).read_text())
        assert record['version']==2 and record['policy_version']=='int-1-v1'
        entry=record['entries']['1'];assert entry['risk_budget']['max_allocation_gbp']==5
        assert entry['decision_trace']['prompt']['action']=='No Action'
        assert record['account']['positions'] and entry['outcome'] is None
        assert all('decision_trace' in review for review in record['suggestions'])
        for theme in ['light','dark']:
            page.emulate_media(color_scheme=theme,reduced_motion='reduce')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/f'{name}-{theme}-decision.png'),full_page=True)
        page.reload();expect(page.locator('#action-title')).to_have_text('Review selling')
        # Actual parent-generated v1 ledger restores exactly; no silent migration.
        page.locator('summary',has_text='Keep or reset this practice').click()
        old=json.loads((ROOT/'tests/fixtures/int1-legacy-v1.json').read_text())['record']
        page.once('dialog',lambda d:d.accept())
        page.set_input_files('#restore',{'name':'legacy.json','mimeType':'application/json','buffer':json.dumps(old).encode()})
        expect(page.locator('#status')).to_contain_text('Verified backup restored')
        expect(page.locator('#action-title')).to_have_text('Hold')
        with page.expect_download() as downloaded:page.click('#backup')
        restored=json.loads(Path(downloaded.value.path()).read_text());assert restored==old
        assert not errors,errors
        results.append({'profile':name,'engine':args.browser,'passed':True,'physical_device':False});context.close()
    browser.close()
server.shutdown()
(out/'report.json').write_text(json.dumps({'results':results,'interface_changed':False,'physical_device_tested':False},indent=2)+'\n')
print(f'PASS: {args.browser} unchanged three answers/list/details, risk cap, Hold/review, auditable v2 backup and exact legacy restore; physical devices not tested')
