"""Exercise the exact candidate with real approved images and isolated account storage."""
from pathlib import Path
from contextlib import ExitStack
import json,mimetypes,os,re,shutil,socket,subprocess,tempfile,time,urllib.request
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright,expect
from supplier_details_recovery import verify_recovery
R=Path(__file__).resolve().parents[2];E=R/'artifacts/target-locales-20261111';proof=json.loads(Path(os.environ.get('NODENO_NATIVE_BROWSER_PROOF',str(E/'release.json'))).read_bytes());source=R/proof['release'];checks=[]
if os.environ.get('NODENO_NATIVE_BROWSER_PROOF'):E=Path(os.environ['NODENO_NATIVE_BROWSER_PROOF']).resolve().parent
moduleVersion=re.search(r"locale-runtime\.js\?v=([^']+)",(source/'public/app.js').read_text(encoding='utf8'))[1]
if proof.get('testOnly'):E=E/'draft-php';E.mkdir(exist_ok=True)
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

 native=['de','az','kk','tk','uz','ky','fa'];defaults={'tr':'TRY','en':'USD','ru':'RUB','ar':'SAR','de':'EUR','az':'AZN','kk':'KZT','tk':'USD','uz':'USD','ky':'USD','fa':'USD'}
 countryMatrix=[('TR','tr','TRY'),('DE','de','EUR'),('GB','en','GBP'),('AZ','az','AZN'),('KZ','kk','KZT'),('TM','tk','USD'),('UZ','uz','USD'),('KG','ky','USD'),('IR','fa','USD'),('IQ','ar','USD'),('SY','ar','USD')]
 detailIndex=json.loads((release/'private/supplier-details.json').read_bytes());detailBlob=(release/'private/supplier-details.bin').read_bytes()
 supplier=byid[proof['supplierProduct']]if proof.get('testOnly')else next(p for p in catalog['products']if p.get('productType')=='supplier-item'and p['code'].startswith('ND-ALT'))
 entry=detailIndex.get('entries',detailIndex.get('products',detailIndex))[supplier['id']];supplierText=json.loads(detailBlob[entry['offset']:entry['offset']+entry['bytes']])['description']
 def texts(locale):
  if locale not in native:return {}
  return {k:v for suffix in ['', '.catalogue']for k,v in json.loads((release/('public/locales/'+locale+suffix+'.json')).read_bytes())['translations'].items()}
 def localized(value,locale,translation):
  if locale in value:return value[locale]
  if all(value.get(l)==value.get('en')for l in ['tr','ru','ar']):return value.get('en','')
  return translation[value['en']]
 with sync_playwright()as pw:
  cases=[('chromium',1440,'tr'),('chromium',390,'tr'),('chromium',390,'en'),('chromium',390,'ru'),('webkit',390,'ar')]+[('chromium',390,l)for l in native]+[('webkit',320,'fa'),('chromium',1440,'de')]
  if os.environ.get('NODENO_NATIVE_CASE_LOCALE'):
   assert proof.get('testOnly') is True,'partial cases are never production acceptance'
   cases=[case for case in cases if case[2]==os.environ['NODENO_NATIVE_CASE_LOCALE']]
  for engine,width,locale in cases:
   print(json.dumps({'starting':locale,'engine':engine,'width':width}),flush=True)
   exe=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(pw,engine).launch(headless=True,executable_path=str(exe));context=browser.new_context(ignore_https_errors=True,viewport={'width':width,'height':950},is_mobile=width<768,has_touch=width<768,reduced_motion='reduce'if engine=='webkit'else'no-preference');page=context.new_page();page.set_default_timeout(45000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("if(sessionStorage.getItem('qa-show-map')!=='1')localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.currency.v1',JSON.stringify('KZT'));localStorage.setItem('nodeno.analytics.consent.v1','false')")
   def assets(route):
    f=(release/'public'/unquote(urlparse(route.request.url).path).lstrip('/')).resolve()
    if f.is_relative_to((release/'public/assets').resolve())and f.is_file():route.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0]or'application/octet-stream')
    else:route.continue_()
   page.route('**/assets/**',assets)
   if proof.get('testOnly'):
    page.on('console',lambda message:errors.append(message.text)if message.type=='error'and message.text.startswith('supplier_details_debug')else None)
    debugApp=(release/'public/app.js').read_text(encoding='utf8').replace('.catch(()=>{supplierDetailRequests.delete(p.id);});',".catch(error=>{console.error('supplier_details_debug',error.message,error.translationSource);supplierDetailRequests.delete(p.id);});")
    page.route('**/app.js*',lambda route:route.fulfill(body=debugApp,content_type='text/javascript'))
   def navigate(url):
    try:return page.goto(url,wait_until='networkidle')
    except Exception as error:
     # Windows Chromium can exhaust retries when a new navigation races the
     # single-worker PHP fixture's closing image connections. Retry only this
     # GET transport failure once; HTTP errors and content assertions still fail.
     if 'net::ERR_TOO_MANY_RETRIES'not in str(error):raise
     page.wait_for_timeout(700);return page.goto(url,wait_until='networkidle')
   navigate(origin+'/?lang='+locale);expect(page.locator('#language')).to_have_value(locale);expect(page.locator('#display-currency')).to_have_value(defaults[locale],timeout=20000);expect(page.locator('html')).to_have_attribute('dir','rtl'if locale in ['ar','fa']else'ltr')
   expectedCurrency=page.evaluate("version=>import('/currency.js?v='+version).then(m=>m.currencyState().currency)",moduleVersion);assert expectedCurrency==defaults[locale]
   vitrine=page.locator('[data-home-vitrine]');expect(vitrine).to_be_visible();expect(vitrine.locator('[data-vitrine-slide]')).to_have_count(3);vitrine.locator('[data-vitrine-go]').nth(1).click();expect(vitrine.locator('[data-vitrine-go]').nth(1)).to_have_attribute('aria-current','true');expect(vitrine.locator('[data-vitrine-play]')).to_have_attribute('aria-pressed','true')
   def wait_visible_photos(root):
    page.wait_for_function("""root=>{const visible=[...root.querySelectorAll('img')].filter(img=>{const r=img.getBoundingClientRect();return r.width>0&&r.height>0&&r.right>0&&r.left<innerWidth&&r.bottom>0&&r.top<innerHeight});return visible.length>0&&visible.every(img=>img.complete&&img.naturalWidth>1)}""",arg=root.element_handle(),timeout=30000)
   wait_visible_photos(vitrine)
   page.screenshot(path=str(E/('home-'+engine+'-'+str(width)+'-'+locale+'.png')))
   shelf=page.locator('#product-shelf-storageIdeas');shelf.evaluate('(e)=>scrollTo({top:e.getBoundingClientRect().top+scrollY-document.querySelector(".store-header").getBoundingClientRect().height-16,behavior:"instant"})');page.wait_for_load_state('networkidle');card=shelf.locator('.product-card').first
   assert card.evaluate('(c)=>{const h=c.querySelector("h3").getBoundingClientRect(),v=c.querySelector(".card-color").getBoundingClientRect();return v.top-h.bottom<18&&h.height<60}')
   assert card.locator('.card-price-main').evaluate('(e)=>e.getBoundingClientRect().height<30&&e.querySelector(".price-unit").textContent.includes("m²")')
   if width<768:assert page.locator('.quick-open:visible').count()==0
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');wait_visible_photos(shelf);page.screenshot(path=str(E/('cards-'+engine+'-'+str(width)+'-'+locale+'.png')))
   # Full supplier prose must replace the compact catalogue summary. The local
   # provider is disabled; this acceptance never creates a charge or order.
   navigate(origin+'/?lang='+locale+'&product='+supplier['id']);expect(page.locator('#product-title')).to_be_visible();translation=texts(locale);target=localized(supplierText,locale,translation);paragraph=next(p.strip()for p in target.split('\n\n')if len(p.strip())>80)
   try:expect(page.locator('.product-about')).to_contain_text(paragraph[-70:],timeout=20000)
   except Exception:
    debug=page.evaluate("""async ({id,locale})=>{try{const response=await fetch('/api/supplier-products/'+id);const data=await response.json();const m=await import('/locale-runtime.js?v=target-locales-20261111-r1');await m.ensureLocaleData(data.description,locale);m.localizeDataTree(data,locale);return {status:response.status,id:data.id,sha:data.sha256,text:m.localizedValue(data.description,locale)};}catch(e){return {error:e.message,source:e.translationSource}}}""",{'id':supplier['id'],'locale':locale})
    (E/('product-failure-'+locale+'.json')).write_text(json.dumps({'errors':errors,'text':page.locator('.product-about').inner_text(),'expected':paragraph,'debug':debug},ensure_ascii=False,indent=2),encoding='utf8');raise
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   recovery=verify_recovery(page,origin,locale,supplier,paragraph,translation)
   raw=context.request.get(origin+'/?lang='+locale+'&product=5015');assert raw.status==200 and 'lang="'+locale+'"'in raw.text()[:500]
   navigate(origin+'/legal/kvkk?lang='+locale);corpus=json.loads((release/('private/site-documents.'+locale+'.json')).read_bytes());doc=next(d for d in corpus['documents']if d['id']=='kvkk');expect(page.locator('h1')).to_have_text(doc['title']);expect(page.locator('html')).to_have_attribute('lang',locale);expect(page.locator('.legal-language a')).to_have_count(11);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   navigate(origin+'/?lang='+locale);page.locator('#display-currency').select_option('EUR');page.reload(wait_until='networkidle');expect(page.locator('#display-currency')).to_have_value('EUR',timeout=20000);page.locator('#language').select_option('en'if locale!='en'else'tr');page.locator('#language').select_option(locale);expect(page.locator('#display-currency')).to_have_value(defaults[locale])
   if engine=='chromium'and width==1440 and locale=='tr':
    page.evaluate("sessionStorage.setItem('qa-show-map','1');localStorage.removeItem('nodeno.international-welcome.hidden')")
    for country,want,currency in countryMatrix:
     navigate(origin+'/?lang='+page.locator('#language').input_value());dialog=page.locator('#international-welcome');expect(dialog).to_be_visible(timeout=15000)
     if country=='TR':dialog.locator('[data-map-region=TUR]').dispatch_event('click')
     else:dialog.locator('[data-country-select='+country+']').first.click()
     expect(dialog).to_have_count(0);expect(page.locator('#language')).to_have_value(want);expect(page.locator('#display-currency')).to_have_value(currency,timeout=20000);assert 'lang='+want in page.url;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.evaluate("sessionStorage.removeItem('qa-show-map');localStorage.setItem('nodeno.international-welcome.hidden','1')")
   assert not errors,(engine,width,locale,errors)
   checks.append({'engine':engine,'width':width,'locale':locale,'visiblePhotosLoaded':True,'compactTitleColourGap':True,'priceAndUnitTogether':True,'noQuickOverlay':True,'noOverflow':True,'noRuntimeErrors':True,'nativeProduct':True,'nativeLegal':True,'correctCurrency':True,**recovery});context.close();browser.close();print(json.dumps({'passedCase':locale,'width':width,'engine':engine}),flush=True)
 (E/'browser-local.json').write_text(json.dumps({'passed':True,'testOnly':proof.get('testOnly',False),'productionAcceptance':not proof.get('testOnly',False),'releaseHash':proof['releaseHash'],'checks':checks,'countryMapMatrix':True,'manualCurrencyPersistence':True,'realCharges':0},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(checks)}),flush=True)
