#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-browser.py
# Açıklama   : Doğrudan kopyanın gerçek HTTPS/MFA yönetimini ve özgün müşteri ekranlarını sınar.
import argparse,base64,hashlib,hmac,json,os,re,struct,sys,time
from urllib.parse import urlsplit
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_browser_ready import NativePageReadiness

ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3186').rstrip('/');scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','local');assert re.fullmatch('[a-z-]+',scope)
assert BASE in ['https://127.0.0.1:3186','https://127.0.0.1:3188/test','https://sexogate.com/test'] or re.fullmatch('https://(?:sexogate.com|127.0.0.1:3188)/test/native-preview-[a-f0-9]{16}',BASE)
access_name='php-stage-access.json' if BASE.startswith('https://sexogate.com') else 'php-access.json';access=json.loads((ROOT/'.local'/access_name).read_text('utf8'));folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--branding-only',action='store_true');parser.add_argument('--release-smoke',action='store_true');args=parser.parse_args()
def safe_error(kind,error,trace):
 message=str(error)
 for name in ['password','totpSecret','email']:
  if access.get(name):message=message.replace(access[name],'[redacted]')
 message=re.sub(r'^.*(?:cookie:|authorization:|x-csrf-token:).*$','[private request headers redacted]',message,flags=re.M|re.I)
 print(kind.__name__+': '+message[:1600],file=sys.stderr)
sys.excepthook=safe_error
def otp(secret):
 key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));digest=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15;return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def dismiss(page):
 age=page.locator('#sexogate-age-gate')
 if age.count() and age.is_visible():age.locator('.sexogate-age-accept').click()
 for text in ['Mağazayı keşfet','Yalnız gerekli']:
  button=page.get_by_role('button',name=text,exact=True)
  if button.count() and button.first.is_visible():button.first.click()
def admin_route(page,route):
 started=time.monotonic();url=BASE+'/yonetim'+route;key=route.lstrip('#').split('?',1)[0];print(json.dumps({'adminRoute':route,'started':True}),flush=True)
 if page.url!=url:
  if key=='guide':page.goto(url)
  else:
   endpoint=BASE+'/api/admin/'+{'social':'social/overview','integrations':'system'}.get(key,key)
   with page.expect_response(lambda r:r.url==endpoint and r.request.method=='GET') as result:page.goto(url)
   assert result.value.status==200,(route,result.value.status)
 page.locator('#main .loading').wait_for(state='detached');print(json.dumps({'adminRoute':route,'seconds':round(time.monotonic()-started,2)}),flush=True);assert 'Kayıtlar alınamadı' not in page.locator('#main').inner_text(),route

