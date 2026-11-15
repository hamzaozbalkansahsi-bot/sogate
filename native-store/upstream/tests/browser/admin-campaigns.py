"""Actual admin form -> PHP -> SQLite -> storefront API/SSR, isolated identities only."""
from pathlib import Path
import os,json,tempfile,shutil,subprocess,socket,time,secrets,hashlib,base64,hmac,struct
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/media-object-removal-20261102';OUT=E/'admin-campaign-browser';OUT.mkdir(exist_ok=True)
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
def port():
 s=socket.socket();s.bind(('127.0.0.1',0));n=s.getsockname()[1];s.close();return n
def otp(secret):
 digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15;return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
temp=Path(tempfile.mkdtemp(prefix='nodeno-campaign-browser-'));release=temp/'release';shutil.copytree(R/'tmp/media-object-removal-20261102/live-base',release)
for f in ['control-http.php','control-catalog.php']:shutil.copyfile(R/'hosting'/f,release/'private'/f)
for f in ['admin.js','admin.css','admin.html','admin-password-visibility.js','admin-campaigns.js']:shutil.copyfile(R/'web'/f,release/'public'/f)
storage=temp/'persistent';storage.mkdir();token=secrets.token_hex(32);email='campaign-operator@example.test'
(storage/'admin-bootstrap.json').write_text(json.dumps({'schema':1,'email':email,'tokenHash':hashlib.sha256(token.encode()).hexdigest(),'expiresAt':int(time.time())+1800}),encoding='utf-8')
quote=lambda p:"'"+p.as_posix().replace("'","\\'")+"'"
(release/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+quote(release/'private')+",'storageRoot'=>"+quote(storage)+",'mediaRoot'=>"+quote(R/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf-8')
upstream=port();tls=port();origin='https://127.0.0.1:'+str(tls);log=open(OUT/'php.log','w',encoding='utf-8')
server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(release/'public'),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
cert=temp/'cert.pem';key=temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
proxy=subprocess.Popen([str(NODE),str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
report={'isolatedTestOnly':True,'realPHPAndSQLite':True,'views':[],'testedFilesSha256':{relative:hashlib.sha256((release/relative).read_bytes()).hexdigest()for relative in ['public/admin.html','public/admin.js','public/admin.css','public/admin-password-visibility.js','public/admin-campaigns.js','private/control-catalog.php','private/control-http.php']}};errors=[]
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'));context=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1050},timezone_id='Europe/Istanbul');page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  for attempt in range(60):
   try:page.goto(origin+'/yonetim',wait_until='networkidle');break
   except Exception:time.sleep(.1)
  page.locator('[name=email]').fill(email);page.locator('[name=password]').fill('Nodeno-Isolated-Password-2026');page.locator('[name=token]').fill(token);page.get_by_role('button',name='Doğrulamayı kur',exact=True).click();expect(page.locator('.secret')).to_be_visible();secret=page.locator('.secret').inner_text();page.locator('[name=code]').fill(otp(secret));page.get_by_role('button',name='Kurulumu tamamla',exact=True).click();page.get_by_role('button',name='Yönetime geç',exact=True).click();expect(page.locator('#main h1')).to_be_visible()
  source=context.request.get(origin+'/api/catalog').json();product=next(v for v in source['products']if v['id']=='2395');base=product['salePriceMinor']
  page.goto(origin+'/yonetim#campaigns',wait_until='networkidle');page.get_by_role('button',name='Yeni kampanya',exact=True).first.click();page.locator('[name=title]').fill('İzole Kasım kampanyası');page.locator('[data-product-filter=productIds]').fill(product['code']);page.locator('[data-product-choice][value="2395"]').check();page.locator('[name=percent]').fill('25')
  page.locator('[name=startsAt]').fill(time.strftime('%Y-%m-%dT%H:%M',time.gmtime(time.time()+3*3600-3600)));page.locator('[name=endsAt]').fill(time.strftime('%Y-%m-%dT%H:%M',time.gmtime(time.time()+3*3600+86400)));expect(page.locator('[name=enabled]')).to_be_checked();expect(page.locator('[data-campaign-preview]')).to_contain_text('Kampanya hesabı')
  def shot(name):
   page.evaluate('() => Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{})))')
   if page.locator('.notice-toast').count():expect(page.locator('.notice-toast')).not_to_be_visible(timeout=6000)
   f=OUT/(name+'.png');page.screenshot(path=str(f),full_page=True);report['views'].append({'path':f.relative_to(R).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'visualReview':False})
  shot('desktop-campaign-editor');lost=[]
  def lose_first_response(route):
   if not lost:
    response=route.fetch();assert response.ok;lost.append(True);route.abort()
   else:
    response=route.fetch();route.fulfill(response=response)
  page.route('**/api/admin/campaigns/*/save-publish',lose_first_response)
  page.get_by_role('button',name='Kaydet ve yayınla',exact=True).click();expect(page.locator('#record-form [data-error]')).not_to_be_empty();expect(page.locator('#editor')).to_be_visible()
  page.get_by_role('button',name='Kaydet ve yayınla',exact=True).click();expect(page.locator('#editor')).not_to_be_visible(timeout=5000);expect(page.locator('[data-campaign-card]')).to_contain_text('Aktif');page.unroute('**/api/admin/campaigns/*/save-publish');assert len(context.request.get(origin+'/api/admin/campaigns').json()['data'])==1
  current=context.request.get(origin+'/api/catalog').json();live=next(v for v in current['products']if v['id']=='2395');assert live['salePriceMinor']==(base*75+50)//100;assert 'previousPriceMinor'not in live
  html=context.request.get(origin+'/?lang=tr&product=2395').text();assert format(live['salePriceMinor']/100,'.2f')in html;shot('desktop-campaign-active')
  page.locator('[data-edit]').first.click();page.locator('[name=percent]').fill('30');page.get_by_role('button',name='Taslağı kaydet',exact=True).click();expect(page.locator('#editor')).not_to_be_visible();expect(page.locator('[data-campaign-card]')).to_contain_text('değişiklik bekliyor');assert next(v for v in context.request.get(origin+'/api/catalog').json()['products']if v['id']=='2395')['salePriceMinor']==live['salePriceMinor']
  page.locator('[data-edit]').first.click();page.locator('[name=percent]').fill('40');page.get_by_role('button',name='Kaydet ve yayınla',exact=True).click();expect(page.locator('#editor')).not_to_be_visible();assert next(v for v in context.request.get(origin+'/api/catalog').json()['products']if v['id']=='2395')['salePriceMinor']==(base*60+50)//100
  page.goto(origin+'/yonetim#dashboard',wait_until='networkidle');expect(page.get_by_role('heading',name='Mağazanızın genel görünümü',exact=True)).to_be_visible();shot('desktop-dashboard');page.set_viewport_size({'width':390,'height':844});shot('mobile-dashboard');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.locator('[data-menu]').click();expect(page.locator('.sidebar.open')).to_be_visible();page.locator('[data-nav-search]').fill('entegrasyon');expect(page.locator('.sidebar .nav-link:visible')).to_have_count(1);page.locator('[data-nav-search]').fill('');page.locator('[data-menu-close]').click()
  page.goto(origin+'/yonetim#campaigns',wait_until='networkidle');expect(page.locator('[data-campaign-card]')).to_be_visible();shot('mobile-campaign-active');page.locator('[data-edit]').first.click();expect(page.locator('#record-form')).to_be_visible();shot('mobile-campaign-editor');page.locator('[data-campaign-preview]').scroll_into_view_if_needed();shot('mobile-campaign-price-preview');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  page.locator('#editor [data-close]').click();page.goto(origin+'/yonetim#guide',wait_until='networkidle');expect(page.get_by_role('heading',name='Yönetim rehberi',exact=True)).to_be_visible();expect(page.locator('#main')).to_contain_text('Kaydet ve yayınla');assert 'Taslağı tekrar açın'not in page.locator('#main').inner_text()
  report.update(passed=True,lostResponseRetryPublishesOnce=True,oneStepPublishesExactPrice=True,latestUnsavedEditsPublished=True,draftDoesNotChangeLivePrice=True,storefrontSSRMatches=True,guideMatchesActions=True,javascriptErrors=errors);browser.close()
finally:
 proxy.terminate();proxy.wait(timeout=10);server.terminate();server.wait(timeout=10);log.close();(OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
