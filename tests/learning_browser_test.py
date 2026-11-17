"""Opt-in retrospective simulation on desktop, phone and tablet; no physical-device claim."""
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
        url=f'http://127.0.0.1:{server.server_port}/learning/'
    output=ROOT/'work/learn1/screens';output.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=getattr(p,args.browser).launch(headless=True,**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
            for name,width,height in [('desktop',1440,1100),('iphone',375,812),('ipad',1024,1366)]:
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(url,wait_until='networkidle')
                page.wait_for_selector('#case:not([disabled])',state='attached')
                assert page.locator('#answers').is_hidden()
                page.check('#opt-in')
                assert page.locator('[data-answer]').count()==3
                assert page.locator('#action').inner_text()=='Research Watch'
                assert 'Chronological research' in page.locator('.mr-badge').inner_text()
                for theme in ['light','dark']:
                    page.locator(f'button[data-theme="{theme}"]').click()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(output/f'{args.browser}-{name}-{theme}.png'),full_page=True)
                report=page.evaluate("async()=>await (await fetch('report.json')).json()")
                for sign in ['positive','negative']:
                    index=next(i for i,c in enumerate(report['records']) if c['outcome'].get('net_outcome')==sign)
                    page.select_option('#case',str(index))
                    page.get_by_text('Inspect the later dated hypothetical outcome',exact=True).click()
                    assert 'net' in page.locator('#outcome').inner_text()
                    assert page.locator('#path').text_content().find('Hypothetical Buy')>=0
                    assert page.locator('#path').text_content().find('Hypothetical Sell')>=0
                    page.get_by_text('Inspect the later dated hypothetical outcome',exact=True).click()
                index=next(i for i,c in enumerate(report['records']) if c['prediction']['rule'] is None)
                page.select_option('#case',str(index));assert page.locator('#action').inner_text()=='No Action'
                assert 'No earlier same-market' in page.locator('#meaning').inner_text()
                assert page.evaluate('localStorage.length')==0
                page.evaluate("""async()=>{const m=await import('./view.mjs');const d=await (await fetch('report.json')).json();d.records[0].prediction.title='<img id="injected" src=x onerror="window.injected=true">';m.render(d,0);}""")
                assert page.locator('#injected').count()==0
                assert not page.evaluate('Boolean(window.injected)')
                page.uncheck('#opt-in');assert page.locator('#answers').is_hidden()
                assert not errors,errors
                context.close()
            # Missing evidence fails closed instead of retaining an old recommendation.
            context=browser.new_context();page=context.new_page()
            page.route('**/report.json',lambda route:route.fulfill(status=404,body='missing'))
            page.goto(url,wait_until='networkidle')
            assert page.locator('#answers').is_hidden()
            assert 'could not load' in page.locator('#load-status').inner_text()
            context.close();browser.close()
    finally:
        if server:server.shutdown();server.server_close()
    print(f'PASS: {args.browser} opt-in chronological learning, Watch/No Action, positive/negative/missing paths, three answers, XSS, unchanged accounts, light/dark desktop/iPhone/iPad; no physical device tested')


if __name__=='__main__':main()
