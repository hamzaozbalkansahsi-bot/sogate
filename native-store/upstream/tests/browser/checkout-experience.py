"""Real local PHP quotes + browser UX acceptance. Stripe responses are explicitly mocked; no charges."""
from pathlib import Path
import json,os,shutil,socket,subprocess,tempfile,time,hashlib,mimetypes
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];OUT=R/'artifacts/checkout-experience-20261112';release=R/'artifacts/cpanel-release-checkout-experience-20261112'
manifest=json.loads((release/'private/release.json').read_bytes());catalog=json.loads((release/'private/catalog.json').read_bytes())
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
q=lambda p:"'"+p.as_posix().replace("'","\\'")+"'"
temp=Path(tempfile.mkdtemp(prefix='nodeno-stripe-browser-'));server=proxy=log=None;checks=[]
try:
 local=temp/'release';shutil.copytree(release,local,ignore=shutil.ignore_patterns('fronts','doors','cache'));storage=temp/'data';storage.mkdir();(local/'private/cache').mkdir(exist_ok=True)
 (local/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(local/'private')+",'storageRoot'=>"+q(storage)+",'mediaRoot'=>"+q(R/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf8')
 upstream,tls=port(),port();origin='https://127.0.0.1:'+str(tls);log=open(OUT/'browser-server.log','w',encoding='utf8')
 server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(local/'public'),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(local/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 cert,key=temp/'cert.pem',temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
 proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);time.sleep(1)
 with sync_playwright()as pw:
  for engine,width in [('chromium',1440),('chromium',390),('webkit',390)]:
   if os.environ.get('QA_WIDTH')and width!=int(os.environ['QA_WIDTH']):continue
   if os.environ.get('QA_ENGINE')and engine!=os.environ['QA_ENGINE']:continue
   exe=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(pw,engine).launch(executable_path=str(exe),headless=True)
   for lang in os.environ.get('QA_LANGS','tr,en,ru,ar').split(','):
    print(json.dumps({'stage':'scenario','engine':engine,'width':width,'locale':lang}),flush=True)
    storage=temp/('data-'+engine+'-'+str(width)+'-'+lang);storage.mkdir();(local/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(local/'private')+",'storageRoot'=>"+q(storage)+",'mediaRoot'=>"+q(R/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf8')
    context=browser.new_context(ignore_https_errors=True,viewport={'width':width,'height':1000 if width>768 else 844},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:print(json.dumps({'httpError':r.status,'path':urlparse(r.url).path}),flush=True)if r.status>=400 else None)
    def assets(route):
     p=release/'public'/unquote(urlparse(route.request.url).path).lstrip('/')
     if p.is_file():route.fulfill(body=p.read_bytes(),content_type=mimetypes.guess_type(str(p))[0]or'application/octet-stream')
     else:route.continue_()
    page.route('**/assets/**',assets)
    approved=json.loads((release/'private/media-approved.json').read_bytes());cleanup=json.loads((R/'artifacts/media-cleanup.json').read_bytes())
    def media(route):
     parts=urlparse(route.request.url).path.strip('/').split('/');identity=approved['references'].get(parts[1]+':'+parts[2]);row=approved['images'][identity];body=(R/cleanup['images'][identity]['path']).read_bytes();assert hashlib.sha256(body).hexdigest()==row['outputSha'];route.fulfill(body=body,content_type=row['mime'])
    page.route('**/media/**',media)
    page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'));localStorage.setItem('nodeno.cart.v1',JSON.stringify([{id:'2395',quantity:2},{id:'2393',quantity:1}]))")
    page.goto(origin+'/?lang='+lang+'&page=checkout',wait_until='networkidle')
    necessary=page.locator('#insights-banner .insights-actions button').last
    if necessary.is_visible():necessary.click()
    page.locator('[data-action=guest-start]').click();form=page.locator('#guest-checkout-form')
    for name,value in {'name':'Deniz Örnek','email':'deniz@example.test','phone':'+905551112233','city':'İzmir','district':'Buca','postalCode':'35040','line1':'Örnek Mahallesi\nDeneme Sokak 12'}.items():form.locator('[name="'+name+'"]').fill(value)
    form.locator('[name=name]').focus();page.keyboard.press('Enter');expect(form.locator('[name=email]')).to_be_focused();page.keyboard.press('Tab');expect(form.locator('[name=phone]')).to_be_focused();form.locator('[name=country]').select_option('TR');form.locator('[type=submit]').click();expect(page.locator('.guest-review')).to_be_visible();expect(page.locator('.payment-totals')).to_be_visible();assert page.locator('.payment-form').count()==0
    # Read-only public status is real PHP; only provider readiness is substituted for UI acceptance.
    def status(route):
     data=route.fetch().json();seller={'name':'PTYS Technologies LLC','address':'Test seller address','email':'seller@example.test','termsVersion':'fixture','terms':{l:'Fixture sale terms for browser acceptance only.'for l in ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']},'returns':{l:'Fixture return terms for browser acceptance only.'for l in ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']}};data.update(enabled=True,test=True,seller=seller,termsRevision='fixture-terms');route.fulfill(json=data)
    page.route('**/api/payments/status',status)
    page.locator('[data-action=guest-edit]').click();expect(page.locator('#guest-checkout-form')).to_be_visible();page.wait_for_load_state('networkidle');assert page.locator('.payment-form').count()==0
    page.locator('#guest-checkout-form [type=submit]').click();expect(page.locator('.payment-form')).to_be_visible();page.wait_for_load_state('networkidle')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert page.locator('.checkout-product-photo img').count()==2
    page.screenshot(path=str(OUT/f'local-{engine}-{width}-{lang}-review.png'),full_page=True)
    attempts=[]
    def checkout(route):attempts.append(route.request.post_data_json);route.fulfill(status=503,json={'error':'payment_provider_unavailable'})
    page.route('**/api/payments/checkout',checkout);pay=page.locator('.payment-form');pay.locator('[name=terms]').check();pay.locator('[type=submit]').click();expect(pay.locator('[role=alert]')).not_to_be_empty();pay.locator('[type=submit]').click();page.wait_for_load_state('networkidle');assert len(attempts)==2 and attempts[0]['idempotencyKey']==attempts[1]['idempotencyKey'];assert attempts[0]['contact']['delivery']['line1'].count('\n')==1
    page.reload(wait_until='networkidle');expect(page.locator('.guest-review')).to_be_visible();expect(page.locator('.guest-review')).to_contain_text('deniz@example.test');expect(page.locator('[name=freight]')).to_have_count(0)
    expect(page.locator('.payment-form')).to_be_visible();
    for button in page.locator('[data-checkout-terms]').all():
     button.click();expect(page.locator('#checkout-terms-dialog')).to_be_visible();page.locator('#checkout-terms-dialog header button').click();expect(page.locator('#checkout-terms-dialog')).not_to_be_visible();button.click();page.keyboard.press('Escape');expect(page.locator('#checkout-terms-dialog')).not_to_be_visible()
    page.screenshot(path=str(OUT/f'local-{engine}-{width}-{lang}-after-refresh.png'),full_page=True);print(json.dumps({'stage':'before-redirect','forms':page.locator('.payment-form').count(),'errors':errors}),flush=True);downloads=[];page.on('download',lambda value:downloads.append(value));page.unroute('**/api/payments/checkout');page.route('**/api/payments/checkout',lambda route:route.fulfill(json={'checkoutUrl':'https://checkout.stripe.com/c/pay/mock','id':'test-only','documentUrl':'/api/payments/order/'+'a'*64+'/documents'}));page.route('https://checkout.stripe.com/**',lambda route:route.fulfill(body='<h1>Isolated provider redirect</h1>',content_type='text/html'))
    page.locator('.payment-form [name=terms]').check();page.locator('.payment-form [type=submit]').click();expect(page.locator('h1')).to_have_text('Isolated provider redirect');assert downloads==[]
    assert not errors,errors;checks.append({'engine':engine,'width':width,'locale':lang,'realServerQuote':True,'editCannotPayOldAddress':True,'retrySameCommand':True,'noOverflow':True,'providerMocked':True});context.close()
   browser.close()
 result={'passed':True,'releaseHash':manifest['releaseHash'],'live':False,'providerTest':False,'scenarios':len(checks),'checks':checks};(OUT/os.environ.get('QA_REPORT','browser.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'scenarios':len(checks),'releaseHash':manifest['releaseHash']}))
finally:
 if 'page'in globals()and not page.is_closed()and __import__('sys').exc_info()[0]:
  try:page.screenshot(path=str(OUT/'browser-failure.png'),full_page=True);(OUT/'browser-failure.html').write_text(page.content(),encoding='utf8')
  except Exception:pass
 if proxy:proxy.terminate();proxy.wait(timeout=10)
 if server:server.terminate();server.wait(timeout=10)
 if log:log.close()
 assert temp.parent.resolve()==Path(tempfile.gettempdir()).resolve()and temp.name.startswith('nodeno-stripe-browser-');shutil.rmtree(temp)
