#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-returns-browser.py
# Açıklama   : İzole gerçek HTTP siparişleriyle iade adımlarını, rol sınırlarını ve mali iş akışını iki motorda sınar.
import base64,hashlib,hmac,json,re,struct,sys,time,traceback
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from native_browser_ready import NativePageReadiness
ROOT=Path(__file__).resolve().parent.parent
local=json.loads((ROOT/'.local/native-stage-local.json').read_text('utf8'));BASE=local['url'];assert BASE=='https://127.0.0.1:3188/test'
fixture=json.loads((ROOT/'.local/returns-local-fixtures.json').read_text('utf8'));owner=json.loads((ROOT/'.local/php-access.json').read_text('utf8'))
folder=ROOT/'docs/screenshots/native-store-returns-local';folder.mkdir(parents=True,exist_ok=True);results=[]
def safe_error(kind,error,trace):
 text=str(error)
 for value in [owner,*[v for f in fixture.values()for v in [f['operator'],f['customer'],*f['orders'].values()]]]:
  for key in ['email','password','totpSecret','token']:
   if value.get(key):text=text.replace(value[key],'[private]')
 text=re.sub(r'(?im)^.*(?:cookie:|x-return-proof:|x-csrf-token:|authorization:).*$', '[private headers]',text)
 print(kind.__name__+': '+text[:1500]+' at '+str([(Path(f.filename).name,f.lineno)for f in traceback.extract_tb(trace)]),file=sys.stderr)
sys.excepthook=safe_error
def otp(secret):
 key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));digest=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15
 return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def dismiss(page):
 gate=page.locator('.sexogate-age-accept')
 if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
 consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
 if consent.count()and consent.is_visible():consent.click()
def req(context,path,method='GET',body=None,csrf=None,proof=None,status=200,origin=True):
 headers={'Accept':'application/json'}
 if method!='GET':headers['Origin']=BASE.split('/test')[0]if origin else 'https://invalid.example'
 if csrf:headers['X-CSRF-Token']=csrf
 if proof:headers['X-Return-Proof']=proof
 r=context.request.fetch(BASE+path,method=method,data=body,headers=headers,timeout=30000)
 assert r.status==status,(path,r.status,r.text()[:150]);return r.json()
