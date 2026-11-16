#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-home-browser.py
# Açıklama   : Ana sayfa rafları, ortak menü, sekme odağı ve ilk HTML eşliğini gerçek tarayıcıda sınar.
import hashlib,json,os,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from native_browser_ready import NativePageReadiness
from native_test_errors import safe_error
sys.excepthook=safe_error
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');SCOPE=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','home-local');SCRIPT_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)and re.fullmatch('home-(local|preview|remote)',SCOPE)
PROTOTYPE=os.environ.get('SEXOGATE_NATIVE_HOME_PROTOTYPE')=='1'
if PROTOTYPE:assert BASE.startswith('https://127.0.0.1:3188/')
folder=ROOT/('docs/screenshots/native-store-'+SCOPE);folder.mkdir(parents=True,exist_ok=True);results=[]
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(60000);ready=NativePageReadiness(page,BASE,60000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  try:
   print(engine+': home',flush=True);page.goto(BASE+'/?lang=tr',wait_until='domcontentloaded');ready.wait();gate=page.locator('.sexogate-age-accept')
   if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
   consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
   if consent.count()and consent.is_visible():consent.click();consent.wait_for(state='hidden');ready.wait()
   expect(page.locator('.sg-home-page')).to_have_count(1);assert not re.search(r'Çok satan|Flaş|Kupon|Mağazaya git|kişinin sepetinde',page.locator('.sg-home-page').inner_text(),re.I);assert page.locator('[data-home-shortcut]').count()>=8
   assert page.locator('[data-home-shelf=selection]').evaluate('e=>e.compareDocumentPosition(document.querySelector(".sg-home-campaigns"))&Node.DOCUMENT_POSITION_FOLLOWING'),'PRODUCT_RAIL_NOT_FIRST'
   ids=page.locator('[data-home-shelf=selection] [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)');assert len(ids)==len(set(ids))==8
   for width in [360,390,430,768,1024,1440]:
    page.set_viewport_size({'width':width,'height':1000});page.evaluate('()=>document.fonts.ready');assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),('HOME_OVERFLOW',width)
    assert page.locator('.sg-campaign-card').evaluate_all('ns=>ns.length===4&&ns.every(e=>e.getBoundingClientRect().height<240)')
    assert page.locator('.store-header').evaluate('e=>e.getBoundingClientRect().height')<=(180 if width<=900 else 160),'OVERSIZED_HEADER'
    metrics=page.locator('[data-home-shelf=selection] .product-card').evaluate_all('ns=>ns.map(e=>({price:e.querySelector(".card-price-compact").getBoundingClientRect().top,add:e.querySelector(".card-add").getBoundingClientRect().top}))');assert max(v['price']for v in metrics)-min(v['price']for v in metrics)<2,('HOME_PRICE_ALIGNMENT',width,metrics);assert max(v['add']for v in metrics)-min(v['add']for v in metrics)<2,('HOME_BUTTON_ALIGNMENT',width,metrics)
    if width in [390,1440]:page.screenshot(path=str(folder/(engine+'-home-'+str(width)+'.png')))
   page.set_viewport_size({'width':390,'height':844});rail=page.locator('[data-home-shelf=selection] .product-row');rail.scroll_into_view_if_needed();rail.focus();page.keyboard.press('ArrowRight');page.wait_for_function('e=>Math.abs(e.scrollLeft)>20',arg=rail.element_handle())
   discovery=page.locator('#sg-home-discovery');discovery.scroll_into_view_if_needed();start=page.evaluate('()=>scrollY');tab=discovery.locator('[data-home-category=sg_lingerie]');tab.click();expect(page.locator('#sg-home-discovery')).to_have_attribute('data-selected-category','sg_lingerie');assert abs(page.evaluate('()=>scrollY')-start)<3,'TAB_SCROLL_JUMP';assert 'homeCategory=sg_lingerie'in page.url;expect(page.locator('meta[name=robots]')).to_have_attribute('content','noindex,follow')
   data=context.request.get(BASE+'/api/catalog',max_retries=1,timeout=60000).json();products=data.get('catalog',data)['products'];known={v['id']:v for v in products};selected=page.locator('#sg-home-results [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)');assert selected and all('sg_lingerie'in known[v]['categoryIds']for v in selected),'DISCOVERY_WRONG_CATEGORY'
   page.locator('[data-home-category=sg_lingerie]').focus();page.keyboard.press('Home');expect(page.locator('[data-home-category=""]')).to_have_attribute('aria-selected','true');assert page.locator('[data-home-category=""]').evaluate('e=>e===document.activeElement'),'TAB_FOCUS_LOST'
   page.locator('[data-home-category=sg_lingerie]').click();page.reload(wait_until='domcontentloaded');ready.wait();expect(page.locator('#sg-home-discovery')).to_have_attribute('data-selected-category','sg_lingerie')
   page.locator('#sg-home-results [data-add]').first.click();picker=page.locator('.sg-variant-dialog');picker.wait_for();assert picker.locator('.sg-variant-add').is_disabled();page.keyboard.press('Escape');picker.wait_for(state='detached')
   page.locator('[data-home-blog]').click();page.wait_for_url(re.compile(r'.*/blog.*'));assert page.locator('.sg-home-page').count()==0,'BLOG_LINK_RETURNED_HOME';page.goto(BASE+'/?lang=ar',wait_until='domcontentloaded');ready.wait();assert page.locator('html').get_attribute('dir')=='rtl';assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth');page.locator('#sg-home-discovery').screenshot(path=str(folder/(engine+'-discovery-rtl.png')))
   ssr=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),java_script_enabled=False,viewport={'width':390,'height':844});initial=ssr.new_page();initial.goto(BASE+'/?lang=tr&homeCategory=sg_lingerie',wait_until='load');assert initial.locator('.sg-home-page').count()==1;expect(initial.locator('#sg-home-discovery')).to_have_attribute('data-selected-category','sg_lingerie');assert initial.locator('[data-home-shelf=selection] [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)')==ids,'SSR_CLIENT_PRODUCT_ORDER';assert all(v.startswith('/test/')for v in initial.locator('.sg-home-page a[href^="/"]').evaluate_all('ns=>ns.map(e=>e.getAttribute("href"))'))
   initial.screenshot(path=str(folder/(engine+'-home-no-javascript.png')));ssr.close();assert not errors,errors
   results.append({'engine':engine,'base':BASE,'release':context.request.get(BASE+'/api/deployment-status',max_retries=1).json()['release'],'scriptSha256':SCRIPT_SHA,'prototype':PROTOTYPE,'widths':[360,390,430,768,1024,1440],'productFirstLayout':True,'compactHeader':True,'balancedSelection':True,'alignedCards':True,'realCategoryTabs':True,'tabsPreserveScrollAndFocus':True,'tabDeepLink':True,'keyboardRail':True,'variantSelectionRequired':True,'blogRoute':True,'serverClientParity':True,'mountedServerLinks':True,'rtl':True,'pageErrors':0})
  except Exception:
   try:page.screenshot(path=str(folder/(engine+'-diagnostic.png')),timeout=5000)
   except Exception:pass
   print(json.dumps({'engine':engine,'pageErrors':errors}),flush=True);raise
  finally:context.close();browser.close()
(ROOT/('.local/native-'+SCOPE+'.json')).write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results),flush=True)
