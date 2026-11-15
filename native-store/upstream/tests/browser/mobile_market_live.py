from pathlib import Path
import json,urllib.request,hashlib
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/mobile-market-20261111';proof=json.loads((E/'release.json').read_bytes());release=R/proof['release'];checks=[];origin='https://nodenohome.com'
for domain in ['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']:
 health=json.load(urllib.request.urlopen('https://'+domain+'/api/health',timeout=45));status=json.load(urllib.request.urlopen('https://'+domain+'/api/payments/status',timeout=45))
 assert health['status']=='ok'and health['releaseHash']==proof['releaseHash']and health['mediaReady']and health['checkoutEnabled']
 assert status['enabled']and not status['test']and status['seller']['termsVersion']=='2026-11-10.3'
 print(json.dumps({'domainPassed':domain}),flush=True)
with sync_playwright()as pw:
 for engine,width,locale in [('chromium',1440,'tr'),('chromium',390,'en'),('chromium',390,'ru'),('webkit',320,'ar')]:
  exe=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  browser=getattr(pw,engine).launch(headless=True,executable_path=str(exe));context=browser.new_context(viewport={'width':width,'height':920},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("if(sessionStorage.getItem('qa-show-map')!=='1')localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.currency.v1',JSON.stringify('KZT'));localStorage.setItem('nodeno.analytics.consent.v1','false')")
  page.goto(origin+'/?lang='+locale,wait_until='networkidle');picker=page.locator('#display-currency');expect(picker).to_have_value({'tr':'TRY','en':'USD','ru':'RUB','ar':'SAR'}[locale],timeout=20000)
  assert page.evaluate("()=>import('/currency.js?v=nodeno-measurements-20261110-r1').then(m=>m.currencyState().currency)")==picker.input_value(),'price_formatter_currency_differs_from_header'
  def geometry():
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   assert page.locator('#header-currency').evaluate('(e)=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth}')
  geometry()
  for lang,code in [('tr','TRY'),('en','USD'),('ru','RUB'),('ar','SAR')]:
   page.locator('#language').select_option(lang);expect(picker).to_have_value(code);assert page.evaluate("()=>import('/currency.js?v=nodeno-measurements-20261110-r1').then(m=>m.currencyState().currency)")==code;geometry()
  page.locator('#language').select_option('tr');picker.select_option('KZT');page.reload(wait_until='networkidle');expect(picker).to_have_value('KZT',timeout=20000)
  page.locator('#language').select_option('en');expect(picker).to_have_value('USD');page.locator('#language').select_option('tr');expect(picker).to_have_value('TRY')
  shelf=page.locator('#product-shelf-storageIdeas');shelf.evaluate('(s)=>window.scrollTo({top:s.getBoundingClientRect().top+scrollY-document.querySelector(".store-header").getBoundingClientRect().height-16,behavior:"instant"})');page.wait_for_load_state('networkidle')
  if width<768:assert page.locator('.quick-open:visible').count()==0
  page.wait_for_function('()=>{const stages=[...document.querySelectorAll("#product-shelf-storageIdeas .product-stage")].filter(s=>{const r=s.getBoundingClientRect(),p=s.closest(".product-row").getBoundingClientRect();return r.left<Math.min(innerWidth,p.right)&&r.right>Math.max(0,p.left)&&r.top<innerHeight&&r.bottom>0});return stages.length>0&&stages.every(s=>{const i=s.querySelector("img");return i&&i.complete&&i.naturalWidth>0})}')
  shelf.locator('img').evaluate_all('(images)=>Promise.all(images.filter(i=>i.complete&&i.naturalWidth>0).map(i=>i.decode()))');page.wait_for_timeout(800);page.screenshot(path=str(E/('live-'+engine+'-'+str(width)+'-'+locale+'.png')))
  page.evaluate("sessionStorage.setItem('qa-show-map','1');localStorage.removeItem('nodeno.international-welcome.hidden')")
  for country,lang,code in [('DE','en','EUR'),('KZ','ru','KZT'),('TR','tr','TRY')]:
   page.goto(origin+'/?lang='+page.locator('#language').input_value(),wait_until='networkidle');dialog=page.locator('#international-welcome');expect(dialog).to_be_visible(timeout=10000)
   if country=='TR':dialog.locator('[data-map-region=TUR]').dispatch_event('click')
   else:dialog.locator('[data-country-select='+country+']').click()
   expect(dialog).to_have_count(0);expect(page.locator('#language')).to_have_value(lang);expect(picker).to_have_value(code,timeout=20000);geometry()
   marker=page.evaluate('(value)=>new Intl.NumberFormat(document.documentElement.lang,{style:"currency",currency:value}).formatToParts(1).find(p=>p.type==="currency").value',code)
   expect(page.locator('[data-price]').first).to_contain_text(marker)
  assert not errors,errors
  checks.append({'engine':engine,'width':width,'locale':locale,'headerSelectorsAccessible':True,'languageCurrencySync':True,'legacyMismatchMigrated':True,'manualOverridePersists':True,'mapCountrySync':True,'mobileQuickOverlayRemoved':True,'noOverflow':True,'noRuntimeErrors':True});context.close();browser.close();print(json.dumps({'passedCase':locale,'width':width}),flush=True)
(E/'browser-live.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'checks':checks,'realCharges':0},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(checks)}),flush=True)
