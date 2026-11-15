"""Read-only production acceptance; never posts a buyer inquiry or creates an owner."""
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,urllib.request,urllib.error,ssl
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/wholesale-qa';OUT.mkdir(exist_ok=True)
release=json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text(encoding='utf-8'));expected=release['releaseHash']
class Head(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.meta={};self.lang=''
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='link':self.links.append(a)
  if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content')
  if tag=='html':self.lang=a.get('lang')
class Response:
 def __init__(self,response):self.status_code=response.status;self.url=response.url;self.content=response.read();self.text=self.content.decode('utf-8')
 def json(self):return json.loads(self.content)
 def raise_for_status(self):assert self.status_code<400,(self.url,self.status_code)
class ReadOnlySession:
 def get(self,url,timeout=30):
  try:
   with urllib.request.urlopen(url,timeout=timeout,context=ssl.create_default_context()) as r:return Response(r)
  except urllib.error.HTTPError as r:return Response(r)
session=ReadOnlySession();domains=['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'];checks=[]
for domain in domains:
 origin='https://'+domain;health=session.get(origin+'/api/health',timeout=40);health.raise_for_status();assert health.json()['releaseHash']==expected
 info=session.get(origin+'/api/wholesale',timeout=30);info.raise_for_status();data=info.json();assert data['checkoutEnabled'] is False;assert 'TR' not in data['countries'];assert 'US' in data['countries'];assert set(data)=={'revision','compositionVersion','products','countries','checkoutEnabled'}
 for lang in ['tr','en','ru','ar']:
  r=session.get(origin+'/?page=wholesale&lang='+lang,timeout=30);r.raise_for_status();assert r.url.startswith(origin+'/');h=Head();h.feed(r.text);canonical='https://nodenohome.com/?lang='+lang+'&page=wholesale';assert any(v.get('rel')=='canonical' and v.get('href')==canonical for v in h.links);assert h.lang==lang;assert h.meta['robots'].startswith('index,follow');assert len([v for v in h.links if v.get('hreflang')])==5;assert '"@type":"Service"' in r.text;assert '/media/' in r.text;assert 'wholesale.css?v=nodeno-sets-20261101-r1' in r.text
 for path in ['/wholesale.php','/private/wholesale.php','/api/admin/wholesaleRequests','/api/admin/wholesaleRequests/rfq_missing','/api/wholesale/inquiries','/api/wholesale/inquiries/rfq_missing']:
  r=session.get(origin+path,timeout=30);assert r.status_code in (401,403,404,405),(path,r.status_code);assert '<?php' not in r.text;assert 'buyer@example.test' not in r.text
 checks.append({'domain':domain,'trustedHTTPS':True,'locales':4,'privateBoundaries':6})
for lang in ['tr','en','ru','ar']:
 r=session.get('https://nodenohome.com/sitemap-pages-'+lang+'.xml',timeout=30);r.raise_for_status();assert 'page=wholesale' in r.text
for asset in ['app.js','wholesale.js','wholesale-i18n.js','wholesale.css','seo-core.js','seo-ui.js','admin.js','admin.html']:
 r=session.get('https://nodenohome.com/'+asset+'?wholesale-acceptance='+expected[:12],timeout=30);r.raise_for_status();assert hashlib.sha256(r.content).hexdigest()==release['files']['public/'+asset]
admin=session.get('https://nodenohome.com/yonetim',timeout=30);admin.raise_for_status();assert '/admin.js?v=20261101-sets-r1' in admin.text
with sync_playwright() as p:
 executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe';browser=p.chromium.launch(executable_path=str(executable));context=browser.new_context(viewport={'width':1440,'height':1050});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 try:
  for lang in ['tr','en','ru','ar']:
   page.goto('https://nodenohome.com/?page=wholesale&lang='+lang,wait_until='networkidle');expect(page.locator('#wholesale-form')).to_be_visible();assert page.locator('link[rel=canonical]').get_attribute('href')=='https://nodenohome.com/?lang='+lang+'&page=wholesale';assert page.locator('html').get_attribute('dir')==('rtl' if lang=='ar' else 'ltr');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   if lang=='tr':
    necessary=page.get_by_role('button',name='Yalnız gerekli',exact=True)
    if necessary.is_visible():necessary.click()
    page.screenshot(path=str(OUT/'live-wholesale-desktop.png'))
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(OUT/('live-wholesale-'+lang+'-mobile.png')));page.set_viewport_size({'width':1440,'height':1050})
  page.goto('https://nodenohome.com/?page=wholesale&lang=tr',wait_until='networkidle');page.locator('[data-wholesale-add]').first.click();page.locator('[data-wholesale-quantity]').fill('2');page.set_viewport_size({'width':390,'height':844});page.locator('[data-wholesale-line]').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'live-wholesale-quote-mobile.png'));assert not errors,errors
 finally:browser.close()
result={'passed':True,'releaseHash':expected,'domains':checks,'liveLocales':4,'liveInquiryPost':False,'realOwnerCreated':False,'errors':errors};(OUT/'live-acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
