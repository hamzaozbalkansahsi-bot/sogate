"""Regression checks for mobile category images and consent dialog geometry."""
from pathlib import Path
import os,json,subprocess,socket,time,sys
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/mobile-layout-20261113'
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def main():
 proof=json.loads((E/'release.json').read_bytes());baseline='--baseline'in sys.argv;C=R/proof['base'if baseline else'release'];Q=E/('baseline'if baseline else'preview');P=Q/'public';P.mkdir(parents=True,exist_ok=True)
 for f in(C/'public').rglob('*'):
  if f.is_file():
   target=P/f.relative_to(C/'public');target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():os.link(f,target)
 q=lambda p:"'"+p.as_posix().replace("'","\\'")+"'";(Q/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(C/'private')+",'storageRoot'=>"+q(Q/'storage')+",'mediaRoot'=>"+q(R/'artifacts/social-engine-20261112/preview/media')+"];",encoding='utf-8')
 cert=Q/'cert.pem';key=Q/'key.pem'
 if not cert.exists():subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
 up,tls=port(),port();origin='https://127.0.0.1:'+str(tls);log=(Q/'php.log').open('w',encoding='utf-8');env={**os.environ,'NODENO_TEST_PUBLIC':str(P),'NODENO_TEST_HTTPS':'loopback-tls-only','NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(up),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)};server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-S','127.0.0.1:'+str(up),'-t',str(P),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 report={'passed':False,'baseline':baseline,'releaseHash':proof['baseReleaseHash'if baseline else'releaseHash'],'checks':[]}
 try:
  with sync_playwright()as pw:
   for engine in (['chromium']if baseline else['chromium','webkit']):
    exe=Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe';browser=getattr(pw,engine).launch(executable_path=str(exe),headless=True)
    context=browser.new_context(ignore_https_errors=True,viewport={'width':390,'height':844},has_touch=True);context.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false');");page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for width,lang in ([(390,'tr')]if baseline else[(320,'tr'),(390,'tr'),(430,'en'),(390,'ru'),(390,'ar'),(1440,'tr')]):
     page.set_viewport_size({'width':width,'height':844 if width<760 else 1000});page.goto(origin+'/?lang='+lang+'&page=categories',wait_until='networkidle');expect(page.locator('[data-category-tile="ahsap-mobilya-malzemeleri"]')).to_be_visible();tile=page.locator('[data-category-tile="ahsap-mobilya-malzemeleri"]');tile.scroll_into_view_if_needed();page.wait_for_timeout(250)
     if not baseline:
      assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(engine,width,lang,'page overflow');assert '735f57be' in tile.locator('img').get_attribute('src');assert tile.locator('img').evaluate("i=>getComputedStyle(i).objectFit")=='contain'
      assert page.locator('.category-tile-photo img').evaluate_all("xs=>xs.every(i=>getComputedStyle(i).objectFit==='contain')")
      if lang=='tr':expect(tile).to_contain_text('Ahşap mobilya ve yardımcı ürünler')
     page.screenshot(path=str(E/(engine+'-'+str(width)+'-'+lang+'-categories'+('-before'if baseline else'')+'.png')))
     page.locator('#insights-settings').click();dialog=page.locator('#insights-preferences');expect(dialog).to_be_visible();geo=dialog.evaluate("d=>{const a=d.querySelector('a').getBoundingClientRect(),b=d.querySelector('.insights-actions').getBoundingClientRect(),r=d.getBoundingClientRect();return {gap:b.top-a.bottom,left:r.left,right:r.right,top:r.top,bottom:r.bottom,overflow:d.scrollWidth>d.clientWidth+1}}")
     if baseline:assert geo['gap']<8,geo
     else:
      assert geo['gap']>=12 and geo['left']>=0 and geo['right']<=width+1 and not geo['overflow'],(engine,width,lang,geo)
      assert dialog.locator('.insights-actions button').evaluate_all("xs=>xs.every(b=>b.getBoundingClientRect().height>=44)")
      expect(dialog.get_by_role('button').first).to_be_focused();page.screenshot(path=str(E/(engine+'-'+str(width)+'-'+lang+'-privacy.png')));dialog.locator('.insights-close').click();expect(dialog).not_to_be_visible();page.locator('#insights-settings').click();page.keyboard.press('Escape');expect(dialog).not_to_be_visible()
     if baseline:page.screenshot(path=str(E/'privacy-before.png'));page.keyboard.press('Escape')
     report['checks'].append({'engine':engine,'width':width,'locale':lang,'policyActionGap':geo['gap'],'noOverlap':geo['gap']>=12})
    assert not errors,errors;browser.close()
  report['passed']=True
 finally:
  proxy.terminate();proxy.wait(timeout=10);server.terminate();server.wait(timeout=10);log.close();(E/('baseline-check.json'if baseline else'browser-local.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))
if __name__=='__main__':main()

