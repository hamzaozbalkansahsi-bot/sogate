"""Read-only live acceptance: no registration, order or provider checkout submission."""
from pathlib import Path
import hashlib,json,urllib.request
from playwright.sync_api import sync_playwright,expect

R=Path(__file__).resolve().parents[2];E=R/'artifacts/packaging-fix-20261111'
proof=json.loads((E/'release.json').read_bytes());release=R/proof['release']
headings={'tr':'Kapaklarla evinizin görünümünü baştan sona yenileyin.','en':"Refresh your home's look with new cabinet fronts.",'ru':'Обновите облик дома с новыми мебельными фасадами.','ar':'جدّد مظهر منزلك بالكامل بواجهات خزائن جديدة.'}
def get(url):
 request=urllib.request.Request(url,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity'})
 with urllib.request.urlopen(request,timeout=45)as response:return response.read()
domains=[]
for domain in ['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']:
 origin='https://'+domain;health=json.loads(get(origin+'/api/health'));status=json.loads(get(origin+'/api/payments/status'))
 assert health['status']=='ok'and health['releaseHash']==proof['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']is True and health['products']==3602
 assert status['enabled']is True and status['test']is False and status['seller']['termsVersion']=='2026-11-10.3'
 for name in ['app.js','shop-i18n.js']:assert hashlib.sha256(get(origin+'/'+name)).digest()==hashlib.sha256((release/'public'/name).read_bytes()).digest()
 domains.append({'domain':domain,'sameReleaseAndPublicModules':True,'mediaReady':True,'liveCheckoutEnabled':True,'termsVersion':status['seller']['termsVersion']})
catalog=json.loads(get('https://nodenohome.com/api/catalog'));byid={p['id']:p for p in catalog['products']};checks=[]
with sync_playwright()as pw:
 for engine,width,locale,domain in [('chromium',1440,'tr','nodenohome.com'),('chromium',390,'en','nodenohome.com.tr'),('chromium',390,'ru','nodenohome.com'),('webkit',390,'ar','nodenohome.com.tr')]:
  executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  browser=getattr(pw,engine).launch(headless=True,executable_path=str(executable));context=browser.new_context(viewport={'width':width,'height':920},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'));")
  page.goto('https://'+domain+'/?lang='+locale,wait_until='networkidle');shelf=page.locator('#product-shelf-storageIdeas');expect(shelf.locator('h2')).to_have_text(headings[locale]);shelf.scroll_into_view_if_needed()
  page.wait_for_load_state('networkidle')
  page.wait_for_function('()=>{const stages=[...document.querySelectorAll("#product-shelf-storageIdeas .product-stage")].filter(s=>{const r=s.getBoundingClientRect();return r.left<innerWidth&&r.right>0&&r.top<innerHeight&&r.bottom>0});const ready=stages.length>0&&stages.every(s=>{const i=s.querySelector("img");return i&&i.complete&&i.naturalWidth>0});window.frontsReadyAt=ready?(window.frontsReadyAt||Date.now()):0;return ready&&Date.now()-window.frontsReadyAt>600}')
  shelf.locator('img').evaluate_all('(images)=>Promise.all(images.filter(i=>i.complete&&i.naturalWidth>0).map(i=>i.decode()))')
  page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
  links=shelf.locator('a[href*="product="]').evaluate_all('(links)=>links.map(a=>new URL(a.href).searchParams.get("product"))');assert links and all(byid[key]['productType']in['cabinet-front','cabinet-profile']for key in links)
  assert 'category=dolap-kapaklari'in shelf.locator('.section-heading a').get_attribute('href');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not errors,errors
  assert shelf.locator('.product-stage').first.evaluate('(s)=>{const c=getComputedStyle(s),i=s.querySelector("img");return parseFloat(c.paddingBlockStart)>=16&&parseFloat(c.paddingInlineStart)>=12&&getComputedStyle(i).objectFit==="contain"&&i.getBoundingClientRect().top-s.getBoundingClientRect().top>=15}')
  page.screenshot(path=str(E/('live-home-fronts-'+engine+'-'+locale+'.png')))
  page.goto('https://'+domain+'/legal/returns?lang='+locale,wait_until='networkidle');expect(page.locator('h1')).to_be_visible();assert '2026-11-10.3'in page.locator('main').inner_text()
  checks.append({'engine':engine,'width':width,'locale':locale,'domain':domain,'headingAndCategoryCorrect':True,'visibleImagesLoaded':True,'noOverflow':True,'noRuntimeErrors':True,'returnPolicyVersionPreserved':True});context.close();browser.close();print(json.dumps({'browserCasePassed':locale,'engine':engine}),flush=True)
(E/'browser-live.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'domains':domains,'checks':checks,'testUsersCreated':0,'testOrdersCreated':0,'realCharges':0},indent=2)+'\n')
print(json.dumps({'passed':True,'domains':len(domains),'browserCases':len(checks),'realCharges':0}),flush=True)
