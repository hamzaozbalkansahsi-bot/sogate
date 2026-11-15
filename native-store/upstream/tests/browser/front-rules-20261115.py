"""Isolated candidate and optional live acceptance for the corrected front photo."""
from pathlib import Path
import hashlib,json,os,socket,subprocess,time
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];E=R/'artifacts/front-image-integrity-20261115';C=R/'artifacts/cpanel-release-front-rules-20261115-r1';Q=E/'qa';P=Q/'public'

def main():
 proof=json.loads((E/'release.json').read_bytes());data=json.loads((C/'private/cabinet-fronts.json').read_bytes());product=next(x for x in data['products']if x['id']=='front-dc1a5394d3e7dc80');digest=product['assetHashes'][0];expected=(C/'public'/data['assets'][digest]['path'].lstrip('/')).read_bytes();version=hashlib.sha256((C/'private/cabinet-fronts.json').read_bytes()).hexdigest()
 P.mkdir(parents=True,exist_ok=True)
 for f in (C/'public').rglob('*'):
  if f.is_file():
   t=P/f.relative_to(C/'public');t.parent.mkdir(parents=True,exist_ok=True)
   if not t.exists():os.link(f,t)
 (Q/'storage').mkdir(exist_ok=True)
 runtime="<?php return ['privateRoot'=>"+repr((C/'private').as_posix())+",'storageRoot'=>"+repr((Q/'storage').as_posix())+",'mediaRoot'=>"+repr((R/'artifacts/social-engine-20261112/preview/media').as_posix())+"];"
 (Q/'nodeno-runtime.php').write_text(runtime,encoding='utf8')
 with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 log=(E/'browser-php.log').open('w');env={**os.environ,'NODENO_TEST_PUBLIC':str(P),'NODENO_TEST_HTTPS':'loopback-tls-only'}
 server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','extension=gd','-S',f'127.0.0.1:{port}','-t',str(P),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 report={'passed':False,'releaseHash':proof['releaseHash'],'testOnly':True,'checks':[]}
 try:
  with sync_playwright()as pw:
   for engine in (['chromium']if os.environ.get('FRONT_RULE_VISUAL_ONLY')else['chromium','webkit']):
    exe=Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
    browser=getattr(pw,engine).launch(executable_path=str(exe),headless=True);page=browser.new_page()
    page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false');")
    for width in [390,1440]:
     page.set_viewport_size({'width':width,'height':950})
     for lang in (['tr']if os.environ.get('FRONT_RULE_VISUAL_ONLY')else['tr','ar']):
      page.goto(f'http://127.0.0.1:{port}/?lang={lang}&product={product["id"]}',wait_until='networkidle')
      photo=page.locator('.gallery-main .product-image').first;photo.wait_for(state='visible')
      assert photo.evaluate('(e)=>e.complete&&e.naturalWidth===772&&e.naturalHeight===1381')
      assert version in photo.get_attribute('src');response=page.request.get(photo.evaluate('(e)=>e.currentSrc'));assert response.ok and response.body()==expected
      assert response.headers.get('x-content-sha256')==digest
      assert photo.evaluate('(e)=>getComputedStyle(e).objectFit')=='contain'
      assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
      page.screenshot(path=str(E/f'{engine}-{width}-{lang}.png'))
      report['checks'].append({'engine':engine,'width':width,'locale':lang,'photoSha256':digest,'naturalDimensions':[772,1381],'fullProductContained':True,'newCacheVersion':True,'noOverflow':True})
    browser.close()
  report['passed']=True
 finally:server.terminate();server.wait(timeout=10);log.close();(E/('browser-visual.json'if os.environ.get('FRONT_RULE_VISUAL_ONLY')else'browser-local.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':report['passed'],'checks':len(report['checks'])}))

if __name__=='__main__':main()
