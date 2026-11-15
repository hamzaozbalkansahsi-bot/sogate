"""Real PHP storefront checks against an immutable supplier release; no remote writes."""
from pathlib import Path
import json,os,subprocess,socket,time,shutil,hashlib,mimetypes
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];release=R/os.environ.get('NODENO_SUPPLIER_RELEASE','artifacts/cpanel-release-suppliers-ready-20261110-r2');O=R/'artifacts/supplier-expansion/publication/browser';O.mkdir(exist_ok=True)
catalog=json.loads((release/'private/catalog.json').read_bytes());products=[p for p in catalog['products']if p.get('productType')=='supplier-item'];assert products
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
local=O/'runtime';local.mkdir(exist_ok=True);(local/'public').mkdir(exist_ok=True);(local/'storage').mkdir(exist_ok=True)
for p in (release/'public').iterdir():
 if p.is_file():shutil.copyfile(p,local/'public'/p.name)
q=lambda p:"'"+p.as_posix().replace("'","\\'")+"'"
(local/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(release/'private')+",'storageRoot'=>"+q(local/'storage')+"];",encoding='utf8')
upstream=port();origin='http://127.0.0.1:'+str(upstream);log=(O/'server.log').open('w');server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(local/'public'),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(local/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
checks=[]
engine=os.environ.get('NODENO_SUPPLIER_ENGINE','chromium');prefix='webkit-'if engine=='webkit'else''
try:
 time.sleep(1)
 with sync_playwright()as pw:
  for width in ([390]if engine=='webkit'else[1440,390]):
   executable=R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'if engine=='webkit'else Path.home()/'AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe';browser=getattr(pw,engine).launch(executable_path=str(executable),headless=True)
   for lang in (['tr','ar']if engine=='webkit'else['tr','en','ru','ar']):
    context=browser.new_context(viewport={'width':width,'height':1000 if width>768 else 844},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def assets(route):
     file=release/'public'/unquote(urlparse(route.request.url).path).lstrip('/')
     if file.is_file():route.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0]or'application/octet-stream')
     else:route.continue_()
    page.route('**/assets/**',assets)
    page.route('**/media/**',lambda route:route.abort())
    page.add_init_script("localStorage.setItem('nodeno.analytics.consent.v1','false');localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'))")
    def visit_product(product):
     page.evaluate("url=>{const a=document.createElement('a');a.href=url;a.dataset.nav='';document.body.appendChild(a);a.click();a.remove();}",origin+'/?lang='+lang+'&product='+product['id'])
     expect(page.locator('#product-title')).to_have_text(product['modelName'][lang])
    item=next(p for p in products if p['salePriceMinor']is not None and p['id'].startswith('altinis'))
    page.goto(origin+'/?lang='+lang+'&product='+item['id'],wait_until='networkidle');expect(page.locator('#product-title')).to_have_text(item['modelName'][lang]);assert page.locator('.gallery-slide img').first.evaluate('(im)=>im.complete&&im.naturalWidth>0');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    if lang=='ar':assert page.locator('html').get_attribute('dir')=='rtl'
    for button in page.locator('#insights-banner .insights-actions button').all():
     if button.is_visible():button.click();break
    assert page.locator('.price-tax-note').first.inner_text().strip()
    if item.get('supplierDetailsHash'):
     response=context.request.get(origin+'/api/supplier-products/'+item['id']);assert response.status==200;detail=response.json();assert detail['sha256']==item['supplierDetailsHash'] and set(detail)=={'id','description','sha256'};assert len(detail['description'][lang])>=len(item['name'][lang]);expect(page.locator('#product-information')).to_contain_text(detail['description'][lang].split('\n')[0][:60])
    page.screenshot(path=str(O/f'{prefix}product-{width}-{lang}.png'),full_page=False)
    body=context.request.get(origin+'/?lang='+lang+'&product='+item['id']).text();assert '/assets/suppliers/'in body and 'application/ld+json'in body
    choices=[p for p in products if p['salePriceMinor']is not None and p['saleUnit']=='length']
    if choices:
     p=choices[0];visit_product(p);assert 'KDV hariç'not in page.locator('.product-price-block').inner_text();assert page.locator('#detail-quantity').get_attribute('step')==str(p['quantityPolicy']['step'])
    if width==390:
     variants=[p for p in products if p.get('variantLabel')and not p.get('variationSelectionRequired')and p['quantityPolicy']['minimum']==3]
     if variants:
      p=variants[0];visit_product(p);expect(page.locator('.supplier-options')).to_be_visible();expect(page.locator('.supplier-options [aria-current=true]')).to_contain_text(p['variantLabel'][lang]);expect(page.locator('#detail-quantity')).to_have_value('3');page.locator('[data-detail-step="3"]').click();expect(page.locator('#detail-quantity')).to_have_value('6');page.screenshot(path=str(O/f'{prefix}variant-{lang}.png'),full_page=False)
    if lang=='tr'and width==1440:
     missing=next((p for p in products if not p['images']),None)
     if missing:visit_product(missing);expect(page.locator('#gallery-viewport .image-fallback')).to_be_visible();assert page.locator('.zoom-hint').count()==0
    assert not errors,errors;checks.append({'width':width,'language':lang,'passed':True});context.close()
   browser.close()
 report={'passed':True,'live':False,'engine':engine,'releaseHash':json.loads((release/'private/release.json').read_bytes())['releaseHash'],'scenarios':checks};(O/('acceptance-webkit.json'if engine=='webkit'else'acceptance.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
finally:server.terminate();server.wait(timeout=10);log.close()

