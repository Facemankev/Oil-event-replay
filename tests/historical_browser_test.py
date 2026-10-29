"""Static export smoke test at iPad/mobile dimensions; no backend required."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import threading,json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':820,'height':1180},has_touch=True,is_mobile=True)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
 page.locator('a[href="history.html"]').click()
 expect(page.locator('#status')).to_contain_text('5231 prices')
 expect(page.locator('#provenance')).to_contain_text('primary reconciliation pending')
 page.select_option('#series','wti');page.click('#query')
 expect(page.locator('#prices')).to_contain_text('-36.98')
 expect(page.locator('#status')).to_contain_text('5137 prices')
 page.fill('#from','2020-04-25');page.fill('#to','2020-04-26');page.click('#query')
 expect(page.locator('#prices')).to_contain_text('No reported observations')
 page.fill('#from','2006-01-01');page.fill('#to','2026-10-27');page.click('#query')
 expect(page.locator('#status')).to_contain_text('5137 numeric observations')
 assert page.locator('#prices tr').count()==500
 expect(page.locator('#limit')).to_contain_text('first 500')
 page.set_viewport_size({'width':375,'height':812})
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 for theme in ['light','dark']:
  page.emulate_media(color_scheme=theme,reduced_motion='reduce')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.emulate_media(color_scheme='light')
 page.fill('#from','2020-04-17');page.fill('#to','2020-04-24');page.click('#query')
 (ROOT/'work'/'issue10').mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(ROOT/'work'/'issue10'/'history-mobile.png'),full_page=True)
 assert not errors,errors
 browser.close()
server.shutdown()
print('PASS: static SQLite export, provenance, negative WTI price, empty ranges, full counts, table limit, iPad/mobile viewport')
