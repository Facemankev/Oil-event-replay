"""Run an unchanged browser script with local-only networking and failure traces."""
import argparse,json,runpy,sys,traceback
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import Browser,BrowserContext,sync_playwright

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--script',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    script=(ROOT/args.script).resolve();output=Path(args.output).resolve()
    if not script.is_relative_to(ROOT) or not script.is_file():raise ValueError('Existing repository script required')
    if not output.is_relative_to((ROOT/'work/ci-browser').resolve()):raise ValueError('Dedicated evidence directory required')
    output.mkdir(parents=True,exist_ok=True)
    contexts=[];blocked=[];capture_errors=[]
    manager_type=type(sync_playwright());original_manager_exit=manager_type.__exit__
    original_new_page=Browser.new_page;original_new=Browser.new_context;original_close=BrowserContext.close;original_browser_close=Browser.close

    def save(context):
        state=next((s for s in contexts if s['context'] is context),None)
        if state is None or state['saved']:return
        state['saved']=True
        stem=f"context-{state['index']:03d}"
        for i,page in enumerate(context.pages):
            try:
                if not page.is_closed():page.screenshot(path=str(output/f'{stem}-page-{i}.png'),full_page=True,timeout=5000)
            except Exception as e:capture_errors.append(type(e).__name__+': screenshot')
        try:context.tracing.stop(path=str(output/f'{stem}.zip'))
        except Exception as e:capture_errors.append(type(e).__name__+': trace')

    def register(context):
        if any(s['context'] is context for s in contexts):return context
        context.tracing.start(screenshots=True,snapshots=True,sources=False)
        contexts.append(dict(context=context,index=len(contexts),saved=False))
        def route(request):
            u=urlsplit(request.request.url)
            if u.scheme in ('data','blob','about') or u.hostname in ('127.0.0.1','localhost','::1'):
                request.continue_()
            else:
                blocked.append(dict(host=u.hostname,path=u.path))
                request.abort('blockedbyclient')
        context.route('**/*',route)
        return context

    def new_context(browser,*a,**kw):
        return register(original_new(browser,*a,**kw))

    def new_page(browser,*a,**kw):
        page=original_new_page(browser,*a,**kw);register(page.context);return page

    def close(context,*a,**kw):
        save(context);return original_close(context,*a,**kw)

    def browser_close(browser,*a,**kw):
        for context in browser.contexts:save(context)
        return original_browser_close(browser,*a,**kw)

    def manager_exit(manager,*a,**kw):
        for state in contexts:
            if not state['saved']:save(state['context'])
        return original_manager_exit(manager,*a,**kw)

    manager_type.__exit__=manager_exit
    Browser.new_context=new_context;Browser.new_page=new_page;BrowserContext.close=close;Browser.close=browser_close
    status=0
    try:
        remaining=args.arguments[1:] if args.arguments[:1]==['--'] else args.arguments
        sys.argv=[str(script),*remaining]
        runpy.run_path(str(script),run_name='__main__')
        if not contexts:raise RuntimeError('Suite created no traced browser contexts; no silent pass')
    except BaseException as e:
        if isinstance(e,SystemExit) and e.code in (0,None):pass
        else:traceback.print_exc();status=1
    finally:
        if status==0 and not contexts:
            print('FAILED: suite created no browser contexts; refusing silent success',file=sys.stderr);status=1
        for state in contexts:
            if not state['saved']:save(state['context'])
        manager_type.__exit__=original_manager_exit
        Browser.new_context=original_new;Browser.new_page=original_new_page;BrowserContext.close=original_close;Browser.close=original_browser_close
        (output/'capture.json').write_text(json.dumps(dict(contexts=len(contexts),
            traces=len(list(output.glob('*.zip'))),capture_errors=capture_errors,
            blocked_external_requests=blocked,network='Loopback fixtures only; source links are inspected, not fetched.'),indent=2)+'\n')
        if status==0:
            # Successful traces are transient; keep compact metadata/logs, not hundreds of MB.
            for pattern in ('*.zip','context-*.png'):
                for p in output.glob(pattern):p.unlink()
    return status

if __name__=='__main__':sys.exit(main())