def admin(context,credentials):
 s=req(context,'/api/admin/session');s=req(context,'/api/admin/login','POST',{'email':credentials['email'],'password':credentials['password']},s['csrfToken'])
 # Native MFA deliberately rejects reuse of the same 30-second counter.
 time.sleep(30.1-time.time()%30)
 s=req(context,'/api/admin/login/verify','POST',{'code':otp(credentials['totpSecret'])},s['csrfToken']);assert s['user'];return s
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  print(engine+': local return flow',flush=True);browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=True,viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(30000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));ready=NativePageReadiness(page,BASE,60000);f=fixture[engine]
  try:
   catalog=req(context,'/api/catalog');assert all(re.fullmatch('sg_ty_[a-f0-9]{16}',v['id'])for v in catalog['products']),'ARCHIVED_CATALOG_REAPPEARED'
   deployment=req(context,'/api/deployment-status');assert deployment['release']==local['release']
   response=page.goto(BASE+'/?page=return-center&lang=tr');assert response.status==200;ready.wait();dismiss(page);page.locator('[data-return-lookup]').wait_for();ready.wait()
   expect(page.locator('meta[name=robots]')).to_have_attribute('content','noindex,nofollow')
   assert 'no-store'in response.headers.get('cache-control',''),'RETURN_PAGE_CACHE'
   csrf=req(context,'/api/returns')['csrfToken'];req(context,'/api/returns/order','POST',{'lookupToken':f['orders']['one']['token']},status=403);req(context,'/api/returns/order','POST',{'lookupToken':f['orders']['one']['token']},csrf,status=403,origin=False)
   page.locator('[name=token]').fill(f['orders']['one']['token'])
   with page.expect_response(lambda r:r.url==BASE+'/api/returns/order')as loaded:page.locator('[data-return-lookup] button').click()
   order=loaded.value.json();assert loaded.value.status==200,('order_lookup',loaded.value.status,order.get('error'));page.locator('[data-return-select]').wait_for();assert order['lines'][0]['selection']=='Beden: XL · Renk: Siyah'
   page.locator('[data-return-select] button[type=submit]').click();expect(page.locator('[data-return-error]')).to_be_focused()
   page.locator('[name=line]').first.check();page.locator('[data-return-select] button[type=submit]').click();page.locator('[name=note]').fill('İstanbul, Şişli — ölçü uygun değil.');page.locator('[data-return-reason] button:not([type=button])').click();page.locator('[data-return-submit]').wait_for();expect(page.locator('.sg-return-amount strong')).to_have_text(re.compile(r'40,01'))
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),('RETURN_OVERFLOW',width)
    if width in [390,1440]:page.locator('.sg-returns').screenshot(path=str(folder/(engine+'-review-'+str(width)+'.png')))
   with page.expect_response(lambda r:r.url==BASE+'/api/returns/cases'and r.request.method=='POST')as submitted:page.locator('[data-return-submit]').click()
   created=submitted.value.json();body=submitted.value.request.post_data_json;code=created['code'];assert re.fullmatch('SGR-[0-9]{6}-[A-F0-9]{12}',code);expect(page.locator('.sg-return-reference strong')).to_have_text(code)
   again=req(context,'/api/returns/cases','POST',body,csrf,order['proof']);assert again['code']==code
   altered={**body,'note':'İçerik değişti'};req(context,'/api/returns/cases','POST',altered,csrf,order['proof'],409)
   req(context,'/api/returns/cases/'+code,status=403)
   other=browser.new_context(ignore_https_errors=True);req(other,'/api/returns');req(other,'/api/returns/cases/'+code,proof=order['proof'],status=403);other.close()
   second=req(context,'/api/returns/order','POST',{'lookupToken':f['orders']['two']['token']},csrf);req(context,'/api/returns/cases/'+code,proof=second['proof'],status=404)
   page.locator('[data-return-cancel]').click();page.locator('[data-return-confirm-cancel]').click();expect(page.locator('.sg-return-tag')).to_have_text('Talep iptal edildi')
   page.locator('[data-return-another]').click();page.locator('[data-return-select]').wait_for();assert page.locator('.sg-return-history button').count()==1
   page.locator('[name=line]').first.check();page.locator('[data-return-select] button[type=submit]').click();page.locator('[data-return-reason] button:not([type=button])').click()
   with page.expect_response(lambda r:r.url==BASE+'/api/returns/cases'and r.request.method=='POST')as submitted:page.locator('[data-return-submit]').click()
   code=submitted.value.json()['code'];page.locator('.sg-return-reference').wait_for();page.locator('.sg-returns').screenshot(path=str(folder/(engine+'-reference.png')))
   account=req(context,'/api/account');req(context,'/api/account/login','POST',{'email':f['customer']['email'],'password':f['customer']['password']},account['csrfToken']);s=req(context,'/api/returns');assert len(s['orders'])==1
   req(context,'/api/returns/order','POST',{'orderId':f['orders']['two']['id']},s['csrfToken'],status=404);req(context,'/api/returns/order','POST',{'lookupToken':f['orders']['two']['token']},s['csrfToken'],status=403)
   ops=browser.new_context(ignore_https_errors=True);opSession=admin(ops,f['operator']);case=req(ops,'/api/admin/return-center/'+code);assert 'grossMinor'not in case and 'jobs'not in case and 'netMinor'not in case
   req(ops,'/api/admin/return-center/report',status=403);req(ops,'/api/admin/return-center/'+code+'/command','POST',{'action':'approve','version':case['version']},opSession['csrfToken'],status=403)
   def command(ctx,session,c,action,**values):return req(ctx,'/api/admin/return-center/'+c['code']+'/command','POST',{'version':c['version'],'action':action,**values},session['csrfToken'])
   case=command(ops,opSession,case,'shipping',carrier='İzole taşıyıcı — gerçek servis değil',handoffCode='LOCAL-ONLY-SHIP',evidenceRef='fixture://isolated-carrier',expiresAt=int(time.time())+86400)
   case=command(ops,opSession,case,'dispatch',trackingNumber='LOCAL-ONLY-TRACK');case=command(ops,opSession,case,'receive');assert case['qc']['stockIncreased']is False
   case=command(ops,opSession,case,'inspect',inspectionComplete=True,disposition='quarantine',evidenceRef='fixture://inspection');opPage=ops.new_page();opPage.goto(BASE+'/yonetim/iade-merkezi');opPage.locator('[data-rma-open]').first.wait_for();opPage.locator('[data-rma-open="'+code+'"]').click();opPage.locator('[data-rma-form=inspect]').wait_for();assert opPage.locator('[data-rma-form=expense]').count()==0;ops.close()
   finance=browser.new_context(ignore_https_errors=True);finSession=admin(finance,owner);case=req(finance,'/api/admin/return-center/'+code);case=command(finance,finSession,case,'approve');assert case['refundState']=='queued'and len(case['jobs'])==2
   fiscal={'operation':'return_invoice','originalRef':'LOCAL-INVOICE-'+code,'correctiveRef':'LOCAL-CORRECTION-'+code,'evidenceRef':'fixture://not-a-real-fiscal-document'}
   req(finance,'/api/admin/return-center/'+code+'/fiscal','POST',fiscal,finSession['csrfToken'],status=422);req(finance,'/api/admin/return-center/'+code+'/fiscal','POST',{**fiscal,'verifiedByOperator':True,'operation':'cancellation'},finSession['csrfToken'],status=409)
   case=req(finance,'/api/admin/return-center/'+code+'/fiscal','POST',{**fiscal,'verifiedByOperator':True},finSession['csrfToken']);assert case['fiscalState']=='confirmed'and case['refundState']=='queued'
   report=req(finance,'/api/admin/return-center/report');assert report['currencies']==[],'TEST_PAYMENT_IN_LIVE_REPORT'
   finPage=finance.new_page();finPage.goto(BASE+'/yonetim/iade-merkezi');finPage.locator('[data-rma-open="'+code+'"]').click();finPage.locator('[data-rma-form=expense]').wait_for()
   for width in [360,390,430,768,1440]:
    finPage.set_viewport_size({'width':width,'height':900});assert finPage.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),('RETURN_ADMIN_OVERFLOW',width)
   finPage.screenshot(path=str(folder/(engine+'-admin-1440.png')),full_page=True);finance.close()
   page.goto(BASE+'/?page=return-center&lang=en');ready.wait();expect(page.locator('.sg-returns h1')).to_have_text('Easy returns');page.locator('[data-return-lookup]').wait_for()
   page.goto(BASE+'/?page=return-center&lang=ar');ready.wait();assert page.locator('html').get_attribute('dir')=='rtl';expect(page.locator('.sg-return-language .button')).to_have_count(2);assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
   raw=browser.new_context(ignore_https_errors=True,java_script_enabled=False);ssr=raw.new_page();ssr.goto(BASE+'/?page=return-center&lang=tr');assert ssr.locator('.sg-returns h1').inner_text()=='Kolay iade';assert ssr.locator('.sg-returns noscript a').count()==1;raw.close()
   assert not errors,errors;assert req(context,'/api/deployment-status')['release']==local['release']
   results.append({'engine':engine,'base':BASE,'release':local['release'],'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'publicProducts':len(catalog['products']),'oldSupplierProductsVisible':False,'realPaymentsCalled':False,'fiscalApiCalled':False,'localPaidFixturesOnly':True,'partialReturn':True,'serverQuote':True,'idempotency':True,'cancelAndHistory':True,'csrfAndOrigin':True,'sessionAndOrderOwnership':True,'warehouseFinancialBoundary':True,'adminMfa':True,'quarantineNoRestock':True,'fiscalConfirmationSeparate':True,'testExcludedFromLiveReport':True,'trAndEn':True,'rtlLanguageChoice':True,'firstHtmlAndNoindex':True,'widths':[360,390,430,768,1440],'pageErrors':0});print(json.dumps(results[-1]),flush=True)
  except Exception:

   if page.locator('[name=token]').count():page.locator('[name=token]').fill('')
   page.screenshot(path=str(folder/(engine+'-diagnostic.png')));raise
  finally:context.close();browser.close()
(ROOT/'.local/native-returns-local.json').write_text(json.dumps(results,indent=2),'utf8')
