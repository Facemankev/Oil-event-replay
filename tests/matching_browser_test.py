"""Usable matching inputs/results, source gates, failures and Gold × Desk layouts."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    url=f'http://127.0.0.1:{server.server_port}/matching/'
    page.emulate_media(color_scheme='dark')
    page.goto(url)
    expect(page.locator('#theme')).to_have_text('Use light mode')
    page.click('#theme')
    expect(page.locator('html')).to_have_attribute('data-theme','light')
    expect(page.locator('#verification')).to_contain_text('blocked')
    expect(page.locator('#results article')).to_have_count(6)
    expect(page.locator('#results article').first).to_contain_text('Limited evidence')
    expect(page.locator('#results article').first.locator('.reaction-list li')).to_have_count(5)
    expect(page.locator('#results article').first).to_contain_text('Provisional seed prices')
    page.check('#verified-only')
    expect(page.locator('#results article').first).to_contain_text('unverified price numbers are hidden')
    assert '%' not in page.locator('#results .reaction-list').first.inner_text()
    page.uncheck('#verified-only')
    page.select_option('#example','harvey-2017-texas')
    expect(page.locator('#results article')).to_have_count(3)
    assert page.locator('[data-event="harvey-2017-texas"]').count()==0
    assert page.locator('[data-event="ida-2021-louisiana"]').count()==0
    page.select_option('#example','saudi-2019-abqaiq')
    expect(page.locator('#public')).to_have_value('2019-09-23')
    page.select_option('#example','')
    page.select_option('#category','production_policy')
    page.select_option('#mechanism','output_increase')
    page.fill('#public','2026-10-29');page.fill('#occurred','2026-10-29')
    page.fill('#title','<img src=x onerror=alert(1)>')
    page.locator('button[type=submit]').click()
    expect(page.locator('#summary')).to_contain_text('<img src=x onerror=alert(1)>')
    assert page.locator('#summary img').count()==0
    assert page.locator('[data-event="opec-2022-october"]').count()==0
    page.fill('#public','2000-01-01');page.locator('button[type=submit]').click()
    expect(page.locator('#results article')).to_have_count(0)
    expect(page.locator('#summary')).to_contain_text('No sufficiently comparable')
    page.select_option('#category','weather');page.select_option('#mechanism','landfall')
    page.fill('#title','Hypothetical Gulf storm');page.fill('#location','Gulf of Mexico')
    page.fill('#public','2026-10-29');page.locator('button[type=submit]').click()
    page.locator('#results details').first.locator('summary').click()
    expect(page.locator('#results article').first).to_contain_text('SHA-256')
    assert page.locator('#results details a').first.get_attribute('href').startswith('https://')
    for size,name in [({'width':1440,'height':1000},'desktop'),({'width':820,'height':1180},'ipad'),({'width':1180,'height':820},'ipad-landscape'),({'width':375,'height':812},'phone')]:
        page.set_viewport_size(size)
        for theme in ['light','dark']:
            page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
            page.emulate_media(reduced_motion='reduce')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(name,theme)
            assert page.locator('button[type=submit]').bounding_box()['height']>=44
        page.evaluate("document.documentElement.dataset.theme='light'")
        (ROOT/'work/matching').mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(ROOT/f'work/matching/{name}.png'),full_page=True)
    assert not errors,errors
    page.route('**/catalog.json',lambda route:route.fulfill(status=500,body='unavailable'))
    page.reload()
    expect(page.locator('#verification')).to_contain_text('could not load')
    expect(page.locator('button[type=submit]')).to_be_disabled()
    browser.close()
server.shutdown()
print('PASS: matching, disclosure dates, source gate, no-match, safe text, price evidence, missing export, desktop/iPad/mobile and light/dark')
