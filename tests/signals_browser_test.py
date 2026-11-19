"""Synthetic historical ratings, private import and unchanged paper-state safeguards."""
import argparse,json,sys,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from signal_ratings.demo import screen_fixture
from signal_ratings.view import render_screen

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--browser',choices=['chromium','webkit'],default='chromium');args=p.parse_args()
    (ROOT/'work').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
        folder=Path(folder);fixture=screen_fixture();fixture['cards'][0]['title']='<img id="injected" src=x onerror="window.injected=true">'
        render_screen(folder/'index.html',fixture)
        forged=json.loads(json.dumps(fixture));forged['cards'][0]['ratings']['declared']['rating']='LIKELY';forged['likely_approved_validation_ids']=['forged'];(folder/'forged.json').write_text(json.dumps(forged))
        (folder/'invalid.json').write_text('{bad json')
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=folder));threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as pw:
                browser=getattr(pw,args.browser).launch(headless=True,**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
                for name,width,height in [('desktop',1440,1000),('iphone',375,812),('ipad',1024,1366)]:
                    context=browser.new_context(viewport={'width':width,'height':height},is_mobile=name!='desktop',has_touch=name!='desktop',reduced_motion='reduce')
                    page=context.new_page();errors=[];requests=[]
                    page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
                    page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='networkidle')
                    assert 'SYNTHETIC' in page.locator('#status').inner_text()
                    assert page.locator('#opportunity .three-answers>div').count()==3
                    assert 'No LIKELY' in page.locator('#validation-note').inner_text()
                    page.select_option('#market','NVDA');assert page.locator('#signal-rating').inner_text()=='POSSIBLE'
                    assert '↑ UP' in page.locator('#signal-window').inner_text();assert '5 trading sessions' in page.locator('#signal-window').inner_text()
                    assert page.locator('#injected').count()==0 and not page.evaluate('Boolean(window.injected)')
                    page.get_by_text('Evidence, historical examples and outcomes',exact=True).click()
                    assert '18 complete' in page.locator('#sample').inner_text()
                    assert 'Average / median price return' in page.locator('#stats').inner_text()
                    assert '66.67%' in page.locator('#stats').inner_text()
                    assert page.locator('#examples li').count()==2
                    assert 'https://example.org/' in page.locator('#examples a').first.get_attribute('href')
                    page.select_option('#example-filter','unsuccessful');assert page.locator('#examples li').count()==1
                    assert 'Unsuccessful direction' in page.locator('#examples').inner_text()
                    page.select_option('#cost','small_account_flat_fee');assert page.locator('#signal-rating').inner_text()=='NO ACTION'
                    assert page.locator('#signal-window').inner_text()=='Direction uncertain'
                    page.select_option('#cost','declared');page.select_option('#market','MRNA');assert '↓ DOWN' in page.locator('#signal-window').inner_text()
                    assert 'Watch downside risk' in page.locator('#action').inner_text()
                    page.locator('#current-mode').click();assert page.locator('#current').is_visible()
                    assert 'NO ACTION' in page.locator('#current').inner_text()
                    page.locator('#historical-mode').click();page.select_option('#rating-filter','LIKELY')
                    assert page.locator('#empty').is_visible();assert page.locator('#opportunity').is_hidden()
                    for theme in ['light','dark']:
                        page.locator(f'button[data-theme="{theme}"]').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.locator('#file-panel summary').click();page.locator('#private-file').set_input_files(folder/'forged.json')
                    page.select_option('#rating-filter','all');page.select_option('#market','NVDA')
                    assert page.locator('#signal-rating').inner_text()=='NO ACTION'
                    page.locator('#private-file').set_input_files(folder/'invalid.json')
                    page.locator('#research').wait_for(state='hidden');assert 'Could not load private evidence' in page.locator('#status').inner_text()
                    assert page.evaluate('localStorage.length')==0
                    assert not errors,errors
                    assert all(r.startswith(f'http://127.0.0.1:{server.server_port}/') for r in requests),requests
                    context.close()
                # Exercise the actual static module/fetch entry point as well
                # as the standalone private HTML generated above.
                public=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=ROOT))
                threading.Thread(target=public.serve_forever,daemon=True).start()
                try:
                    source=folder/'screen.json';source.write_text(json.dumps(fixture))
                    context=browser.new_context(viewport={'width':375,'height':812},is_mobile=True,has_touch=True)
                    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    page.goto(f'http://127.0.0.1:{public.server_port}/signals/',wait_until='networkidle')
                    assert page.locator('#research').is_hidden()
                    page.locator('#file-panel summary').click();page.locator('#private-file').set_input_files(source)
                    page.locator('#research').wait_for(state='visible')
                    assert 'SYNTHETIC' in page.locator('#status').inner_text()
                    assert not errors,errors
                    context.close()
                    context=browser.new_context();page=context.new_page()
                    page.route('**/signal_ratings/policy.json',lambda route:route.fulfill(status=500,body='unavailable'))
                    page.goto(f'http://127.0.0.1:{public.server_port}/signals/',wait_until='networkidle')
                    assert page.locator('#research').is_hidden()
                    assert 'Could not load the registered policy' in page.locator('#status').inner_text()
                    context.close()
                finally:public.shutdown();public.server_close()
                browser.close()
        finally:server.shutdown();server.server_close()
    print(f'PASS: {args.browser} SIGNAL-1 synthetic ratings, three questions, costs, statistics, both outcomes, forged-Likely rejection, private import, XSS, no uploads/state changes; desktop/iPhone/iPad light/dark. Physical Safari untested.')

if __name__=='__main__':main()
