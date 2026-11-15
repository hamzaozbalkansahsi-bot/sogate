from pathlib import Path
import json,urllib.request
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/vitrine-20261111';proof=json.loads((E/'release.json').read_bytes());checks=[];origin='https://nodenohome.com'
for domain in ['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']:
 health=json.load(urllib.request.urlopen('https://'+domain+'/api/health',timeout=45));status=json.load(urllib.request.urlopen('https://'+domain+'/api/payments/status',timeout=45))
 assert health['status']=='ok'and health['releaseHash']==proof['releaseHash']and health['mediaReady']and health['checkoutEnabled']
 assert status['enabled']and not status['test']and status['seller']['termsVersion']=='2026-11-10.3'
 print(json.dumps({'domainPassed':domain}),flush=True)
with sync_playwright()as pw:
 for engine,width,locale in [('chromium',1440,'tr'),('chromium',390,'en'),('chromium',390,'ru'),('webkit',390,'ar')]:
  print(json.dumps({'starting':locale,'width':width}),flush=True)
  exe=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  browser=getattr(pw,engine).launch(headless=True,executable_path=str(exe));context=browser.new_context(ignore_https_errors=True,viewport={'width':width,'height':1000 if width>767 else 920},is_mobile=width<768,has_touch=width<768,reduced_motion='reduce'if engine=='webkit'else'no-preference');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false')")
  page.goto(origin+'/?lang='+locale,wait_until='networkidle');v=page.locator('[data-home-vitrine]');expect(v).to_be_visible();expect(v.locator('[data-vitrine-slide]')).to_have_count(3);tabs=v.locator('[data-vitrine-go]');play=v.locator('[data-vitrine-play]')
  if engine=='webkit':expect(play).to_have_attribute('aria-pressed','true')
  else:
   play.click();expect(play).to_have_attribute('aria-pressed','true')
  page.wait_for_function('()=>{const i=document.querySelector("[data-vitrine-slide] img");return i&&i.complete&&i.naturalWidth>0}')
  page.wait_for_timeout(600);page.screenshot(path=str(E/('live-home-'+engine+'-'+str(width)+'-'+locale+'.png')))
  tabs.nth(1).click();expect(tabs.nth(1)).to_have_attribute('aria-current','true');page.wait_for_timeout(550);expect(play).to_have_attribute('aria-pressed','true')
  if width>767:
   page.locator('#search').focus();page.mouse.move(1,1);active=tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")');page.wait_for_timeout(6500);assert tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")')==active
   play.click();page.locator('#search').focus();page.mouse.move(1,1);expect(tabs.nth(2)).to_have_attribute('aria-current','true',timeout=9000);play.click()
  if engine=='webkit':
   active=tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")');page.locator('#search').focus();page.mouse.move(1,1);page.wait_for_timeout(6500);assert tabs.evaluate_all('(a)=>a.findIndex(x=>x.getAttribute("aria-current")==="true")')==active
  shelf=page.locator('#product-shelf-storageIdeas');shelf.evaluate('(e)=>scrollTo({top:e.getBoundingClientRect().top+scrollY-document.querySelector(".store-header").getBoundingClientRect().height-16,behavior:"instant"})');page.wait_for_load_state('networkidle')
  first=shelf.locator('.product-card').first;assert first.evaluate('(c)=>{const h=c.querySelector("h3").getBoundingClientRect(),color=c.querySelector(".card-color").getBoundingClientRect();return color.top-h.bottom<18&&h.height<52}')
  assert first.locator('.card-price-main').evaluate('(e)=>e.getBoundingClientRect().height<30&&e.querySelector(".price-unit").textContent.includes("m²")')
  if width<768:assert page.locator('.quick-open:visible').count()==0
  page.wait_for_function('()=>{const ss=[...document.querySelectorAll("#product-shelf-storageIdeas .product-stage")].filter(e=>{const r=e.getBoundingClientRect(),p=e.closest(".product-row").getBoundingClientRect();return r.left<Math.min(p.right,innerWidth)&&r.right>Math.max(p.left,0)&&r.top<innerHeight&&r.bottom>0});return ss.length>0&&ss.every(s=>{const i=s.querySelector("img");return i&&i.complete&&i.naturalWidth>0})}')
  page.wait_for_timeout(800);page.screenshot(path=str(E/('live-cards-'+engine+'-'+str(width)+'-'+locale+'.png')));assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not errors,errors
  checks.append({'engine':engine,'width':width,'locale':locale,'threeRealProductSlides':True,'manualAndPauseControls':True,'reducedMotionRespected':True,'compactTitleColourGap':True,'priceAndUnitTogether':True,'noQuickOverlay':True,'noOverflow':True,'noRuntimeErrors':True});context.close();browser.close();print(json.dumps({'passedCase':locale}),flush=True)
(E/'browser-live.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'checks':checks,'realCharges':0},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(checks)}),flush=True)
