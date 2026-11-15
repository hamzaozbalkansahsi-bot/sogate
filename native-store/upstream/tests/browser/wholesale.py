"""Actual packaged B2B flow against isolated PHP/SQLite, never production buyers."""
from pathlib import Path
import os,json,tempfile,shutil,subprocess,socket,time,secrets,hashlib,base64,hmac,struct,re
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/wholesale-qa';OUT.mkdir(exist_ok=True)
def port():
 s=socket.socket();s.bind(('127.0.0.1',0));value=s.getsockname()[1];s.close();return value
def otp(secret):
 digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15
 return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def scalar(storage,sql):
 script="require 'hosting/control-store.php';$db=nodenoControlDatabase($argv[1]);echo json_encode($db->query($argv[2])->fetchAll(),JSON_THROW_ON_ERROR);"
 return json.loads(subprocess.check_output([str(ROOT/'artifacts/runtime-php/php.exe'),'-r',script,str(storage),sql],cwd=ROOT,text=True,encoding='utf-8'))
report={'checks':[],'sourceOverride':bool(os.environ.get('NODENO_WHOLESALE_SOURCE'))}
with sync_playwright() as p:
 for engine in (('chromium',) if os.environ.get('NODENO_WHOLESALE_RED') else ('chromium','webkit')):
  temp=Path(tempfile.mkdtemp(prefix='nodeno-wholesale-browser-'));release=temp/'release';shutil.copytree(ROOT/'artifacts/cpanel-release',release);storage=temp/'persistent';storage.mkdir();token=secrets.token_hex(32);email='wholesale-operator@example.test'
  (storage/'admin-bootstrap.json').write_text(json.dumps({'schema':1,'email':email,'tokenHash':hashlib.sha256(token.encode()).hexdigest(),'expiresAt':int(time.time())+1800}),encoding='utf-8')
  q=lambda path:"'"+path.as_posix().replace("'","\\'")+"'"
  (release/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(release/'private')+",'storageRoot'=>"+q(storage)+",'mediaRoot'=>"+q(ROOT/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf-8')
  upstream=port();tls_port=port();origin='https://127.0.0.1:'+str(tls_port);log=open(OUT/(engine+'-php.log'),'w',encoding='utf-8');env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'}
  server=subprocess.Popen([str(ROOT/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(release/'public'),str(ROOT/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  cert=temp/'cert.pem';key=temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  proxy=subprocess.Popen(['node',str(ROOT/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls_port),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);browser=None
  try:
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(p,engine).launch(executable_path=str(executable));guest=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1050});page=guest.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   if os.environ.get('NODENO_WHOLESALE_SOURCE'):
    page.route('**/wholesale.js?*',lambda route:route.fulfill(path=str(ROOT/'web/wholesale.js'),content_type='text/javascript'))
   if os.environ.get('NODENO_WHOLESALE_RED'):
    old=subprocess.check_output(['git','show','bdac426:web/app.js'],cwd=ROOT)
    page.route('**/app.js?*',lambda route:route.fulfill(body=old,content_type='text/javascript'))
   for attempt in range(60):
    try:page.goto(origin+'/?page=wholesale&lang=en',wait_until='networkidle');break
    except Exception:time.sleep(.1)
   expect(page.locator('#wholesale-form')).to_be_visible(timeout=7000)
   necessary=page.get_by_role('button',name='Necessary only',exact=True)
   if necessary.is_visible():necessary.click()
   catalog=guest.request.get(origin+'/api/catalog').json();product=catalog['products'][0];product_id=product['id']
   for lang in ['tr','en','ru','ar']:
    page.goto(origin+'/?page=wholesale&lang='+lang,wait_until='networkidle');expect(page.locator('#wholesale-form')).to_be_visible();assert page.locator('link[rel=canonical]').get_attribute('href')=='https://nodenohome.com/?lang='+lang+'&page=wholesale';assert page.locator('html').get_attribute('dir')==('rtl' if lang=='ar' else 'ltr')
    page.set_viewport_size({'width':375,'height':844});page.screenshot(path=str(OUT/(engine+'-'+lang+'-mobile.png')))
    if not page.evaluate('document.documentElement.scrollWidth<=innerWidth'):
     print(json.dumps(page.evaluate("({width:innerWidth,scroll:document.documentElement.scrollWidth,elements:[...document.querySelectorAll('body *')].map(e=>({tag:e.tagName,id:e.id,class:e.className,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right})).filter(r=>r.left< -1||r.right>innerWidth+1).slice(0,20)})")),flush=True)
     raise AssertionError(lang+' mobile overflow')
    page.set_viewport_size({'width':1440,'height':1050})
   page.goto(origin+'/?page=wholesale&lang=en&item='+product_id,wait_until='networkidle');expect(page.locator('[data-wholesale-line]')).to_have_count(1);assert page.locator('[name=country] option[value=TR]').count()==0;assert page.locator('[name=country] option[value=US]').count()==1
   line=page.locator('[data-wholesale-line]').first;line.locator('[data-wholesale-quantity]').fill('2');page.locator('[data-wholesale-add][aria-pressed=false]').first.click();expect(page.locator('[data-wholesale-line]')).to_have_count(2)
   for key,value in {'company':'Isolated wholesale buyer','name':'Test contact','email':'buyer@example.test','phone':'+441234567890','city':'London','note':'Test delivery inquiry'}.items():page.locator('#wholesale-form [name='+key+']').fill(value)
   page.locator('[name=country]').select_option('GB');page.evaluate("window.dispatchEvent(new PopStateEvent('popstate'))");expect(page.locator('[name=company]')).to_have_value('Isolated wholesale buyer')
   page.locator('#language').select_option('ar');expect(page.locator('[name=company]')).to_have_value('Isolated wholesale buyer');page.locator('#language').select_option('en');expect(page.locator('[name=company]')).to_have_value('Isolated wholesale buyer');page.locator('[name=consent]').check()
   page.route('**/api/wholesale/inquiries',lambda route:route.abort());page.locator('.wholesale-submit').click();expect(page.locator('[data-wholesale-error]')).to_contain_text('could not be sent');expect(page.locator('[name=email]')).to_have_value('buyer@example.test');page.unroute('**/api/wholesale/inquiries')
   held=[]
   def hold_inquiry(route):
    response=route.fetch();held.append((route,response));page.evaluate("document.documentElement.dataset.wholesalePending = 'yes'")
   page.route('**/api/wholesale/inquiries',hold_inquiry);page.locator('.wholesale-submit').click();expect(page.locator('html')).to_have_attribute('data-wholesale-pending','yes');expect(page.locator('[name=company]')).to_be_disabled();expect(page.locator('[data-wholesale-quantity]').first).to_be_disabled();expect(page.locator('[data-wholesale-add]').first).to_be_disabled();expect(page.locator('[data-wholesale-remove]').first).to_be_disabled();page.evaluate("window.dispatchEvent(new PopStateEvent('popstate'))");expect(page.locator('[name=company]')).to_be_disabled();expect(page.locator('[name=company]')).to_have_value('Isolated wholesale buyer');held[0][0].fulfill(response=held[0][1]);page.unroute('**/api/wholesale/inquiries');expect(page.locator('.wholesale-success')).to_be_visible();assert guest.request.get(origin+'/api/admin/wholesaleRequests').status==401;rows=scalar(storage,"SELECT data_json FROM control_records WHERE resource='wholesaleRequests'");assert len(rows)==1;stored=json.loads(rows[0]['data_json']);assert stored['email']=='buyer@example.test';assert len(stored['lines'])==2;assert stored['lines'][0]['unit']=='piece' and stored['lines'][0]['quantity']==2;assert stored['lines'][0]['units']==2 and stored['lines'][0]['unitPriceMinor'] is None;assert not scalar(storage,"SELECT id FROM control_records WHERE resource='orders'")
   admin_context=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1050});admin=admin_context.new_page();admin.on('pageerror',lambda e:errors.append(str(e)));admin.goto(origin+'/yonetim',wait_until='networkidle');admin.locator('[name=email]').fill(email);admin.locator('[name=password]').fill('NODENO-wholesale-local-password');admin.locator('[name=token]').fill(token);admin.get_by_role('button',name='Doğrulamayı kur',exact=True).click();expect(admin.locator('.secret')).to_be_visible();secret=admin.locator('.secret').inner_text();admin.locator('[name=code]').fill(otp(secret));admin.get_by_role('button',name='Kurulumu tamamla',exact=True).click();admin.get_by_role('button',name='Yönetime geç',exact=True).click()
   admin.goto(origin+'/yonetim#wholesaleRequests',wait_until='networkidle');expect(admin.locator('#record-table')).to_contain_text('Isolated wholesale buyer');assert admin.locator('[data-new]').count()==0;admin.locator('[data-edit]').first.click();expect(admin.locator('[name=requestSummary]')).to_have_attribute('readonly','');expect(admin.locator('[name=requestSummary]')).to_have_value(re.compile('.*2 adet',re.S));admin.locator('[name=status]').select_option('in_progress');admin.locator('[name=note]').fill('Reviewing shipment');admin.get_by_role('button',name='Kaydet',exact=True).click();expect(admin.locator('#editor')).not_to_be_visible();admin.screenshot(path=str(OUT/(engine+'-admin-requests.png')))
   admin.goto(origin+'/yonetim#wholesale',wait_until='networkidle');admin.locator('[data-new]').first.click();admin.locator('[name=productId]').select_option(product_id);admin.locator('[name=enabled]').check();admin.locator('[name=minimumQuantity]').fill('2');admin.locator('[name=currency]').select_option('EUR');admin.locator('[name=tier1Units]').fill('1');admin.locator('[name=tier1PriceMinor]').fill('90');admin.locator('[name=tier2Units]').fill('32');admin.locator('[name=tier2PriceMinor]').fill('80');admin.get_by_role('button',name='Taslağı kaydet',exact=True).click();expect(admin.locator('#editor')).not_to_be_visible();admin.locator('[data-edit]').first.click();admin.get_by_role('button',name='Yayınla',exact=True).click();expect(admin.locator('#editor')).not_to_be_visible()
   page.goto(origin+'/?page=wholesale&lang=en&item='+product_id,wait_until='networkidle');expect(page.locator('[data-wholesale-line]')).to_have_count(1);line=page.locator('[data-wholesale-line]').first;line.locator('[data-wholesale-quantity]').fill('32');expect(line.locator('[data-wholesale-calculation]')).to_contain_text('€80.00');expect(line.locator('[data-wholesale-calculation]')).to_contain_text('€2,560.00');page.screenshot(path=str(OUT/(engine+'-desktop.png')));page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');line.scroll_into_view_if_needed();page.screenshot(path=str(OUT/(engine+'-quote-mobile.png')))
   page.goto(origin+'/?product='+product_id+'&lang=en',wait_until='networkidle');expect(page.locator('.product-purchase .wholesale-entry a')).to_be_visible();assert 'item='+product_id in page.locator('.product-purchase .wholesale-entry a').get_attribute('href');assert not errors,errors
   report['checks'].append({'engine':engine,'locales':4,'mobile':True,'desktop':True,'guestInquiry':True,'privateBoundary':True,'adminWorkflow':True,'pieceSnapshot':True,'tierCurrency':True,'retainedForm':True,'errors':errors})
  finally:
   if browser:browser.close()
   proxy.terminate();server.terminate();proxy.wait(timeout=10);server.wait(timeout=10);log.close()
report['passed']=True;report['releaseHash']=json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text())['releaseHash'];(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
