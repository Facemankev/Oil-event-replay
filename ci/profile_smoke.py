"""Every approved research page in both themes on actual desktop/touch profiles."""
import argparse,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--browser',choices=['chromium','webkit'],required=True);args=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=ROOT))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    output=ROOT/'work/ci-browser'/args.browser/'profiles';output.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=getattr(p,args.browser).launch(headless=True,**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if args.browser=='chromium' else {}))
            profiles=[('desktop',{'viewport':{'width':1440,'height':1000}}),('iphone',p.devices['iPhone 13']),('ipad',p.devices['iPad (gen 7)'])]
            for name,device in profiles:
                for theme in ('light','dark'):
                    context=browser.new_context(**device,color_scheme=theme,reduced_motion='reduce');page=context.new_page();errors=[]
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    for folder in ('ripple','free_pilot','simulations','learning'):
                        storage_before=page.evaluate('JSON.stringify(localStorage)') if page.url.startswith('http://127.0.0.1:') else None
                        page.goto(f'http://127.0.0.1:{server.server_port}/{folder}/',wait_until='networkidle')
                        if folder=='ripple':
                            page.wait_for_selector('#screen-opportunities:not([hidden])')
                            assert page.locator('#event-title').inner_text()
                            assert page.locator('.opportunity-card dd').count()==3 or page.locator('#screen-opportunities dd').count()==3
                            before=page.evaluate('JSON.stringify(localStorage)')
                            page.locator('#view-history').click();page.wait_for_selector('#history-list li')
                            page.locator('#history-list a').first.click();page.wait_for_selector('#history-event-title')
                            assert page.locator('#history-event-source a').count()>0
                            assert page.evaluate('JSON.stringify(localStorage)')==before
                        else:
                            page.wait_for_selector('#case:not([disabled])',state='attached')
                            if folder!='free_pilot':page.check('#opt-in')
                            assert page.locator('[data-answer]').count()==3
                            if storage_before is not None:assert page.evaluate('JSON.stringify(localStorage)')==storage_before
                            if folder=='free_pilot':page.get_by_text('View historical comparisons and evidence',exact=True).click()
                            if folder=='simulations':page.get_by_text('View the dated hypothetical path',exact=True).click()
                            if folder=='learning':page.get_by_text('Inspect the earlier learning and validation',exact=True).click()
                        page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
                        expected='#26292d' if theme=='dark' else '#f7f8f6'
                        assert page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--mr-paper").trim()')==expected
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(name,theme,folder)
                        page.screenshot(path=str(output/f'{folder}-{name}-{theme}.png'),full_page=True)
                    assert not errors,errors
                    context.close()
            browser.close()
    finally:server.shutdown();server.server_close()
    print('PASS: four approved pages, desktop/iPhone/iPad touch profiles, light/dark, source navigation and unchanged accounts; '+args.browser)

if __name__=='__main__':main()
