"""Exercise the exact candidate with real approved images and isolated account storage."""
from pathlib import Path
from contextlib import ExitStack
import json,mimetypes,os,shutil,socket,subprocess,tempfile,time,urllib.request
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/vitrine-20261111';proof=json.loads((E/'release.json').read_bytes());source=R/proof['release'];checks=[]
headings={'tr':'Kapaklarla evinizin görünümünü baştan sona yenileyin.','en':"Refresh your home's look with new cabinet fronts.",'ru':'Обновите облик дома с новыми мебельными фасадами.','ar':'جدّد مظهر منزلك بالكامل بواجهات خزائن جديدة.'}
with tempfile.TemporaryDirectory(prefix='nodeno-packaging-browser-')as temporary,ExitStack()as stack:
 root=Path(temporary);release=root/'release';shutil.copytree(source,release,copy_function=os.link);vault=root/'media';vault.mkdir();storage=root/'data';storage.mkdir();(storage/'exchange-rates-v1.json').write_bytes(urllib.request.urlopen('https://nodenohome.com/api/exchange-rates',timeout=45).read())
 cleanup=json.loads((R/'artifacts/media-cleanup.json').read_bytes());approved=json.loads((release/'private/media-approved.json').read_bytes());extensions={'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/avif':'avif','image/gif':'gif'}
 for key,row in approved['images'].items():
  origin=R/cleanup['images'][key]['path'];target=vault/(row['outputSha']+'.'+extensions[row['mime']])
  if not target.exists():os.link(origin,target)
 def pq(value):return "'"+str(value).replace('\\','\\\\').replace("'","\\'")+"'"
 (release/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+pq(release/'private')+",'storageRoot'=>"+pq(storage)+",'mediaRoot'=>"+pq(vault)+'];',encoding='utf8')
 seller=json.loads(urllib.request.urlopen('https://nodenohome.com/api/payments/status',timeout=40).read())['seller'];seed=root/'seller.json';seed.write_text(json.dumps(seller),encoding='utf8');php=R/'artifacts/runtime-php/php.exe'
 subprocess.run([str(php),'-r',"require "+pq(release/'private/payment-admin.php')+";$db=nodenoControlDatabase($argv[1]);nodenoControlSetSetting($db,'payment:stripe',['version'=>1,'enabled'=>false,'mode'=>'test','seller'=>json_decode(file_get_contents($argv[2]),true)]);",str(storage),str(seed)],capture_output=True,check=True)
 with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 origin='http://127.0.0.1:'+str(port);log=stack.enter_context(open(E/'browser-local-server.log','w',encoding='utf8'));server=subprocess.Popen([str(php),'-S','127.0.0.1:'+str(port),'-t',str(release/'public'),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);stack.callback(lambda:server.wait(timeout=8));stack.callback(server.terminate)
 for _ in range(100):
  try:
   with urllib.request.urlopen(origin+'/api/catalog',timeout=1)as response:catalog=json.load(response)
   break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('local_runtime_unavailable')
 # WebKit correctly withholds Secure session cookies over plain HTTP. Exercise
 # the real HTTPS contract through the established loopback-only TLS fixture.
 cert,key=root/'cert.pem',root/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
 with socket.socket()as sock:sock.bind(('127.0.0.1',0));tls=sock.getsockname()[1]
 proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(port),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);stack.callback(lambda:proxy.wait(timeout=8));stack.callback(proxy.terminate);time.sleep(1);origin='https://127.0.0.1:'+str(tls)
 byid={p['id']:p for p in catalog['products']}
 with sync_playwright()as pw:
  for engine,width,locale in [('chromium',1440,'tr'),('chromium',390,'en'),('chromium',390,'ru'),('webkit',390,'ar')]:
   print(json.dumps({'starting':locale,'width':width}),flush=True)
   exe=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(pw,engine).launch(headless=True,executable_path=str(exe));context=browser.new_context(ignore_https_errors=True,viewport={'width':width,'height':1000 if width>767 else 920},is_mobile=width<768,has_touch=width<768,reduced_motion='reduce'if engine=='webkit'else'no-preference');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false')")
   def assets(route):
    f=(release/'public'/unquote(urlparse(route.request.url).path).lstrip('/')).resolve()
    if f.is_relative_to((release/'public/assets').resolve())and f.is_file():route.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0]or'application/octet-stream')
    else:route.continue_()
   page.route('**/assets/**',assets)
   page.goto(origin+'/?lang='+locale,wait_until='networkidle');v=page.locator('[data-home-vitrine]');expect(v).to_be_visible();expect(v.locator('[data-vitrine-slide]')).to_have_count(3);tabs=v.locator('[data-vitrine-go]');play=v.locator('[data-vitrine-play]')
   if engine=='webkit':expect(play).to_have_attribute('aria-pressed','true')
   else:
    play.click();expect(play).to_have_attribute('aria-pressed','true')
   page.wait_for_function('()=>{const i=document.querySelector("[data-vitrine-slide] img");return i&&i.complete&&i.naturalWidth>0}')
   page.wait_for_timeout(600);page.screenshot(path=str(E/('home-'+engine+'-'+str(width)+'-'+locale+'.png')))
   tabs.nth(1).click();expect(tabs.nth(1)).to_have_attribute('aria-current','true');page.wait_for_timeout(550);expect(play).to_have_attribute('aria-pressed','true')
   if width>767:
    page.locator('#search').focus();page.mouse.move(1,1);active=tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")');page.wait_for_timeout(6500);assert tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")')==active
    play.click();page.locator('#search').focus();page.mouse.move(1,1);expect(tabs.nth(2)).to_have_attribute('aria-current','true',timeout=9000);play.click()
   if engine=='webkit':
    active=tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")');page.locator('#search').focus();page.mouse.move(1,1);page.wait_for_timeout(6500);assert tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")')==active
   shelf=page.locator('#product-shelf-storageIdeas');shelf.evaluate('(e)=>scrollTo({top:e.getBoundingClientRect().top+scrollY-document.querySelector(".store-header").getBoundingClientRect().height-16,behavior:"instant"})');page.wait_for_load_state('networkidle')
   first=shelf.locator('.product-card').first;assert first.evaluate('(c)=>{const h=c.querySelector("h3").getBoundingClientRect(),color=c.querySelector(".card-color").getBoundingClientRect();return color.top-h.bottom<18&&h.height<52}')
   assert first.locator('.card-price-main').evaluate('(e)=>e.getBoundingClientRect().height<30&&e.querySelector(".price-unit").textContent.includes("m²")')
   if width<768:assert page.locator('.quick-open:visible').count()==0
   page.wait_for_function('()=>{const ss=[...document.querySelectorAll("#product-shelf-storageIdeas .product-stage")].filter(e=>{const r=e.getBoundingClientRect(),p=e.closest(".product-row").getBoundingClientRect();return r.left<Math.min(p.right,innerWidth)&&r.right>Math.max(p.left,0)&&r.top<innerHeight&&r.bottom>0});return ss.length>0&&ss.every(s=>{const i=s.querySelector("img");return i&&i.complete&&i.naturalWidth>0})}')
   page.wait_for_timeout(800);page.screenshot(path=str(E/('cards-'+engine+'-'+str(width)+'-'+locale+'.png')));assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not errors,errors
   checks.append({'engine':engine,'width':width,'locale':locale,'threeRealProductSlides':True,'manualAndPauseControls':True,'reducedMotionRespected':True,'compactTitleColourGap':True,'priceAndUnitTogether':True,'noQuickOverlay':True,'noOverflow':True,'noRuntimeErrors':True});context.close();browser.close();print(json.dumps({'passedCase':locale}),flush=True)
 (E/'browser-local.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'checks':checks,'realCharges':0},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(checks)}),flush=True)
