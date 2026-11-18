"""No-skip two-engine suite runner; failures retain screenshots/traces and fail CI."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'ci/browser_suites.json'


def suites(engine):
    data=json.loads(CATALOG.read_text())
    if engine not in ('chromium','webkit'):raise ValueError('Supported browser required')
    for folder in data['required_pages']:
        if not (ROOT/folder/'index.html').is_file():raise ValueError('Required page missing: '+folder)
    selected=[dict(s) for s in data['suites'] if engine in s['engines']]
    for item in data['optional_frontends']:
        if (ROOT/item['directory']).exists():
            if not (ROOT/item['suite']).is_file():raise ValueError('Frontend present without required two-engine suite: '+item['directory'])
            selected.append(dict(name=item['directory'],file=item['suite'],engines=['chromium','webkit']))
    for s in selected:
        if not (ROOT/s['file']).is_file():raise ValueError('Required browser script missing: '+s['file'])
    return selected


def run_suite(engine,suite,output,timeout=300,client=subprocess.run):
    target=output/suite['name'];target.mkdir(parents=True,exist_ok=True)
    extra=['--browser',engine] if len(suite['engines'])>1 else []
    command=[sys.executable,'-m','ci.browser_worker','--script',suite['file'],'--output',str(target),'--',*extra]
    started=time.monotonic()
    with (target/'test.log').open('w') as log:
        try:
            p=client(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
            code=p.returncode
        except subprocess.TimeoutExpired:
            log.write('\nFAILED: suite exceeded the explicit timeout; no pass or skip.\n');code=124
    return dict(suite=suite['name'],script=suite['file'],engine=engine,exit_code=code,
        status='passed' if code==0 else 'failed',seconds=round(time.monotonic()-started,2),
        reproduce=f'python3 -m ci.run_browser --browser {engine} --only {suite["name"]}',
        log=str(target.relative_to(ROOT)/'test.log'))


def summary(records):
    lines=['# Market Ripple browser checks','',
           'Fixture-only Chromium/WebKit checks; iPhone/iPad are emulated. Physical Safari is not tested.','',
           '| Suite | Engine | Result | Reproduce |','| --- | --- | --- | --- |']
    for r in records:lines.append(f'| {r["suite"]} | {r["engine"]} | {r["status"]} ({r["exit_code"]}) | `{r["reproduce"]}` |')
    lines+=['','Failed suites retain logs, final screenshots and Playwright traces in the artifact. No external market/news API is used.']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--browser',required=True,choices=['chromium','webkit']);p.add_argument('--only')
    args=p.parse_args();selected=suites(args.browser)
    if args.only:
        selected=[s for s in selected if s['name']==args.only]
        if not selected:p.error('Unknown suite; refusing an empty pass')
    output=ROOT/'work/ci-browser'/args.browser;output.mkdir(parents=True,exist_ok=True)
    records=[]
    for suite in selected:
        r=run_suite(args.browser,suite,output);records.append(r)
        (output/'results.json').write_text(json.dumps(records,indent=2)+'\n')
        (output/'summary.md').write_text(summary(records))
        print(f'{r["status"].upper()}: {r["suite"]} / {args.browser}',flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary(records))
    return 1 if any(r['exit_code']!=0 for r in records) else 0

if __name__=='__main__':sys.exit(main())
