"""Functional regression in Chromium at iPad/mobile sizes; provider responses are test fixtures."""
import json, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':820,'height':1180},has_touch=True,is_mobile=True)
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/paper.html');page.click('#start')
 expect(page.locator('#modeTitle')).to_have_text('Historical practice — not today’s market')
 expect(page.locator('#quote')).to_contain_text('48.8700 USD')
 expect(page.locator('#quote')).to_contain_text('0.680500')
 page.fill('#reason','<img src=x onerror=alert(1)>');page.click('#buy')
 expect(page.locator('#summary')).to_contain_text('Virtual cash £45.00')
 expect(page.locator('#positions')).to_contain_text('Cost £5.00')
 assert page.locator('#journal img').count()==0
 page.click('#next');expect(page.locator('#clock')).to_contain_text('2016-05-26')
 expect(page.locator('#positions')).to_contain_text('Value £5.07')
 with page.expect_download() as event:page.click('#backup')
 data=json.loads(Path(event.value.path()).read_text())
 assert data['journal'][0]['quote']['fx']['rate']==.6805
 assert data['journal'][0]['assumptions']['slippageBps']==0
 page.locator('#positions button').click()
 expect(page.locator('#summary')).to_contain_text('Virtual cash £50.07')
 page.reload();expect(page.locator('#summary')).to_contain_text('Virtual cash £50.07')
 # Source tampering in a backup is rejected before replacing the account.
 data['journal'][0]['quote']['price']=999
 page.set_input_files('#restore',{'name':'tampered.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
 expect(page.locator('#message')).to_contain_text('differs from the committed source')
 page.select_option('#asset','AAPL');expect(page.locator('#buy')).to_be_disabled()
 expect(page.locator('#quote')).to_contain_text('unresolved reuse rights')
 page.select_option('#asset','FX');expect(page.locator('#buy')).to_be_disabled()
 page.set_viewport_size({'width':375,'height':812});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.on('dialog',lambda dialog:dialog.accept());page.click('#reset');assert page.locator('#mode option[value=current]').is_disabled();page.evaluate("document.querySelector('#mode option[value=current]').disabled=false");page.select_option('#mode','current');page.click('#start')
 page.select_option('#asset','AAPL');expect(page.locator('#quote')).to_contain_text('deploy and configure');expect(page.locator('#buy')).to_be_disabled()
 # Separate current-mode account: fixtures never appear in production config/data.
 live=context.new_page();live.on('pageerror',lambda e:errors.append(str(e)))
 live.route('**/trading/config.js',lambda route:route.fulfill(content_type='application/javascript',body="window.MARKET_RIPPLE_PRICE_PROXY='https://fixture.example/quote';"))
 def respond(route):
  stamp=live.evaluate('new Date().toISOString()')
  quote={'asset':'AAPL','mode':'current','price':100,'currency':'USD','timestamp':stamp,'source':'TEST FIXTURE','evidence':'TEST ONLY','gbpPerUnit':.8,'fx':{'base':'USD','quote':'GBP','rate':.8,'timestamp':stamp,'source':'TEST FIXTURE FX','evidence':'TEST ONLY'},'delaySeconds':0,'marketStatus':'open','corporateActions':'current-unadjusted'}
  route.fulfill(content_type='application/json',body=json.dumps(quote),headers={'Access-Control-Allow-Origin':'*'})
 live.route('https://fixture.example/**',respond)
 live.clock.install();live.goto(base+'/paper.html');live.select_option('#asset','AAPL');live.click('#refresh')
 expect(live.locator('#buy')).to_be_enabled();live.click('#buy');expect(live.locator('#positions')).to_contain_text('0.06250000')
 live.clock.fast_forward(130000);expect(live.locator('#buy')).to_be_disabled();expect(live.locator('#positions button')).to_be_disabled()
 live.route('https://fixture.example/**',lambda route:route.fulfill(status=503,content_type='application/json',body='{}',headers={'Access-Control-Allow-Origin':'*'}))
 live.click('#refresh');expect(live.locator('#buy')).to_be_disabled();expect(live.locator('#positions button')).to_be_disabled()
 expect(live.locator('#summary')).to_contain_text('Account total unavailable')
 assert not errors,errors
 browser.close()
server.shutdown()
print('PASS: historical buy/revalue/close, FX, persistence, backup evidence, tampering/XSS, unavailable assets, current provider failure, iPad/mobile layout')
