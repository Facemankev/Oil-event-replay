"""Verify source fidelity and the isolated branding preview."""
from pathlib import Path
import hashlib,json,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
preview=ROOT/'preview/gold-desk'
manifest=json.loads((preview/'source.json').read_text())
for name,sha in manifest['files'].items():
 assert (preview/name).read_bytes()==(ROOT/'.claude/skills/market-ripple-design'/name).read_bytes()
 assert hashlib.sha256((preview/name).read_bytes()).hexdigest()==sha
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(f'http://127.0.0.1:{server.server_port}/preview/gold-desk/')
 frame=page.frame_locator('#design')
 expect(frame.locator('#f-before')).to_have_text('$48.63')
 expect(frame.locator('#f-after')).to_have_text('$46.69')
 for width in ['1440','820','1180','auto']:
  page.locator(f'[data-width="{width}"]').click()
  for theme in ['light','dark']:
   frame.locator(f'[data-set-theme="{theme}"]').click()
   expect(frame.locator('html')).to_have_attribute('data-theme',theme)
  for market in ['apple','brent']:
   frame.locator(f'[data-market="{market}"]').click()
   for window in ['30','14']:
    frame.locator(f'[data-window="{window}"]').click()
    assert frame.locator('#rows tr').count()>10
 for size,name in [({'width':1440,'height':1000},'desktop'),({'width':820,'height':1180},'ipad-portrait'),({'width':1180,'height':820},'ipad-landscape'),({'width':375,'height':812},'phone')]:
  page.set_viewport_size(size);page.locator('[data-width="auto"]').click()
  frame.locator('[data-set-theme="light"]').click()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.wait_for_timeout(350)
  (ROOT/'work/brand-preview').mkdir(parents=True,exist_ok=True)
  page.screenshot(path=str(ROOT/f'work/brand-preview/{name}.png'),full_page=True)
 assert not errors,errors
 browser.close()
server.shutdown()
print('PASS: unchanged source bytes, original prices/controls, desktop/iPad/phone layout, light/dark, no browser exceptions')
