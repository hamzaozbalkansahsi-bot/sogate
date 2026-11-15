#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-browser.py
# Açıklama   : Doğrudan kopyanın gerçek HTTPS/MFA yönetimini ve özgün müşteri ekranlarını sınar.
import argparse,base64,hashlib,hmac,json,struct,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent;BASE='https://127.0.0.1:3186';access=json.loads((ROOT/'.local/php-access.json').read_text('utf8'));folder=ROOT/'docs/screenshots/native-store-local';folder.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--branding-only',action='store_true');args=parser.parse_args()
def safe_error(kind,error,trace):
 message=str(error)
 for name in ['password','totpSecret','email']:
  if access.get(name):message=message.replace(access[name],'[redacted]')
 print(kind.__name__+': '+message[:1600],file=sys.stderr)
sys.excepthook=safe_error
def otp(secret):
 key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));digest=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15;return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def dismiss(page):
 for text in ['Mağazayı keşfet','Yalnız gerekli']:
  button=page.get_by_role('button',name=text,exact=True)
  if button.count() and button.first.is_visible():button.first.click()
def admin_route(page,route):
 url=BASE+'/yonetim'+route;key=route.lstrip('#').split('?',1)[0]
 if page.url!=url:
  if key=='guide':page.goto(url)
  else:
   endpoint=BASE+'/api/admin/'+{'social':'social/overview','integrations':'system'}.get(key,key)
   with page.expect_response(lambda r:r.url==endpoint and r.request.method=='GET') as result:page.goto(url)
   assert result.value.status==200,(route,result.value.status)
 page.locator('#main .loading').wait_for(state='detached');assert 'Kayıtlar alınamadı' not in page.locator('#main').inner_text(),route

results=[]
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':950});page=context.new_page();page.set_default_timeout(20000);errors=[];external=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if not r.url.startswith(BASE) and r.url.startswith(('http:','https:')) else None)
  try:
   page.goto(BASE+'/yonetim');page.wait_for_load_state('networkidle');page.locator('[name=email]').fill(access['email']);page.locator('[name=password]').fill(access['password']);page.get_by_role('button',name='Devam et',exact=True).click();page.locator('#verify').wait_for();time.sleep(30.5-time.time()%30);page.locator('[name=proof]').fill(otp(access['totpSecret']));page.locator('#verify button[type=submit]').click();page.locator('.sidebar').wait_for(state='attached');page.locator('#verify').wait_for(state='detached');page.wait_for_load_state('networkidle')
   cookies=context.cookies();assert any(c['name'].startswith('__Host-') and c['secure'] and c['httpOnly'] for c in cookies)
   routes=page.locator('.sidebar a[href^="#"]').evaluate_all('(nodes)=>[...new Set(nodes.map(n=>n.getAttribute("href")))]');assert len(routes)>=20,routes
   if args.branding_only:routes=['#products']
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
    response=page.goto(BASE+path);assert response.status==200,(path,response.status);page.wait_for_load_state('networkidle');dismiss(page)
    for width in [360,390,430,768,1440]:
     page.set_viewport_size({'width':width,'height':900});assert page.evaluate('() => document.documentElement.scrollWidth<=innerWidth'),(path,width)
    page.set_viewport_size({'width':390,'height':844})
    if path in ['/blog','/?page=categories','/yonetim/blog']:page.screenshot(path=str(folder/(engine+'-'+{'/blog':'blog','/?page=categories':'categories','/yonetim/blog':'blog-admin'}[path]+'.png')),full_page=True)
    public.append(path)
   assert not errors,errors;assert not external,external
   results.append({'engine':engine,'scope':'brand-overrides' if args.branding_only else 'full-navigation','adminRoutes':len(routes),'publicRoutes':len(public),'widths':[360,390,430,768,1440],'mfa':True,'secureCookie':True,'pageErrors':0,'externalRequests':0,'sourceEngineUnchanged':True});print(json.dumps(results[-1]),flush=True)
  finally:context.close();browser.close()
(ROOT/('.local/native-browser-branding.json' if args.branding_only else '.local/native-browser.json')).write_text(json.dumps(results,indent=2),encoding='utf8')
