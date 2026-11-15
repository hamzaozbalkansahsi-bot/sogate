"""Exercise the exact candidate with real approved images and isolated account storage."""
from pathlib import Path
from contextlib import ExitStack
import json,mimetypes,os,shutil,socket,subprocess,tempfile,time,urllib.request
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/packaging-fix-20261111';proof=json.loads((E/'release.json').read_bytes());source=R/proof['release'];checks=[]
headings={'tr':'Kapaklarla evinizin görünümünü baştan sona yenileyin.','en':"Refresh your home's look with new cabinet fronts.",'ru':'Обновите облик дома с новыми мебельными фасадами.','ar':'جدّد مظهر منزلك بالكامل بواجهات خزائن جديدة.'}
with tempfile.TemporaryDirectory(prefix='nodeno-packaging-browser-')as temporary,ExitStack()as stack:
 root=Path(temporary);release=root/'release';shutil.copytree(source,release,copy_function=os.link);vault=root/'media';vault.mkdir();storage=root/'data';storage.mkdir()
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
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(pw,engine).launch(headless=True,executable_path=str(executable));context=browser.new_context(ignore_https_errors=True,viewport={'width':width,'height':920},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'));localStorage.setItem('nodeno.cart.v1',JSON.stringify([{id:'2395',quantity:2},{id:'2393',quantity:1}]))")
   print(json.dumps({'startCase':locale,'engine':engine}),flush=True)
   def local_assets(route):
    asset=(release/'public'/unquote(urlparse(route.request.url).path).lstrip('/')).resolve()
    if asset.is_relative_to((release/'public/assets').resolve())and asset.is_file():route.fulfill(body=asset.read_bytes(),content_type=mimetypes.guess_type(str(asset))[0]or'application/octet-stream')
    else:route.continue_()
   page.route('**/assets/**',local_assets)
   page.on('response',lambda response:print(json.dumps({'quoteStatus':response.status,'locale':locale}),flush=True)if '/api/payments/quote'in response.url else None)
   page.goto(origin+'/?lang='+locale,wait_until='networkidle');shelf=page.locator('#product-shelf-storageIdeas');expect(shelf.locator('h2')).to_have_text(headings[locale]);shelf.scroll_into_view_if_needed();page.wait_for_function('()=>{const imgs=[...document.querySelectorAll("#product-shelf-storageIdeas img")].filter(i=>{const r=i.getBoundingClientRect();return r.left<innerWidth&&r.right>0&&r.top<innerHeight&&r.bottom>0});return imgs.length>0&&imgs.every(i=>i.complete&&i.naturalWidth>0)}')
   links=shelf.locator('a[href*="product="]').evaluate_all('(links)=>links.map(a=>new URL(a.href).searchParams.get("product"))');assert links and all(byid[key]['productType']in['cabinet-front','cabinet-profile']for key in links);assert 'category=dolap-kapaklari'in shelf.locator('.section-heading a').get_attribute('href');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   assert shelf.locator('.product-stage').first.evaluate('(s)=>{const c=getComputedStyle(s),i=s.querySelector("img");return parseFloat(c.paddingBlockStart)>=16&&parseFloat(c.paddingInlineStart)>=12&&getComputedStyle(i).objectFit==="contain"&&i.getBoundingClientRect().top-s.getBoundingClientRect().top>=15}')
   page.screenshot(path=str(E/('home-fronts-'+engine+'-'+locale+'.png')),full_page=False)
   page.goto(origin+'/?page=register&lang='+locale,wait_until='networkidle');expect(page.locator('#register-form')).to_have_attribute('data-membership-version','2026-11-10.3')
   page.goto(origin+'/legal/returns?lang='+locale,wait_until='networkidle');expect(page.locator('h1')).to_be_visible();assert '2026-11-10.3'in page.locator('main').inner_text()
   page.goto(origin+'/?page=checkout&lang='+locale,wait_until='networkidle');page.locator('[data-action=guest-start]').click();form=page.locator('#guest-checkout-form')
   for name,value in {'name':'Local Test Buyer','email':'local@example.test','phone':'+905551112233','city':'Izmir','district':'Buca','postalCode':'35040','line1':'Local test address 1'}.items():form.locator('[name="'+name+'"]').fill(value)
   form.locator('[name=country]').select_option('TR');form.locator('[type=submit]').click();expect(page.locator('.guest-review')).to_be_visible();expect(page.locator('.payment-totals')).to_be_visible(timeout=25000);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not errors,errors
   checks.append({'engine':engine,'width':width,'locale':locale,'correctHeadingAndFrontProducts':True,'imagesLoaded':True,'membershipVersionPreserved':True,'returnPolicyPreserved':True,'checkoutReviewAndTotals':True,'noOverflow':True,'noRuntimeErrors':True});context.close();browser.close();print(json.dumps({'passedCase':locale,'engine':engine}),flush=True)
 (E/'browser-local.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'checks':checks,'testUsersCreated':0,'testOrdersCreated':0,'realCharges':0},indent=2)+'\n');print(json.dumps({'passed':True,'scenarios':len(checks),'engines':['chromium','webkit'],'realCharges':0}))
