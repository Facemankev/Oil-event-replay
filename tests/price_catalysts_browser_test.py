"""Private ledger UI with synthetic controls only; Chromium and real WebKit."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import tempfile,threading,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from price_catalysts.demo import synthetic_report
from price_catalysts.view import render_private

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=['chromium','webkit'],default='chromium');args=parser.parse_args()
    (ROOT/'work').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/'work') as temp:
        folder=Path(temp);report=synthetic_report()
        report['ledger'][0]['evidence']['explanation']='<img id="injected" src=x onerror="window.injected=true">'
        render_private(folder/'index.html',report)
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=folder))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as p:
                browser=getattr(p,args.browser).launch(headless=True,**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
                for name,width,height in [('desktop',1440,1000),('iphone',375,812),('ipad',1024,1366)]:
                    context=browser.new_context(viewport={'width':width,'height':height},is_mobile=name!='desktop',has_touch=name!='desktop',reduced_motion='reduce')
                    page=context.new_page();errors=[];requests=[]
                    page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
                    page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='networkidle')
                    assert page.locator('[data-answer]').count()==3
                    assert page.locator('#action').inner_text()=='No Action'
                    assert 'Outcome-selected' in page.locator('main').inner_text()
                    assert page.locator('#injected').count()==0 and not page.evaluate('Boolean(window.injected)')
                    assert '<img' in page.locator('#explanation').text_content()
                    assert 'https://example.org/' in page.locator('#sources a').first.get_attribute('href')
                    for theme in ['light','dark']:
                        page.locator(f'button[data-theme="{theme}"]').click()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        assert page.locator(f'button[data-theme="{theme}"]').get_attribute('aria-pressed')=='true'
                    uninvestigated=next(r for r in report['ledger'] if not r['evidence']['sources'])
                    page.select_option('#movement',uninvestigated['id'])
                    assert 'Do not invent a catalyst' in page.locator('#sources').inner_text()
                    assert 'Not genuinely unseen' in page.locator('#bias').inner_text()
                    page.get_by_text('Subsequent 1-, 5- and 20-session performance and costs',exact=True).click()
                    assert page.locator('#outcomes tr').count()==12
                    assert '£1 per trade leg' in page.locator('#outcomes').inner_text()
                    page.get_by_text('Historical patterns and independent controls',exact=True).click()
                    assert 'Zero validated Buy' in page.locator('#replay').inner_text()
                    assert page.locator('#control-evidence a').count()==1
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    assert page.evaluate('localStorage.length')==0
                    assert not errors,errors
                    assert all(r.startswith(f'http://127.0.0.1:{server.server_port}/') for r in requests),requests
                    context.close()
                browser.close()
        finally:server.shutdown();server.server_close()
    print(f'PASS: {args.browser} synthetic private ledger; three answers, sources, unexplained/missing data, fees, XSS, no external requests; desktop/iPhone/iPad light/dark. Physical devices untested.')

if __name__=='__main__':main()
