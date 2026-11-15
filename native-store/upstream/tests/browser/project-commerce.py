"""Real PHP/browser acceptance; customer data is isolated, live mode is read-only."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,socket,sqlite3,subprocess,tempfile,time,datetime
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];OUT=R/'artifacts/project-commerce';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--supplement',action='store_true');parser.add_argument('--release',default='artifacts/cpanel-release-projects-20261110');args=parser.parse_args()
release=R/args.release;manifest=json.loads((release/'private/release.json').read_bytes());catalog=json.loads((release/'private/catalog.json').read_bytes())
front=next(p for p in catalog['products']if p.get('productType')=='cabinet-front'and p['salePriceMinor']and p['front']['material']=='pvc');door=next(p for p in catalog['products']if p.get('productType')=='door'and p['salePriceMinor']and p['door']['finishGroup']!='veneer')
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def quote(p):return "'"+p.as_posix().replace("'","\\'")+"'"
temp=server=proxy=log=None;origin='https://nodenohome.com';checks=[]
try:
 if not args.live:
  temp=Path(tempfile.mkdtemp(prefix='nodeno-project-'));local=temp/'release';shutil.copytree(release,local);storage=temp/'data';storage.mkdir()
  (local/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+quote(local/'private')+",'storageRoot'=>"+quote(storage)+",'mediaRoot'=>"+quote(R/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf8')
  # The offline local FX test uses the unmodified official TCMB bulletin,
  # verified by the production parser, in isolated storage only.
  raw=(R/'artifacts/doors-r4/tcmb-09112026.xml').read_text(encoding='utf8');(temp/'bulletin.xml').write_text(raw,encoding='utf8')
  fixture=temp/'seed.php';fixture.write_text("<?php require "+quote(R/'hosting/exchange-rates.php')+"; $xml=file_get_contents("+quote(temp/'bulletin.xml')+");$fx=nodenoFxBuild(new DateTimeImmutable('now',new DateTimeZone('Europe/Istanbul')),static function($dates)use($xml){$r=[];foreach($dates as $d)$r[$d]=$d==='2026-11-09'?['status'=>200,'body'=>$xml]:['status'=>404];return $r;});file_put_contents("+quote(storage/'exchange-rates-v1.json')+",json_encode($fx));",encoding='utf8')
  subprocess.run([str(R/'artifacts/runtime-php/php.exe'),str(fixture)],check=True,capture_output=True)
  upstream,tls=port(),port();origin='https://127.0.0.1:'+str(tls);log=open(OUT/'browser-server.log','w',encoding='utf8')
  env={**os.environ,'NODENO_TEST_PUBLIC':str(local/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'}
  server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(local/'public'),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  cert,key=temp/'cert.pem',temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);time.sleep(1)
 with sync_playwright()as pw:
  for engine,width in ([('chromium',1440),('chromium',390)]if args.supplement else[('chromium',1440),('chromium',390),('webkit',390)]):
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(pw,engine).launch(executable_path=str(executable))
   try:
    for lang in (['tr']if args.supplement else['tr','en','ru','ar']):
     context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':width,'height':1000 if width>768 else 844},is_mobile=width<768,has_touch=width<768)
     page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');if(!localStorage.getItem('nodeno.delivery-country.v1'))localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'))")
     page.goto(origin+'/?lang='+lang+'&product='+front['id'],wait_until='networkidle');expect(page.locator('.front-configurator')).to_be_visible(timeout=15000)
     necessary=page.locator('#insights-banner .insights-actions button').last
     if necessary.is_visible():necessary.click()
     page.locator('#front-widthMm').fill('500');page.locator('#front-heightMm').fill('1000');page.locator('#front-heightMm').blur()
     page.locator('#detail-quantity').fill('10');page.locator('#detail-quantity').blur();expect(page.locator('.front-calculation')).to_be_visible()
     assert page.locator('.front-calculation').inner_text().find('m²')>=0
     page.locator('.product-buy-actions [data-detail-add]').click();page.goto(origin+'/?lang='+lang+'&page=cart',wait_until='networkidle')
     expect(page.locator('.basket-item')).to_have_count(1);expect(page.locator('.basket-summary a[href*="checkout"]')).to_have_count(1)
     page.reload(wait_until='networkidle');expect(page.locator('.basket-item')).to_have_count(1)
     page.locator('[data-door-country]').select_option('DE');expect(page.locator('.basket-summary a[href*="checkout"]')).to_have_count(0)
     page.locator('[data-cart-quantity]').fill('20');page.locator('[data-cart-quantity]').blur();expect(page.locator('.basket-summary a[href*="checkout"]')).to_have_count(1)
     assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),(engine,width,lang,'horizontal overflow')
     page.screenshot(path=str(OUT/(('live-'if args.live else'local-')+engine+'-'+str(width)+'-'+lang+'-cart.png')),full_page=True)
     # Required dimensions cannot be bypassed through account-free quote API.
     status=context.request.get(origin+'/api/commerce/status');assert status.ok,status.text();csrf=status.json()['csrfToken']
     options={'widthMm':500,'heightMm':1000,'application':'solid'};items=[{'id':front['id'],'quantity':20,'options':options}]
     quote_body={'items':items,'country':'DE','currency':'TRY','priceRevision':(context.request.get(origin+'/api/catalog').json().get('meta',{}).get('controlRevision')or 0)}
     response=context.request.post(origin+'/api/commerce/quote',data=quote_body,headers={'Origin':origin});assert response.ok,response.text();q=response.json();assert q['minimumEligible']and q['frontAreaMm2']==10000000 and q['subtotalTryMinor']==front['salePriceMinor']*10
     forged={**quote_body,'items':[{'id':front['id'],'quantity':20}]};assert context.request.post(origin+'/api/commerce/quote',data=forged,headers={'Origin':origin}).status==422
     if not args.live and engine=='chromium'and width==1440 and lang=='tr':
      body={**quote_body,'contact':{'name':'Local QA','company':'','email':'qa@example.test','phone':'+905551112233','city':'Izmir','note':'Isolated integration test'},'consent':True,'idempotencyKey':'local-qa-idempotency-001','locale':'tr','website':''}
      a=context.request.post(origin+'/api/door-inquiries',data=body,headers={'Origin':origin,'X-CSRF-Token':csrf});assert a.status==201,a.text();b=context.request.post(origin+'/api/door-inquiries',data=body,headers={'Origin':origin,'X-CSRF-Token':csrf});assert b.status==201 and a.json()==b.json(),b.text()
      invalid=context.request.post(origin+'/api/door-inquiries',data=body,headers={'Origin':origin,'X-CSRF-Token':'bad'});assert invalid.status==403
      # Also exercise the visible form and its success state in isolated storage.
      for key,value in {'name':'Browser QA','email':'browser@example.test','phone':'+905551112233','city':'Izmir'}.items():page.locator('#door-contact-'+key).fill(value)
      page.locator('#door-inquiry-form [name=consent]').check();page.locator('#door-inquiry-form [type=submit]').click();expect(page.locator('.door-request-success')).to_be_visible(timeout=15000)
     page.goto(origin+'/?lang='+lang+'&product='+door['id'],wait_until='networkidle');expect(page.locator('.door-configurator')).to_be_visible();page.locator('#door-frameDepth').select_option('19');page.locator('[data-door-option=hardware]').check()
     assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),(engine,width,lang,'door overflow')
     page.screenshot(path=str(OUT/(('live-'if args.live else'local-')+engine+'-'+str(width)+'-'+lang+'-door.png')),full_page=False)
     page.goto(origin+'/?lang='+lang+'&product='+front['id'],wait_until='networkidle');expect(page.locator('.front-configurator')).to_be_visible()
     page.locator('#front-widthMm').fill('600');page.locator('#front-heightMm').fill('1000');page.locator('#front-heightMm').blur();page.screenshot(path=str(OUT/(('live-'if args.live else'local-')+engine+'-'+str(width)+'-'+lang+'-front.png')),full_page=False)
     if args.supplement:
      page.locator('#detail-quantity').fill('5');page.locator('#detail-quantity').blur();page.locator('.product-buy-actions [data-detail-add]').click();page.goto(origin+'/?lang=tr&page=cart',wait_until='networkidle')
      expect(page.locator('.basket-item')).to_have_count(2);inputs=page.locator('[data-cart-quantity]');assert inputs.nth(0).input_value()=='20'and inputs.nth(1).input_value()=='5'
      page.locator('[data-cart-step="1"]').nth(1).click();expect(inputs.nth(1)).to_have_value('6');expect(inputs.nth(0)).to_have_value('20')
      page.locator('[data-select]').first.uncheck();expect(page.locator('.basket-summary a[href*="checkout"]')).to_have_count(0);page.locator('#select-all').check();expect(page.locator('.basket-summary a[href*="checkout"]')).to_have_count(1)
      page.locator('[data-remove]').nth(1).click();expect(page.locator('.basket-item')).to_have_count(1);page.locator('[data-shopping=undo-cart]').click();expect(page.locator('.basket-item')).to_have_count(2)
      page.reload(wait_until='networkidle');expect(page.locator('.basket-item')).to_have_count(2);stored=page.evaluate("JSON.parse(localStorage.getItem('nodeno.cart.v1'))");assert len({row['key']for row in stored})==2 and {row['options']['widthMm']for row in stored}=={500,600}
      page.goto(origin+'/?lang=tr&page=catalog&category=dolap-kapaklari',wait_until='networkidle');expect(page.locator('.front-collection-banner')).to_be_visible();assert page.locator('.front-collection-banner img').evaluate('(e)=>e.complete&&e.naturalWidth>100')
      page.screenshot(path=str(OUT/(('live-'if args.live else'local-')+str(width)+'-front-collection.png')),full_page=False)
      page.goto(origin+'/?lang=tr&page=cart',wait_until='networkidle');page.locator('[data-door-country]').select_option('TR');page.locator('[data-cart-quantity]').first.fill('10');page.locator('[data-cart-quantity]').first.blur()
      page.locator('.basket-summary a[href*="checkout"]').click();page.locator('[data-action=guest-start]').click()
      def fill_guest():
       for key,value in {'name':'Local QA','email':'qa@example.test','phone':'+905551112233','city':'Berlin','line1':'Example Road 123'}.items():page.locator('#guest-checkout-form [name='+key+']').fill(value)
       page.locator('#guest-checkout-form [name=country]').select_option('DE')
      fill_guest();page.locator('#guest-checkout-form [type=submit]').click();expect(page).to_have_url(origin+'/?page=cart&lang=tr');expect(page.locator('[data-door-country]')).to_have_value('DE');expect(page.locator('.basket-summary a[href*="checkout"]')).to_have_count(0)
      page.locator('[data-cart-quantity]').first.fill('20');page.locator('[data-cart-quantity]').first.blur();page.locator('.basket-summary a[href*="checkout"]').click();page.locator('[data-action=guest-start]').click();fill_guest();page.locator('#guest-checkout-form [type=submit]').click();expect(page.locator('.guest-review')).to_be_visible();expect(page.locator('[data-payment-gate]')).to_be_disabled()
      if 'final-'in str(release):
       for frame,accessory in [('front-250fff15de6bc099','front-17bcf6a285283529'),('front-b807c4d2a452c1f2','front-1fde0006feca970b'),('front-e9745d1f27f9110c','front-606bc484113f8191')]:
        page.goto(origin+'/?lang=tr&product='+frame,wait_until='networkidle');expect(page.locator('.front-configurator')).to_be_visible();expect(page.locator('[data-variant="'+accessory+'"]')).to_have_count(0)
     rates=context.request.get(origin+'/api/exchange-rates');assert rates.ok,rates.text();expect(page.locator('#display-currency option[value=USD]')).to_have_count(1);page.locator('#display-currency').select_option('USD');expect(page.locator('.exchange-explanation')).to_be_visible();assert 'USD'in page.locator('#display-currency').input_value()
     assert not errors,(engine,width,lang,errors)
     checks.append({'engine':engine,'width':width,'language':lang,'measurements':True,'areaMinimums':True,'reload':True,'serverQuote':True,'forgedQuoteRejected':True,'currency':True,'viewportFits':True});context.close()
   finally:browser.close()
 if not args.live:
  db=sqlite3.connect(storage/'accounts.sqlite');rows=db.execute("SELECT data_json FROM control_records WHERE resource='doorRequests'").fetchall();assert len(rows)==2,rows
  assert all(json.loads(r[0])['quoteSnapshot']['frontAreaMm2']==10000000 for r in rows);db.close()
 result={'passed':True,'live':args.live,'releaseHash':manifest['releaseHash'],'scenarios':len(checks),'checks':checks,'physicalPhoneTested':False,'paymentEnabled':False}
 (OUT/(('live-supplement.json'if args.live else'local-supplement.json')if args.supplement else'live-acceptance.json'if args.live else'local-acceptance.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:
 if proxy:proxy.terminate();proxy.wait(timeout=10)
 if server:server.terminate();server.wait(timeout=10)
 if log:log.close()
 if temp:
  assert temp.resolve().parent==Path(tempfile.gettempdir()).resolve()and temp.name.startswith('nodeno-project-');shutil.rmtree(temp)
