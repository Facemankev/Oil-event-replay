"""Reproduce all retained offline contracts before the required status can pass."""
import glob,json,os,shlex,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def commands():
    return [
      [sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],
      ['node','--test',*sorted(glob.glob('tests/*.cjs')+glob.glob('tests/*.mjs'))],
      [sys.executable,'-m','historical','--db','work/ci-offline/prices.sqlite','backfill'],
      [sys.executable,'-m','historical','--db','work/ci-offline/prices.sqlite','update'],
      *[[sys.executable,'-m','world_events','--db','work/ci-offline/events.sqlite','import'] for _ in range(2)],
      [sys.executable,'-m','matching.validate_prices','--db','work/ci-offline/prices.sqlite','--output','work/ci-offline/price-audit.json'],
      [sys.executable,'-m','matching.build','--prices-db','work/ci-offline/prices.sqlite','--events-db','work/ci-offline/events.sqlite','--output','work/ci-offline/catalog.json'],
      ['node','matching/demo.mjs','--check'],[sys.executable,'-m','app.data_status','--check'],
      [sys.executable,'-m','ripple.build','--check'],
      *[['node',folder+'/evaluate.mjs','--check'] for folder in ('intelligence','verification','analogues','equities')],
      [sys.executable,'-m','news_pilot.demo','--check','--output','work/ci-offline/news-demo.json'],
      *[[sys.executable,'-m','event_history','--db','work/ci-offline/library.sqlite','import'] for _ in range(2)],
      [sys.executable,'-m','event_history','--db','work/ci-offline/library.sqlite','evaluate','--check','--output','work/ci-offline/history.json'],
      *[[sys.executable,'-m','free_pilot','import'] for _ in range(2)],
      [sys.executable,'-m','free_pilot','demo','--check'],
      [sys.executable,'-m','simulations','--check'],[sys.executable,'-m','learning','--check','--journal','work/ci-offline/journal'],
      ['bash','.claude/hooks/guard.sh','scan']]


def main():
    output=ROOT/'work/ci-offline';output.mkdir(parents=True,exist_ok=True);records=[]
    for i,cmd in enumerate(commands()):
        with (output/f'{i:02d}.log').open('w') as f:
            try:code=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=240).returncode
            except subprocess.TimeoutExpired:code=124;f.write('\nExplicit offline check timeout\n')
        records.append(dict(command=shlex.join(cmd),exit_code=code,log=f'{i:02d}.log'))
        (output/'results.json').write_text(json.dumps(records,indent=2)+'\n')
        if code:
            message=f'Failed offline check: `{shlex.join(cmd)}`. Exit {code}; artifact log `{i:02d}.log`.'
            print(message)
            if os.environ.get('GITHUB_STEP_SUMMARY'):
                with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(message+'\n')
            return 1
        print('PASS: '+shlex.join(cmd),flush=True)
    return 0

if __name__=='__main__':sys.exit(main())
