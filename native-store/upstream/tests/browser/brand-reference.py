"""Brand regression on an isolated release; never uses customer sessions."""
from pathlib import Path
import json,os,socket,subprocess,time,hashlib,argparse
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];E=R/'artifacts/brand-refresh-20261112';C=R/'artifacts/cpanel-release-brand-reference-20261112-r2';Q=E/'qa-r2';P=Q/'public'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cache-delta',action='store_true');args=parser.parse_args()
    proof=json.loads((E/'release.json').read_bytes());P.mkdir(parents=True,exist_ok=True)
    for f in (C/'public').rglob('*'):
        if not f.is_file():continue
        t=P/f.relative_to(C/'public');t.parent.mkdir(parents=True,exist_ok=True)
        if not t.exists():os.link(f,t)
    (Q/'storage').mkdir(exist_ok=True)
    runtime="<?php return "+"['privateRoot'=>"+repr(str(C/'private').replace('\\','/'))+",'storageRoot'=>"+repr(str(Q/'storage').replace('\\','/'))+",'mediaRoot'=>"+repr(str(R/'artifacts/social-engine-20261112/preview/media').replace('\\','/'))+"];"
    (Q/'nodeno-runtime.php').write_text(runtime,encoding='utf-8')
    with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    log=(E/'browser-php.log').open('w',encoding='utf-8');env={**os.environ,'NODENO_TEST_PUBLIC':str(P),'NODENO_TEST_HTTPS':'loopback-tls-only'}
    server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','extension=gd','-S','127.0.0.1:'+str(port),'-t',str(P),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    report={'passed':False,'releaseHash':proof['releaseHash'],'testOnly':True,'checks':[]}
    if args.cache_delta:
        prior=json.loads((E/'browser-base.json').read_bytes());assert prior['passed']is True and len(prior['checks'])==20
        report['priorVisualAcceptance']={'releaseHash':prior['releaseHash'],'checks':20,'assetAndLayoutBytesUnchanged':True}
        for n in ['public/assets/brand/logo-horizontal.svg','public/assets/brand/social-logo.png','public/admin.css','public/styles.css']:
            if (C/n).exists():assert (C/n).read_bytes()==(R/'artifacts/cpanel-release-brand-reference-20261112'/n).read_bytes()
    try:
        with sync_playwright()as p:
            for engine in ['chromium','webkit']:
                executable=Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
                browser=getattr(p,engine).launch(executable_path=str(executable),headless=True)
                page=browser.new_page(viewport={'width':1440,'height':1000})
                page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1')")
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)[:120]))
                for width in [390,1440]:
                    page.set_viewport_size({'width':width,'height':950})
                    for locale in (['tr','ar']if args.cache_delta else['tr','en','ru','ar']):
                        page.goto(f'http://127.0.0.1:{port}/?lang={locale}',wait_until='networkidle')
                        image=page.locator('.logo img');image.wait_for(state='visible')
                        box=image.bounding_box();assert box['x']>=0 and box['x']+box['width']<=width+1
                        assert image.evaluate('(e)=>e.complete && e.naturalWidth===1600')
                        assert 'brand-20261112-v2' in image.get_attribute('src')
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        assert page.locator('html').get_attribute('dir')==('rtl'if locale=='ar'else'ltr')
                        if locale in ['tr','ar']:page.screenshot(path=str(E/f'{engine}-{width}-{locale}.png'))
                        report['checks'].append({'engine':engine,'locale':locale,'width':width,'logoUnclipped':True,'noOverflow':True})
                    page.goto(f'http://127.0.0.1:{port}/yonetim',wait_until='networkidle')
                    image=page.locator('.auth-card img.brand');image.wait_for(state='visible');assert image.evaluate('(e)=>e.complete && e.naturalWidth===1600')
                    assert 'brand-20261112-v2' in image.get_attribute('src')
                    page.screenshot(path=str(E/f'{engine}-{width}-admin.png'))
                    report['checks'].append({'engine':engine,'page':'admin-login','width':width,'newLogo':True})
                assert not errors,errors
                browser.close()
        report['passed']=True
    finally:
        server.terminate();server.wait(timeout=10);log.close();(E/'browser-local.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(report['checks']),'releaseHash':proof['releaseHash']}))

if __name__=='__main__':main()
