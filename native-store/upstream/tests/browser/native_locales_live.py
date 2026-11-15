"""Read-only acceptance of the published locale release; no orders or charges."""
from pathlib import Path
import hashlib,json,os,urllib.request
from playwright.sync_api import sync_playwright,expect
from supplier_details_recovery import verify_recovery
R=Path(__file__).resolve().parents[2];E=Path(os.environ.get('NODENO_LIVE_EVIDENCE',str(R/'artifacts/target-locales-20261111')));proof=json.loads((E/'release.json').read_bytes());origin='https://nodenohome.com'
locales=['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'];domains=['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'];domainsPassed=[];checks=[]
def read(url):
 with urllib.request.urlopen(url,timeout=60)as response:return response.read()
for domain in domains:
 health=json.loads(read('https://'+domain+'/api/health'));status=json.loads(read('https://'+domain+'/api/payments/status'))
 assert health['status']=='ok'and health['releaseHash']==proof['releaseHash']and health['checkoutEnabled']and health['mediaReady']
 assert status['enabled']and not status['test']and status['seller']['termsVersion']=='2026-11-10.3'
 domainsPassed.append(domain);print(json.dumps({'domainPassed':domain}),flush=True)
for locale in locales:
 body=read(origin+'/?lang='+locale+'&product=5015').decode('utf8');legal=read(origin+'/legal/kvkk?lang='+locale).decode('utf8')
 assert 'lang="'+locale+'"'in body[:1000]and 'lang="'+locale+'"'in legal[:1000]
 assert 'dir="'+('rtl'if locale in ['ar','fa']else'ltr')+'"'in body[:1000]
 if locale not in ['tr','en','ru','ar']:
  for suffix in ['', '.catalogue']:
   filename=locale+suffix+'.json';expected=(R/proof['release']/'public/locales'/filename).read_bytes();actual=read(origin+'/locales/'+filename+'?v=target-locales-20261111-r1')
   assert hashlib.sha256(actual).digest()==hashlib.sha256(expected).digest(),filename
 print(json.dumps({'nativeSsrAndLegalPassed':locale}),flush=True)
sitemap=read(origin+'/sitemap.xml').decode('utf8')
assert all('sitemap-products-'+locale+'.xml'in sitemap and 'sitemap-pages-'+locale+'.xml'in sitemap for locale in locales)
catalog=json.loads((R/proof['release']/'private/catalog.json').read_bytes())
supplier=next(p for p in catalog['products']if p.get('productType')=='supplier-item'and p['code'].startswith('ND-ALT'))
detail=json.loads(read(origin+'/api/supplier-products/'+supplier['id']))['description']
with sync_playwright()as pw:
 for engine,width,locale,currency in [('chromium',390,'tr','TRY'),('chromium',1440,'de','EUR'),('webkit',320,'fa','USD')]:
  exe=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  browser=getattr(pw,engine).launch(headless=True,executable_path=str(exe));context=browser.new_context(viewport={'width':width,'height':950},is_mobile=width<768,has_touch=width<768,reduced_motion='reduce');page=context.new_page();page.set_default_timeout(45000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false')")
  page.route('**/*',lambda route:route.continue_()if route.request.method in ['GET','HEAD']else route.abort())
  page.goto(origin+'/?lang='+locale,wait_until='networkidle');expect(page.locator('#language')).to_have_value(locale);expect(page.locator('#display-currency')).to_have_value(currency)
  def photos(root):
   page.wait_for_function("""root=>{const visible=[...root.querySelectorAll('img')].filter(img=>{const r=img.getBoundingClientRect();return r.width>0&&r.height>0&&r.right>0&&r.left<innerWidth&&r.bottom>0&&r.top<innerHeight});return visible.length>0&&visible.every(img=>img.complete&&img.naturalWidth>1)}""",arg=root.element_handle())
  photos(page.locator('[data-home-vitrine]'));page.screenshot(path=str(E/('live-home-'+locale+'-'+str(width)+'.png')))
  shelf=page.locator('#product-shelf-storageIdeas');shelf.evaluate('(e)=>scrollTo({top:e.getBoundingClientRect().top+scrollY-document.querySelector(".store-header").getBoundingClientRect().height-16,behavior:"instant"})');photos(shelf)
  first=shelf.locator('.product-card').first;assert first.evaluate('(c)=>{const h=c.querySelector("h3").getBoundingClientRect(),v=c.querySelector(".card-color").getBoundingClientRect();return v.top-h.bottom<18&&h.height<60}')
  assert first.locator('.card-price-main').evaluate('(e)=>e.getBoundingClientRect().height<30&&e.querySelector(".price-unit").textContent.includes("m²")')
  if width<768:assert page.locator('.quick-open:visible').count()==0
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not errors,errors
  page.screenshot(path=str(E/('live-cards-'+locale+'-'+str(width)+'.png')))
  translations={k:v for suffix in ['', '.catalogue']for k,v in json.loads((R/proof['release']/('public/locales/'+locale+suffix+'.json')).read_bytes())['translations'].items()}if locale not in ['tr','en','ru','ar']else{}
  target=detail.get(locale)or translations[detail['en']];paragraph=next(p.strip()for p in target.split('\n\n')if len(p.strip())>80)
  recovery=verify_recovery(page,origin,locale,supplier,paragraph,translations);assert not errors,errors
  checks.append({'engine':engine,'width':width,'locale':locale,'currency':currency,'photosLoaded':True,'compactCards':True,'priceAndUnitTogether':True,'noOverflow':True,'noRuntimeErrors':True,**recovery});context.close();browser.close();print(json.dumps({'liveBrowserPassed':locale,'width':width}),flush=True)
result={'passed':True,'releaseHash':proof['releaseHash'],'domains':domainsPassed,'nativeSsrAndLegalLocales':locales,'sitemapLocales':locales,'checks':checks,'realCharges':0,'ordersCreated':0}
(E/'browser-live.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'locales':len(locales),'browserCases':len(checks)}),flush=True)