results=[]
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':1440,'height':950});page=context.new_page();page.set_default_timeout(60000 if BASE.startswith('https://sexogate.com')else 20000);page.set_default_navigation_timeout(60000 if BASE.startswith('https://sexogate.com') else 60000);errors=[];external=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if not r.url.startswith(BASE) and r.url.startswith(('http:','https:')) else None)
  readiness=NativePageReadiness(page,BASE,timeout=60000 if BASE.startswith('https://sexogate.com')else 20000)
  pending=set();page.on('request',lambda request:pending.add(request));page.on('requestfinished',lambda request:pending.discard(request));page.on('requestfailed',lambda request:pending.discard(request))
  try:
   tested_release=context.request.get(BASE+'/api/deployment-status').json()['release']if '/test'in BASE else None
   page.goto(BASE+'/yonetim');readiness.wait();page.locator('[name=email]').fill(access['email']);page.locator('[name=password]').fill(access['password']);page.get_by_role('button',name='Devam et',exact=True).click();page.locator('#verify').wait_for();time.sleep(30.5-time.time()%30);page.locator('[name=proof]').fill(otp(access['totpSecret']));page.locator('#verify button[type=submit]').click();page.locator('.sidebar').wait_for(state='attached');page.locator('#verify').wait_for(state='detached');readiness.wait()
   cookies=context.cookies();assert any(c['name'].startswith('__Host-') and c['secure'] and c['httpOnly'] for c in cookies)
   routes=page.locator('.sidebar a[href^="#"]').evaluate_all('(nodes)=>[...new Set(nodes.map(n=>n.getAttribute("href")))]');assert len(routes)>=20,routes
   if args.branding_only or args.release_smoke:routes=['#products']
   for route in routes:
    admin_route(page,route);assert page.evaluate('() => document.documentElement.scrollWidth<=innerWidth'),route
   print(json.dumps({'engine':engine,'adminNavigationChecked':len(routes)}),flush=True)
   admin_route(page,'#products');assert page.evaluate('() => getComputedStyle(document.querySelector(".sidebar")).backgroundColor')=='rgb(90, 10, 32)';assert 'nodenohome' not in page.locator('.topbar').inner_text();page.screenshot(path=str(folder/(engine+'-admin-desktop.png')),full_page=True)
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});assert page.evaluate('() => document.documentElement.scrollWidth<=innerWidth'),('admin',width)
   page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(folder/(engine+'-admin-mobile.png')),full_page=True)
   public=[]
   paths=['/blog'] if args.branding_only else ['/','/?page=categories','/?page=cart','/?page=favorites','/?page=collections','/?page=compare','/?page=account','/blog','/yonetim/blog']
   for path in paths:
    route_started=time.monotonic();print(json.dumps({'engine':engine,'publicRoute':path}),flush=True)
    response=page.goto(BASE+path);assert response.status==200,(path,response.status);readiness.wait();dismiss(page)
    for width in [360,390,430,768,1440]:
     page.set_viewport_size({'width':width,'height':900});assert page.evaluate('() => document.documentElement.scrollWidth<=innerWidth'),(path,width)
    page.set_viewport_size({'width':390,'height':844})
    if path in ['/blog','/?page=categories','/yonetim/blog']:page.screenshot(path=str(folder/(engine+'-'+{'/blog':'blog','/?page=categories':'categories','/yonetim/blog':'blog-admin'}[path]+'.png')),full_page=True)
    public.append(path);print(json.dumps({'engine':engine,'publicRoute':path,'seconds':round(time.monotonic()-route_started,2)}),flush=True)
   assert not errors,errors;assert not external,external
   if tested_release:assert context.request.get(BASE+'/api/deployment-status').json()['release']==tested_release,'RELEASE_CHANGED_DURING_TEST'
   results.append({'engine':engine,'release':tested_release,'scope':'release-smoke' if args.release_smoke else 'brand-overrides' if args.branding_only else 'full-navigation','base':BASE,'adminRoutes':len(routes),'publicRoutes':len(public),'widths':[360,390,430,768,1440],'mfa':True,'secureCookie':True,'pageErrors':0,'externalRequests':0,'readiness':'critical_requests_and_rendered_ui','optionalFxObserved':readiness.optional_observed,'sourceSnapshotPreserved':True,'domainAndMountRelocated':BASE.endswith('/test') or '/native-preview-' in BASE});print(json.dumps(results[-1]),flush=True)
  except Exception:
   try:print(json.dumps({'diagnostic':True,'engine':engine,'path':urlsplit(page.url).path,'pending':[{'path':urlsplit(request.url).path,'type':request.resource_type}for request in pending],'pageErrors':errors,'ready':page.evaluate('()=>({document:document.readyState,currency:!!document.querySelector("#display-currency"),loading:!!document.querySelector("main .loading,main .loading-state")})')},ensure_ascii=False),flush=True)
   except Exception:print('Navigation diagnostic unavailable',flush=True)
   raise
  finally:context.close();browser.close()
(ROOT/('.local/native-browser'+('-branding' if args.branding_only else '')+('' if scope=='local' else '-'+scope)+'.json')).write_text(json.dumps(results,indent=2),encoding='utf8')
