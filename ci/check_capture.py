"""Require a failed child, screenshot and readable trace from an intentional fixture."""
import argparse,json,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--browser',choices=['chromium','webkit'],required=True);a=p.parse_args()
    output=ROOT/'work/ci-browser'/a.browser/'controlled-capture';output.mkdir(parents=True,exist_ok=True)
    cmd=[sys.executable,'-m','ci.browser_worker','--script','ci/fixtures/controlled_failure.py','--output',str(output),'--','--browser',a.browser]
    with (output/'test.log').open('w') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=60)
    if r.returncode!=1:raise RuntimeError('Expected failed child status 1')
    captures=json.loads((output/'capture.json').read_text())
    if not list(output.glob('*.png')) or not captures['traces']:raise RuntimeError('Failure screenshot/trace missing')
    for trace in output.glob('*.zip'):
        with zipfile.ZipFile(trace) as archive:
            if not any(n.endswith('.trace') for n in archive.namelist()):raise RuntimeError('Unreadable Playwright trace')
    print('PASS: intentional failure retains screenshots, logs and valid trace; '+a.browser)

if __name__=='__main__':main()
