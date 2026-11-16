#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-returns-public.py
# Açıklama   : Canlı önizlemeye sahte sipariş yazmadan iade girişini, hata odağını ve dil/mahremiyet davranışını sınar.
import hashlib,json,os,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from native_browser_ready import NativePageReadiness
from native_test_errors import safe_error
sys.excepthook=safe_error;ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');scope=os.environ.get('SEXOGATE_MARKETPLACE_SCOPE','local');assert scope in ['local','preview','remote'];assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
folder=ROOT/('docs/screenshots/native-store-returns-public-'+scope);folder.mkdir(parents=True,exist_ok=True);results=[]
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(60000);ready=NativePageReadiness(page,BASE,60000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  try:
   release=context.request.get(BASE+'/api/deployment-status').json()['release'];r=page.goto(BASE+'/?page=return-center&lang=tr');ready.wait();assert 'no-store'in r.headers.get('cache-control','')
   gate=page.locator('.sexogate-age-accept')
   if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
   consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
   if consent.count()and consent.is_visible():consent.click()
   page.locator('[data-return-lookup]').wait_for();ready.wait();expect(page.locator('.sg-returns h1')).to_have_text('Kolay iade');expect(page.locator('meta[name=robots]')).to_have_attribute('content','noindex,nofollow');page.locator('[name=token]').fill('0'*64);page.locator('[data-return-lookup] button').click();expect(page.locator('[data-return-error]')).to_be_focused();assert page.locator('[data-return-select]').count()==0
   page.locator('[name=token]').fill('')
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
   page.goto(BASE+'/?page=return-center&lang=en');ready.wait();page.locator('[data-return-lookup]').wait_for();expect(page.locator('.sg-returns h1')).to_have_text('Easy returns');page.screenshot(path=str(folder/(engine+'-entry-en.png')))
   page.goto(BASE+'/?page=return-center&lang=ar');ready.wait();assert page.locator('html').get_attribute('dir')=='rtl';expect(page.locator('.sg-return-language .button')).to_have_count(2);assert not errors,errors
   results.append({'engine':engine,'base':BASE,'release':release,'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'guestLookupProtected':True,'noOrderDataLeaked':True,'trAndEn':True,'rtlLanguageChoice':True,'noStoreNoindex':True,'fakeOrdersCreated':False,'realRefunds':False,'pageErrors':0});print(json.dumps(results[-1]),flush=True)
  finally:context.close();browser.close()
(ROOT/('.local/native-returns-public-'+scope+'.json')).write_text(json.dumps(results,indent=2),'utf8')
