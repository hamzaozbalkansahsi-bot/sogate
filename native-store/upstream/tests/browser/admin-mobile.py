"""Mobile management acceptance against an isolated PHP release, including WebKit."""
from pathlib import Path
import argparse,base64,hashlib,hmac,json,os,socket,struct,subprocess,time
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/admin-mobile-20261112';E.mkdir(exist_ok=True)
W=R/'artifacts/social-engine-20261112/preview';P=W/'public'
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def otp():
 h=hmac.new(base64.b32decode('JBSWY3DPEHPK3PXP'),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=h[-1]&15
 return str((struct.unpack('>I',h[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
def main():
 a=argparse.ArgumentParser();a.add_argument('--baseline',action='store_true');a.add_argument('--engine',choices=['chromium','webkit','both'],default='both');args=a.parse_args()
 cert=E/'cert.pem';key=E/'key.pem'
 if not cert.exists():subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 up=port();tls=port();origin='https://127.0.0.1:'+str(tls);env={**os.environ,'NODENO_TEST_PUBLIC':str(P),'NODENO_TEST_HTTPS':'loopback-tls-only','NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(up),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)}
 log=(E/'php.log').open('w',encoding='utf8');server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','extension=gd','-S','127.0.0.1:'+str(up),'-t',str(P),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 report={'passed':False,'testOnly':True,'engines':[]}
 try:
  with sync_playwright()as p:
   for engine in (['chromium','webkit']if args.engine=='both'else[args.engine]):
    # Only the synthetic owner in this isolated preview is provisioned here.
    php="require $argv[1].'/control-auth.php';$db=nodenoControlDatabase($argv[2]);$now=time();$id='mobile-qa-'.$argv[3];$db->prepare('INSERT OR REPLACE INTO control_users(id,email,role,password_hash,totp_secret,last_totp_counter,recovery_json,created_at,updated_at) VALUES(?,?,?,?,?,-1,?,?,?)')->execute([$id,$id.'@example.test','owner',password_hash('Mobile-QA-only-password-2026',PASSWORD_BCRYPT),nodenoControlEncrypt($argv[2],'JBSWY3DPEHPK3PXP',$id),'[]',$now,$now]);"
    runtime=(W/'nodeno-runtime.php').read_text(encoding='utf8');private=runtime.split("'privateRoot'=>'",1)[1].split("'",1)[0]
    subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',php,private,str(W/'storage'),engine],check=True,capture_output=True)
    executable=Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
    browser=getattr(p,engine).launch(executable_path=str(executable),headless=True)
    try:
     context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,ignore_https_errors=True);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(origin+'/yonetim',wait_until='networkidle');expect(page.get_by_role('textbox',name='E-posta',exact=True)).to_be_visible()
     fields=page.locator('input').evaluate_all('(els)=>els.map(e=>({type:e.type,font:parseFloat(getComputedStyle(e).fontSize)}))')
     if args.baseline:
      report['engines'].append({'engine':engine,'loginFields':fields});assert all(x['font']>=16 for x in fields),'Phone fields below 16px can trigger Safari focus zoom: '+str(fields)
     page.get_by_role('textbox',name='E-posta',exact=True).fill('mobile-qa-'+engine+'@example.test');page.get_by_role('textbox',name='Parola',exact=True).fill('Mobile-QA-only-password-2026');page.get_by_role('button',name='Devam et',exact=True).click();expect(page.get_by_role('textbox',name='Doğrulama veya kurtarma kodu',exact=True)).to_be_visible();assert float(page.get_by_role('textbox',name='Doğrulama veya kurtarma kodu',exact=True).evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)'))>=16
     page.get_by_role('textbox',name='Doğrulama veya kurtarma kodu',exact=True).fill(otp());page.get_by_role('button',name='Giriş yap',exact=True).click();expect(page.locator('.topbar')).to_be_visible();expect(page.locator('#main h1')).to_be_visible();assert page.evaluate('scrollX===0&&scrollY===0'),'Login must start at page top'
     results=[]
     routes=['dashboard','products','orders','suppliers','campaigns','appearance','seo','business','shipping','shipments','invoices','support','wholesaleRequests','analytics','integrations','team','system','social','guide']
     for width,height in [(320,740),(390,844),(844,390),(768,1024),(1440,980)]:
      page.set_viewport_size({'width':width,'height':height})
      for route in (routes if width==390 else ['dashboard','products','social']):
       report['last']={'engine':engine,'route':route,'width':width};page.goto(origin+'/yonetim#'+route,wait_until='networkidle');page.wait_for_function("route=>document.querySelector('.nav-link[aria-current=page]')?.hash==='#'+route&&document.querySelector('#main h1')",arg=route);expect(page.locator('#main h1')).to_be_visible();assert 'Kayıtlar alınamadı'not in page.locator('#main').inner_text(),route
       page.wait_for_load_state('networkidle');layout=page.evaluate('({width:innerWidth,content:document.documentElement.scrollWidth,heading:document.querySelector("#main h1").getBoundingClientRect().toJSON()})');assert layout['content']<=width+1,(engine,route,width,layout)
       assert layout['heading']['x']>=0 and layout['heading']['right']<=width+1,(engine,route,'clipped heading',layout)
       results.append({'route':route,'width':width,'noOverflow':True})
      if width in [390,1440]:
       page.goto(origin+'/yonetim#dashboard',wait_until='networkidle');page.wait_for_function("()=>document.querySelector('.nav-link[aria-current=page]')?.hash==='#dashboard'&&document.querySelector('#main h1')");page.wait_for_load_state('networkidle');expect(page.locator('#main h1')).to_be_visible();page.screenshot(path=str(E/(engine+'-'+str(width)+'-dashboard.png')))
     page.set_viewport_size({'width':390,'height':844});page.goto(origin+'/yonetim#dashboard',wait_until='networkidle');page.locator('[data-menu]').click();expect(page.locator('.sidebar.open')).to_be_visible();assert page.locator('body').evaluate('(e)=>getComputedStyle(e).overflow')=='hidden';page.locator('.sidebar a[href="#products"]').click();expect(page.locator('.sidebar.open')).to_have_count(0);expect(page.locator('#main h1')).to_contain_text('Ürünler');page.locator('[data-edit]').first.click();expect(page.locator('#editor')).to_be_visible();page.screenshot(path=str(E/(engine+'-mobile-editor.png')));dialog=page.locator('#editor').bounding_box();assert dialog['x']>=0 and dialog['x']+dialog['width']<=390+1
     fonts=page.locator('#editor input:not([type=checkbox]),#editor select,#editor textarea').evaluate_all('(els)=>els.map(e=>parseFloat(getComputedStyle(e).fontSize))');assert all(x>=16 for x in fonts),(engine,fonts);page.locator('#editor [data-close]').first.click();expect(page.locator('#editor')).not_to_be_visible()
     page.evaluate('window.scrollTo(0,400)');page.locator('[data-menu]').click();page.locator('.sidebar a[href="#dashboard"]').click();expect(page.locator('#main h1')).to_contain_text('genel görünümü');assert page.evaluate('scrollX===0&&scrollY===0');assert not errors,errors
     report['engines'].append({'engine':engine,'loginFields':fields,'checks':results,'mobileMenu':True,'editor':True,'routeScrollReset':True,'javascriptErrors':errors})
    finally:browser.close()
  report['passed']=True
 finally:
  proxy.terminate();proxy.wait(timeout=10);server.terminate();server.wait(timeout=10);log.close();(E/('baseline.json'if args.baseline else'browser.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
