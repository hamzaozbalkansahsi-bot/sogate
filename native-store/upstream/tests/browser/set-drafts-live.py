"""Production checks use anonymous local baskets only; never create real buyer or RFQ records."""
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,urllib.request,urllib.error,ssl
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/set-drafts';OUT.mkdir(exist_ok=True);release=json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text(encoding='utf-8'))
def get(url):
 try:
  with urllib.request.urlopen(url,timeout=40,context=ssl.create_default_context()) as r:return r.status,r.read(),r.url
 except urllib.error.HTTPError as r:return r.status,r.read(),r.url
class Head(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.meta={};self.lang=''
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='link':self.links.append(a)
  if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content')
  if tag=='html':self.lang=a.get('lang')
domains=['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'];checks=[]
for domain in domains:
 origin='https://'+domain;status,body,url=get(origin+'/api/health');assert status==200;assert json.loads(body)['releaseHash']==release['releaseHash']
 status,body,url=get(origin+'/api/catalog');assert status==200;catalog=json.loads(body);assert len(catalog['furnitureSets'])==17;assert next(p for p in catalog['products'] if p['id']=='4883')['saleUnit']=='set';assert next(p for p in catalog['products'] if p['id']=='4911')['saleUnit']=='piece'
 for lang in ['tr','en','ru','ar']:
  for suffix in ['', '&set=bohera-bedroom']:
   status,body,url=get(origin+'/?page=sets&lang='+lang+suffix);assert status==200;assert url.startswith(origin+'/');text=body.decode();h=Head();h.feed(text);canonical='https://nodenohome.com/?lang='+lang+'&page=sets'+suffix;assert h.lang==lang;assert any(l.get('rel')=='canonical' and l.get('href')==canonical for l in h.links);assert len([l for l in h.links if l.get('hreflang')])==5;assert h.meta['robots'].startswith('index,follow');assert '/media/' in text;assert '"@type":"CollectionPage"' in text
  status,body,url=get(origin+'/?page=wholesale&lang='+lang);assert status==200;assert 'furniture-sets' in body.decode() or 'furniture' in body.decode()
 for path in ['/furniture-sets.php','/private/furniture-sets.php','/data/furniture-sets.json','/api/admin/wholesaleRequests','/api/admin/wholesaleRequests/rfq_missing','/api/wholesale/inquiries']:
  status,body,url=get(origin+path);assert status in [401,403,404,405],(path,status);assert b'<?php' not in body
 status,body,url=get(origin+'/?page=sets&set=missing');assert status==404
 checks.append({'domain':domain,'trustedHTTPS':True,'locales':4,'privateBoundaries':6})
for lang in ['tr','en','ru','ar']:
 status,body,url=get('https://nodenohome.com/sitemap-pages-'+lang+'.xml');assert status==200;assert b'page=sets' in body and b'set=bohera-bedroom' in body
for asset in ['app.js','furniture-sets.js','furniture-drafts.js','furniture-set-core.js','furniture-set-i18n.js','furniture-sets.css','wholesale.js','wholesale-i18n.js','seo-core.js','seo-ui.js','admin.js','admin.html']:
 status,body,url=get('https://nodenohome.com/'+asset+'?sets-acceptance='+release['releaseHash'][:12]);assert status==200;assert hashlib.sha256(body).hexdigest()==release['files']['public/'+asset]
with sync_playwright() as p:
 executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe';browser=p.chromium.launch(executable_path=str(executable));context=browser.new_context(viewport={'width':1440,'height':1050});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(e.stack))
 try:
  page.goto('https://nodenohome.com/?page=sets&lang=en',wait_until='networkidle');expect(page.locator('.furniture-set-card')).to_have_count(17);necessary=page.get_by_role('button',name='Necessary only',exact=True)
  if necessary.is_visible():necessary.click()
  for lang in ['tr','en','ru','ar']:
   page.goto('https://nodenohome.com/?page=sets&set=bohera-bedroom&lang='+lang,wait_until='networkidle');expect(page.locator('[data-set-collection]')).to_be_visible();assert page.locator('html').get_attribute('dir')==('rtl' if lang=='ar' else 'ltr');page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(OUT/('live-'+lang+'-mobile.png')));page.set_viewport_size({'width':1440,'height':1050})
  page.goto('https://nodenohome.com/?page=sets&set=bohera-bedroom&lang=tr',wait_until='networkidle')
  for sku,quantity in [('4907',1),('4911',2),('4915',1)]:
   row=page.locator('[data-set-model=model-'+sku+']');row.locator('[data-set-include]').check();row.locator('[data-set-quantity]').fill(str(quantity));row.locator('[data-set-quantity]').dispatch_event('change')
  page.reload(wait_until='networkidle');expect(page.locator('[data-set-model=model-4911] [data-set-quantity]')).to_have_value('2');expect(page.locator('[data-set-draft-notice]')).to_be_visible();page.locator('[data-set-collection]').select_option('madeira-bedroom');page.locator('[data-set-collection]').select_option('bohera-bedroom');expect(page.locator('[data-set-model=model-4911] [data-set-quantity]')).to_have_value('2');page.locator('[data-set-model=model-4911] .furniture-part-photo').click();page.locator('.product-set-entry a').click();expect(page.locator('[data-set-model=model-4911] [data-set-quantity]')).to_have_value('2');page.locator('[data-set-model=model-4911] [data-set-step="1"]').click();expect(page.locator('[data-set-model=model-4911] [data-set-quantity]')).to_have_value('3');page.locator('[data-set-model=model-4911] [data-set-step="-1"]').click();expect(page.locator('[data-set-model=model-4911] [data-set-quantity]')).to_have_value('2');page.locator('[data-set-model=model-4911] [data-set-quantity]').fill('');page.reload(wait_until='networkidle');expect(page.locator('[data-set-model=model-4911] [data-set-quantity]')).to_have_value('2')
  expect(page.locator('[data-set-model=model-4910] [data-set-include]')).not_to_be_checked();page.evaluate("document.activeElement?.blur();window.scrollTo({top:0,left:0,behavior:'instant'})");page.screenshot(path=str(OUT/'live-builder-desktop.png'),full_page=True);page.set_viewport_size({'width':390,'height':844});page.locator('[data-set-model=model-4911]').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'live-selection-mobile.png'));page.locator('[data-set-commit]').click();assert {i['id']:i['quantity'] for i in page.evaluate("JSON.parse(localStorage.getItem('nodeno.cart.v1'))")}=={'4907':1,'4911':2,'4915':1}
  page.goto('https://nodenohome.com/?page=sets&set=bohera-bedroom&lang=tr',wait_until='networkidle');expect(page.locator('[data-set-include]:checked')).to_have_count(0);expect(page.locator('[data-set-commit]')).to_be_disabled()
  page.goto('https://nodenohome.com/?page=sets&set=bohera-bedroom&mode=wholesale&lang=en',wait_until='networkidle');assert all('TRY' not in price and '₺' not in price for price in page.locator('.furniture-part-price').all_inner_texts());select_row=page.locator('[data-set-model=model-4911]');select_row.locator('[data-set-include]').check();page.locator('[data-set-repeat]').fill('10');page.reload(wait_until='networkidle');expect(page.locator('[data-set-repeat]')).to_have_value('10');page.locator('.furniture-mode a').first.click();expect(page.locator('[data-set-repeat]')).to_have_value('1');expect(page.locator('[data-set-include]:checked')).to_have_count(0);assert not errors,errors
 finally:browser.close()
result={'passed':True,'releaseHash':release['releaseHash'],'domains':checks,'roomCount':17,'guestCart':{'4907':1,'4911':2,'4915':1},'excludedBed':True,'liveInquiryPost':False,'realCustomerCreated':False,'draftRefresh':True,'collectionReturn':True,'productReturn':True,'invalidEditRetained':True,'modeIsolation':True,'clearAfterAdd':True,'errors':errors};(OUT/'live-acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
