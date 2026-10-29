"""Static event explorer, known-time caveats and responsive layouts."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
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
 page.goto(f'http://127.0.0.1:{server.server_port}/event-research.html')
 expect(page.locator('#status')).to_contain_text('24 events')
 assert page.locator('#event option').count()==24
 page.select_option('#event','ike-2008-galveston')
 expect(page.locator('#results')).to_contain_text('-0.9643%')
 expect(page.locator('#results')).to_contain_text('2.8264%')
 expect(page.locator('#first-public')).to_contain_text('02:30:00-05:00')
 assert page.locator('#observations tr').count()==10
 page.select_option('#event','saudi-2019-abqaiq')
 expect(page.locator('#first-public')).to_contain_text('not established')
 expect(page.locator('#alignment')).to_contain_text('2019-09-23')
 expect(page.locator('#confidence')).to_contain_text('not eligible')
 page.select_option('#category','weather');assert page.locator('#event option').count()==6
 for theme in ['light','dark']:
  page.emulate_media(color_scheme=theme,reduced_motion='reduce')
  for size in [{'width':820,'height':1180},{'width':375,'height':812}]:
   page.set_viewport_size(size);assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.emulate_media(color_scheme='light');page.select_option('#event','ike-2008-galveston')
 (ROOT/'work'/'issue13').mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(ROOT/'work'/'issue13'/'event-research-mobile.png'),full_page=True)
 # Imported text never becomes markup, including an untrusted source URL.
 payload=json.loads((ROOT/'data/world-event-research.json').read_text())
 payload['events'][0]['description']='<img src=x onerror=alert(1)>'
 payload['events'][0]['evidence'][0]['url']='javascript:alert(1)'
 page.route('**/data/world-event-research.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(payload)))
 page.reload();expect(page.locator('#description')).to_contain_text('<img')
 assert page.locator('#description img').count()==0
 assert page.locator('#evidence a').count()==0
 assert not errors,errors
 browser.close()
server.shutdown()
print('PASS: 24-event explorer, actual comparisons, first-public caveats, late evidence alignment, shared rows, category filter, light/dark iPad/mobile layouts, safe text/links')
