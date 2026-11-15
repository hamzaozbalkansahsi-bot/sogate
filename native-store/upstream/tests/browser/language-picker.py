from pathlib import Path
import argparse,json,os,tempfile,shutil,subprocess,socket
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/language-picker';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--red',action='store_true');args=parser.parse_args()
def port():
 s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close();return p
server=proxy=log=None;origin='https://nodenohome.com'
if not args.live:
 temp=Path(tempfile.mkdtemp(prefix='nodeno-language-',dir='D:/NODENO_QA_TEMP'));release=temp/'release';shutil.copytree(ROOT/'artifacts/cpanel-release',release);storage=temp/'data';storage.mkdir();q=lambda p:"'"+p.as_posix().replace("'","\\'")+"'";(release/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(release/'private')+",'storageRoot'=>"+q(storage)+",'mediaRoot'=>"+q(ROOT/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf-8');upstream=port();tls=port();origin='https://127.0.0.1:'+str(tls);log=open(OUT/'server.log','w',encoding='utf-8');env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'}
 server=subprocess.Popen([str(ROOT/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(release/'public'),str(ROOT/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);cert=temp/'cert.pem';key=temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
 proxy=subprocess.Popen(['node',str(ROOT/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
checks=[]
try:
 with sync_playwright() as p:
  for engine in (['webkit'] if args.red else ['chromium','webkit']):
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe';browser=getattr(p,engine).launch(executable_path=str(executable));context=browser.new_context(ignore_https_errors=not args.live,is_mobile=True,has_touch=True,device_scale_factor=2,viewport={'width':390,'height':844});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(e.stack))
   try:
    if args.live:
     health=context.request.get(origin+'/api/health');assert health.ok;assert health.json()['releaseHash']==json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text())['releaseHash']
    page.goto(origin+'/?lang=tr',wait_until='networkidle');page.evaluate('document.fonts.ready');page.screenshot(path=str(OUT/(('live-' if args.live else '')+engine+'-before-check.png')))
    for route in (['home'] if args.red else ['home','categories']):
     if route=='categories':page.goto(origin+'/?page=categories&lang=tr',wait_until='networkidle')
     for width in ([390] if args.red else [320,390,430,768,1024,1440]):
      page.set_viewport_size({'width':width,'height':844})
      for lang in (['tr'] if args.red else ['tr','en','ru','ar']):
       page.locator('#language').select_option(lang);expect(page.locator('html')).to_have_attribute('lang',lang);page.evaluate('document.fonts.ready')
       metrics=page.locator('#language').evaluate('''el=>{const s=getComputedStyle(el),c=document.createElement('canvas').getContext('2d');c.font=s.fontWeight+' '+s.fontSize+' '+s.fontFamily;const text=el.selectedOptions[0].textContent;const labelWidth=c.measureText(text).width;const nativeSpace=s.appearance==='none'?0:32;const available=el.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)-nativeSpace;return {text,labelWidth,available,width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,appearance:s.appearance};}''')
       assert metrics['available']>=metrics['labelWidth']+4,(engine,route,width,lang,metrics)
       assert metrics['height']>=44;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(engine,route,width,lang,'overflow')
       if route=='home':
        boxes=page.locator('.header-main').evaluate('''el=>{const a=el.querySelector('.logo').getBoundingClientRect(),b=el.querySelector('.header-actions').getBoundingClientRect();return {clear:document.dir==='rtl'?b.right<=a.left:a.right<=b.left};}''');assert boxes['clear'],(engine,width,lang,'header collision')
       if width==390 and route=='home' and lang in ['tr','ar']:page.screenshot(path=str(OUT/(('live-' if args.live else '')+engine+'-'+lang+'.png')),clip={'x':0,'y':0,'width':390,'height':170})
       checks.append({'engine':engine,'route':route,'width':width,'locale':lang,**metrics})
    assert not errors,errors
   finally:browser.close()
 result={'passed':True,'live':args.live,'releaseHash':json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text())['releaseHash'],'checks':checks};(OUT/('live-report.json' if args.live else 'report.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':True,'live':args.live,'scenarios':len(checks),'releaseHash':result['releaseHash']}))
finally:
 for process in [proxy,server]:
  if process:process.terminate();process.wait(timeout=10)
 if log:log.close()
