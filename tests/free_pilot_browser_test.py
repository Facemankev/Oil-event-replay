"""Gold × Desk historical demo on desktop, phone and tablet; no physical-device claim."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',choices=['chromium','webkit'],default='chromium')
    parser.add_argument('--base-url')
    args=parser.parse_args()
    server=None
    if args.base_url:
        url=args.base_url.rstrip('/')+'/'
    else:
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=ROOT))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url=f'http://127.0.0.1:{server.server_port}/free_pilot/'
    output=ROOT/'work/free-pilot/screens';output.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=getattr(p,args.browser).launch(headless=True,**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
            for name,width,height in [('desktop',1440,1100),('iphone',375,812),('ipad',1024,1366)]:
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(url,wait_until='networkidle')
                page.wait_for_selector('#answers:not([hidden])')
                assert page.locator('[data-answer]').count()==3
                assert page.locator('#action').inner_text()=='No Action'
                assert '4.27%' in page.locator('#reaction').inner_text()
                assert '13.26%' in page.locator('#reaction').inner_text()
                assert 'historical' in page.locator('.mr-badge').inner_text().lower()
                for theme in ['light','dark']:
                    page.locator(f'button[data-theme="{theme}"]').click()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(output/f'{args.browser}-{name}-{theme}.png'),full_page=True)
                for case in ['harvey','nvidia','biogen','fed','nvidia_board']:
                    page.select_option('#case',case)
                    assert page.locator('#action').inner_text()=='No Action'
                    assert page.locator('[data-answer]').count()==3
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.select_option('#case','nvidia')
                page.get_by_text('View historical comparisons and evidence',exact=True).click()
                assert page.locator('#matches li').count()==2
                assert 'Unavailable' in page.locator('#reactions').text_content()
                page.select_option('#case','harvey')
                page.get_by_text('View dated market reactions',exact=True).click()
                assert '2017-' in page.locator('#reactions').inner_text()
                assert page.locator('#reactions tr').count()>=20
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                assert page.evaluate('localStorage.length')==0
                # Data strings are displayed as text; an injected title cannot create an element.
                page.evaluate("""async()=>{const m=await import('./view.mjs');const d=await (await fetch('demo.json')).json();d.cases[0].three_answers.what_happened='<img id="injected" src=x onerror="window.injected=true">';m.renderCase(d,'harvey');}""")
                assert page.locator('#injected').count()==0
                assert not page.evaluate('Boolean(window.injected)')
                assert not errors,errors
                context.close()
            # Missing evidence fails closed instead of retaining an old recommendation.
            context=browser.new_context();page=context.new_page()
            page.route('**/demo.json',lambda route:route.fulfill(status=404,body='missing'))
            page.goto(url,wait_until='networkidle')
            assert page.locator('#answers').is_hidden()
            assert 'could not load' in page.locator('#load-status').inner_text()
            context.close();browser.close()
    finally:
        if server:server.shutdown();server.server_close()
    print(f'PASS: {args.browser} zero-cost demo, five cases, three answers, sources, missing data, XSS, unchanged accounts, light/dark desktop/iPhone/iPad; no physical device tested')


if __name__=='__main__':main()
