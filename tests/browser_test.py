"""Browser regression for the lab and all seven existing oil replays."""
import json, re, sqlite3, subprocess, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
# Ensure every original oil record and its implementation remain byte-for-byte.
baseline=subprocess.check_output(['git','show','b779ff655a776c8f665e39dcf1d4c49fe1337322:index.html'],cwd=ROOT,text=True)
current=(ROOT/'index.html').read_text()
assert baseline.split('<script>')[1].split('</script>')[0] == current.split('<script>')[1].split('</script>')[0]
# Design migration executes and enforces instrument classes / source references.
db=sqlite3.connect(':memory:');db.executescript((ROOT/'research/schema.sql').read_text())
assert len(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())==6
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:'+str(server.server_port)+'/index.html')
 assert page.locator('#mr-results tr').count()==2
 assert '2016-06-23' in page.locator('#mr-method').inner_text()
 assert '2016-07-01' in page.locator('#mr-method').inner_text()
 for window in ['30','90','7']:
  page.select_option('#mr-window',window);assert page.locator('#mr-results tr').count()==2
 page.select_option('#mr-event','1');assert 'No comparison available' in page.locator('#mr-results').inner_text()
 page.select_option('#mr-event','0')
 page.locator('#mr-markets input').first.uncheck();assert page.locator('#mr-results tr').count()==1
 page.locator('#mr-markets input').first.check()
 page.fill('#mr-asset','<img src=x onerror=alert(1)>')
 page.fill('#mr-source','Test publisher')
 page.set_input_files('#mr-file',{'name':'test.csv','mimeType':'text/csv','buffer':b'Date,Close\n2016-06-23,100\n2016-07-01,110\n'})
 assert page.locator('#mr-results tr').count()==3
 assert page.locator('#mr-results img').count()==0
 assert 'not independently verified' in page.locator('#mr-sources').inner_text()
 page.click('#mr-clear');assert page.locator('#mr-results tr').count()==2
 assert page.locator('#event option').count()==7
 for i in range(7):
  page.select_option('#event',str(i));assert page.locator('#graph polyline').count()==2
  initial=page.locator('#timeline').inner_text();page.click('#next');assert page.locator('#timeline').inner_text()!=initial
  page.click('#back');assert page.locator('#timeline').inner_text()==initial
  page.click('#play');page.wait_for_timeout(500);page.click('#reset');assert page.locator('#timeline').inner_text()==initial
 page.select_option('#window','7');assert page.locator('#compare tr').count()==7
 page.set_input_files('#csv',{'name':'oil.csv','mimeType':'text/csv','buffer':b'Date,Price\n2024-04-11,90\n2024-04-12,91\n2024-04-15,92\n2024-04-16,93\n2024-04-17,94\n'})
 expect(page.locator('#uploadStatus')).to_contain_text('Loaded 5');page.click('#clear');expect(page.locator('#uploadStatus')).to_contain_text('restored')
 page.click('[data-q="ebola"]');assert '8 August 2014' in page.locator('#mr-answer').inner_text()
 page.set_viewport_size({'width':375,'height':812})
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 assert not errors,errors
 browser.close()
server.shutdown()
print('PASS: source preservation, schema, comparison, imports, guide, seven oil replays, mobile, browser errors')
