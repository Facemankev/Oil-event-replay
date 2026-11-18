"""Intentional test-only failure: prove screenshot/trace capture, never market data."""
import argparse
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--browser',required=True);a=p.parse_args()
with sync_playwright() as p:
    browser=getattr(p,a.browser).launch(headless=True,**({'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if a.browser=='chromium' else {}))
    context=browser.new_context();page=context.new_page()
    page.set_content('<title>Controlled capture self-test</title><h1>Intentional fixture failure</h1>')
    # Deliberately do not close: exercise evidence capture before context-manager shutdown.
    raise AssertionError('Controlled fixture failure proves evidence capture')
