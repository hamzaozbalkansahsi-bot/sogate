"""Isolated packaged management acceptance: no production identities or demo records."""
from pathlib import Path
import os,json,tempfile,shutil,subprocess,socket,time,secrets,hashlib,base64,hmac,struct
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/control-seo';OUT.mkdir(exist_ok=True)
def otp(secret):
 digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15
 return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
report={'checks':[]}
with sync_playwright() as p:
 for engine in (('chromium',) if os.environ.get('NODENO_ADMIN_QUICK') else ('chromium','webkit')):
  temp=Path(tempfile.mkdtemp(prefix='nodeno-control-browser-'));release=temp/'release';shutil.copytree(ROOT/'artifacts/cpanel-release',release);storage=temp/'persistent';storage.mkdir();token=secrets.token_hex(32);email='operator@example.test'
  (storage/'admin-bootstrap.json').write_text(json.dumps({'schema':1,'email':email,'tokenHash':hashlib.sha256(token.encode()).hexdigest(),'expiresAt':int(time.time())+1800}),encoding='utf-8')
  q=lambda path:"'"+path.as_posix().replace("'","\\'")+"'"
  (release/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(release/'private')+",'storageRoot'=>"+q(storage)+",'mediaRoot'=>"+q(ROOT/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf-8')
  sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();upstream=port;sock=socket.socket();sock.bind(('127.0.0.1',0));tls_port=sock.getsockname()[1];sock.close();origin='https://127.0.0.1:'+str(tls_port)
  log=open(OUT/('admin-'+engine+'-php.log'),'w',encoding='utf-8');env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'};server=subprocess.Popen([str(ROOT/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(port),'-t',str(release/'public'),str(ROOT/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  cert=temp/'cert.pem';key=temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  proxy=subprocess.Popen(['node',str(ROOT/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls_port),'NODENO_QA_UPSTREAM':str(port),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  browser=None
  try:
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(p,engine).launch(executable_path=str(executable));context=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1050});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for attempt in range(60):
    try:
     response=page.goto(origin+'/yonetim',wait_until='networkidle');break
    except Exception:
     time.sleep(.1)
   assert response.status==200;expect(page.locator('#auth')).to_be_visible();page.screenshot(path=str(OUT/('admin-'+engine+'-login.png')))
   assert context.request.get(origin+'/api/admin/orders').status==401
   page.locator('[name=email]').fill(email);page.locator('[name=password]').fill('NODENO-browser-password-2026');page.locator('[name=token]').fill(token);page.get_by_role('button',name='Doğrulamayı kur',exact=True).click();expect(page.locator('.secret')).to_be_visible();secret=page.locator('.secret').inner_text();page.locator('[name=code]').fill(otp(secret));page.get_by_role('button',name='Kurulumu tamamla',exact=True).click();expect(page.get_by_role('heading',name='Kurtarma kodlarınızı saklayın')).to_be_visible();page.get_by_role('button',name='Yönetime geç',exact=True).click();expect(page.get_by_role('heading',name='Mağazanızın genel görünümü')).to_be_visible();page.screenshot(path=str(OUT/('admin-'+engine+'-dashboard.png')))
   for section in ['business','products','orders','carriers','shipping','shipments','invoices','productMappings','support','templates','messages','advertising','campaigns','coupons','collections','appearance','seo','markets','ranking','analytics','integrations','team','system','customer-orders','customers','audit','guide']:
    page.goto(origin+'/yonetim#'+section,wait_until='networkidle');expect(page.locator('#main h1')).to_be_visible();assert 'Kayıtlar alınamadı' not in page.locator('#main').inner_text(),section;assert 'İşlem tamamlanamadı' not in page.locator('#main').inner_text(),section
   page.goto(origin+'/yonetim#products',wait_until='networkidle');page.locator('[data-edit]').first.click();expect(page.locator('#record-form')).to_be_visible();page.locator('[name=priceMinor]').fill('1234.56');page.get_by_role('button',name='Taslağı kaydet',exact=True).click();expect(page.locator('#editor')).not_to_be_visible();page.locator('[data-edit]').first.click();page.get_by_role('button',name='Yayınla',exact=True).click();expect(page.locator('#editor')).not_to_be_visible();page.screenshot(path=str(OUT/('admin-'+engine+'-products.png')))
   catalog=context.request.get(origin+'/api/catalog').json();changed=[v for v in catalog['products'] if v.get('salePriceMinor')==123456];assert changed,'Published price did not reach API';product=changed[0];html=context.request.get(origin+'/?lang=tr&product='+product['id']).text();assert '1234.56' in html,'Published price did not reach JSON-LD';assert '1.234,56' in html,'Published price did not reach SSR'
   page.reload(wait_until='networkidle');page.locator('[data-edit]').first.click();expect(page.locator('[name=priceMinor]')).to_have_value('1234.56');page.locator('#editor [data-close]').click()
   page.goto(origin+'/yonetim#orders',wait_until='networkidle');page.locator('[data-new]').first.click();page.locator('[name=title]').fill('İzole kabul talebi');page.locator('[name=email]').fill('buyer@example.test');page.locator('[name=country]').select_option('TR');page.locator('[name=address]').fill('İzole test adresi');page.locator('[name=status]').select_option('draft');page.locator('[data-item-product]').select_option(product['id']);page.locator('[data-item-quantity]').fill('2');page.locator('[data-item-quantity]').dispatch_event('change');expect(page.locator('[data-item-total]')).to_contain_text('2.469,12');page.get_by_role('button',name='Kaydet',exact=True).click();expect(page.locator('#editor')).not_to_be_visible();page.locator('[data-edit]').first.click();expect(page.locator('[name=totalMinor]')).to_have_value('2469.12');assert page.get_by_role('link',name='Proforma görüntüle').count()==1;page.locator('#editor [data-close]').click()
   page.goto(origin+'/yonetim#integrations',wait_until='networkidle');page.locator('[data-provider=kolaybi]').click();page.locator('[name=channel]').fill('isolated-channel');page.locator('[name=apiKey]').fill('isolated-private-key');page.get_by_role('button',name='Güvenli kaydet',exact=True).click();expect(page.locator('#editor')).not_to_be_visible();expect(page.locator('#main')).to_contain_text('Kaydedildi, doğrulanmadı');assert 'isolated-private-key' not in context.request.get(origin+'/api/admin/integrations/kolaybi').text();page.locator('[data-provider=kolaybi]').click();expect(page.locator('[name=apiKey]')).to_have_value('');page.locator('#editor [data-close]').click()
   page.set_viewport_size({'width':390,'height':844});page.goto(origin+'/yonetim#products',wait_until='networkidle');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Mobile management page overflow';page.locator('[data-menu]').click();expect(page.locator('.sidebar.open')).to_be_visible();page.locator('.sidebar a[href="#dashboard"]').click();expect(page.get_by_role('heading',name='Mağazanızın genel görünümü')).to_be_visible();page.screenshot(path=str(OUT/('admin-'+engine+'-mobile.png')))
   page.route('**/api/admin/logout',lambda route:route.abort());page.locator('[data-logout]').click();expect(page.locator('#notice')).to_contain_text('Çıkış yapılamadı');assert page.locator('[data-logout]').is_visible();page.unroute('**/api/admin/logout');page.set_viewport_size({'width':1440,'height':1050});page.goto(origin+'/yonetim#dashboard',wait_until='networkidle');expect(page.get_by_role('heading',name='Mağazanızın genel görünümü')).to_be_visible();held=[]
   def hold_orders(route):
    response=route.fetch();held.append((route,response));page.evaluate("document.documentElement.dataset.controlHeld = 'yes'")
   page.route('**/api/admin/orders',hold_orders)
   with page.expect_request('**/api/admin/orders'):
    page.locator('.sidebar a[href="#orders"]').click()
   expect(page.locator('html')).to_have_attribute('data-control-held','yes');assert held,'The protected response must be held before logout';page.route('**/api/admin/session',lambda route:route.abort())
   page.locator('[data-logout]').click();expect(page.locator('#auth')).to_be_visible();held[0][0].fulfill(response=held[0][1]);page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');expect(page.locator('#auth')).to_be_visible();assert 'İzole kabul talebi' not in page.locator('#main').inner_text();assert context.request.get(origin+'/api/admin/orders').status==401;assert not errors,errors
   report['checks'].append({'engine':engine,'desktop':True,'mobile':True,'MFA':True,'allSections':27,'versionedPublish':True,'priceParity':True,'orderArithmetic':True,'logoutBoundary':True,'errors':errors})
  finally:
   if browser:browser.close()
   proxy.terminate();proxy.wait(timeout=10);server.terminate();server.wait(timeout=10);log.close()
report['passed']=True;report['releaseHash']=json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text(encoding='utf-8'))['releaseHash'];(OUT/'admin-browser-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
