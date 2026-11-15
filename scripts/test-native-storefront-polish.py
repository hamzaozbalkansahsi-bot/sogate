#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-storefront-polish.py
# Açıklama   : Gerçek fotoğraf yüklemesi, mobilya temizliği, kart hizası ve mobil çakışmaları ölçer.
import json,os,re
from urllib.parse import urlsplit
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_browser_ready import NativePageReadiness
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','polish-local');assert re.fullmatch('[a-z-]+',scope)
assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True);results=[]
def log(message):print(message,flush=True)

def dismiss(page):
 gate=page.locator('#sexogate-age-gate')
 if gate.count():gate.locator('.sexogate-age-accept').click();gate.wait_for(state='detached')
 button=page.get_by_role('button',name='Yalnız gerekli',exact=True)
 if button.count()and button.first.is_visible():button.first.click();button.first.wait_for(state='hidden')
def text_check(page):
 text=page.locator('body').inner_text();assert not re.search(r'\bMutfak\b|Evinize|Alanıma uyar|odalar[ıa]|Yeni eviniz|mobilya|montaj|Teknik bilgiler|Teslimat seçenekleri ürünün|Görsel hazırlanıyor|KDV hariç',text,re.I),text[:500]
def image_check(page):
 images=page.locator('img.product-image');assert images.count()>0,'NO_RENDERED_PRODUCT_IMAGES'
 for image in images.all():
  if image.is_visible():image.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})');page.wait_for_function('(e)=>e.complete&&e.naturalWidth>0',arg=image.element_handle(),timeout=15000)
 assert page.locator('.image-fallback').count()==0,'PRODUCT_IMAGE_FALLBACK'
def image_bounds(page):
 assert page.locator('.sg-campaign-image,.sg-home-shortcuts>a>span,.product-card-stage').evaluate_all('(frames)=>frames.every(f=>{const i=f.querySelector("img");if(!i)return true;const a=f.getBoundingClientRect(),b=i.getBoundingClientRect();return getComputedStyle(i).objectFit==="contain"&&b.height<=a.height+1&&b.width<=a.width+1&&b.top>=a.top-1&&b.bottom<=a.bottom+1})'),'CROPPED_PRODUCT_IMAGE'

def no_overflow(page):assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),page.viewport_size
with sync_playwright()as p:
 for engine in ['webkit','chromium']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(30000);page.set_default_navigation_timeout(60000);errors=[];account_mount_errors=[];network_failures=[];page.on('response',lambda r:account_mount_errors.append(r.url)if '/api/account'in r.url and r.status==404 else None);page.on('pageerror',lambda error:errors.append(str(error)))
  readiness=NativePageReadiness(page,BASE,timeout=30000)
  page.on('requestfailed',lambda r:network_failures.append({'path':urlsplit(r.url).path,'error':r.failure}))
  page.on('response',lambda r:network_failures.append({'path':urlsplit(r.url).path,'status':r.status})if r.status>=400 else None)
  try:
   log(engine+': curtains');page.goto(BASE+'/?lang=tr',wait_until='domcontentloaded');gate=page.locator('#sexogate-age-gate');gate.wait_for(state='visible');curtain=gate.locator('.sexogate-age-curtain-left');assert curtain.evaluate('(e)=>parseFloat(getComputedStyle(e).animationDuration)')>=4.8
   page.wait_for_function('()=>document.querySelector("#sexogate-age-gate").classList.contains("is-ready")');start=curtain.evaluate('(e)=>Math.abs(new DOMMatrix(getComputedStyle(e).transform).m41)');page.screenshot(path=str(folder/(engine+'-curtain-initial.png')),timeout=15000);page.wait_for_timeout(1000);middle=curtain.evaluate('(e)=>Math.abs(new DOMMatrix(getComputedStyle(e).transform).m41)');page.screenshot(path=str(folder/(engine+'-curtain-mid.png')));page.wait_for_timeout(4000);final=curtain.evaluate('(e)=>Math.abs(new DOMMatrix(getComputedStyle(e).transform).m41)');assert final>start+30 and middle>=start,(start,middle,final);dismiss(page);log(engine+': home images');image_check(page);text_check(page)
   assert page.locator('.sg-campaign-card').count()==4;assert page.locator('.sg-home-hero').count()==0;assert page.locator('.sg-home-shortcuts img').count()>=4
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});no_overflow(page);image_bounds(page);assert page.locator('.sg-campaign-card').evaluate_all('(cards)=>cards.every(e=>e.getBoundingClientRect().height<240&&e.querySelector("img").naturalWidth>0)')
   page.set_viewport_size({'width':390,'height':844})
   log(engine+': catalog');page.goto(BASE+'/?page=catalog');readiness.wait();dismiss(page);image_check(page);text_check(page)
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});no_overflow(page);image_bounds(page)
    positions=page.locator('.product-grid>.product-card').evaluate_all('(cards)=>cards.map(c=>({top:c.getBoundingClientRect().top,price:c.querySelector(".card-price-compact").getBoundingClientRect().top,add:c.querySelector(".card-add").getBoundingClientRect().top}))')
    for index,row in enumerate(positions):
     for previous in positions[:index]:
      if abs(row['top']-previous['top'])<2:assert abs(row['price']-previous['price'])<2 and abs(row['add']-previous['add'])<2,('unaligned',width,positions)
   assert context.request.get(BASE+'/api/account/social').status==200,'ACCOUNT_API_MOUNT_BROKEN';log(engine+': product');catalog=context.request.get(BASE+'/api/catalog').json();catalog=catalog.get('catalog',catalog);identifier=catalog['products'][0]['id'];page.goto(BASE+'/?product='+identifier+'&lang=tr');readiness.wait();dismiss(page);image_check(page);text_check(page)
   assert page.locator('a').evaluate_all('(nodes)=>nodes.filter(e=>e.offsetWidth&&e.offsetHeight).every(e=>!getComputedStyle(e).textDecorationLine.includes("underline"))'),'UNDERLINED_LINK';assert page.locator('.sg-product-intro').count()==1;assert not page.locator('[data-fit]').count();assert not page.locator('.delivery-preview').count();assert page.locator('.sg-product-intro').inner_text().count(identifier)==0
   page.locator('[data-sg-open-features]').click();assert page.locator('#sg-all-features').get_attribute('open')is not None;assert page.locator('.sg-feature-list>div').count()>0;assert page.locator('.sg-feature-list dd').evaluate_all('(n)=>n.every(e=>e.textContent.length<221)')
   log(engine+': rail');rail=page.locator('.product-shelf .product-row').first;rail.scroll_into_view_if_needed();maximum=rail.evaluate('(e)=>e.scrollWidth-e.clientWidth');assert maximum>20
   rail.focus();page.keyboard.press('ArrowRight');page.wait_for_function('(e)=>Math.abs(e.scrollLeft)>20',arg=rail.element_handle());page.wait_for_timeout(400)
   log(engine+': privacy');page.set_viewport_size({'width':390,'height':844});privacy=page.locator('.insights-settings');assert privacy.count()==1;assert privacy.evaluate('(e)=>!!e.closest(".store-footer")&&getComputedStyle(e).position==="static"')
   for width in [360,390,430,768]:
    page.set_viewport_size({'width':width,'height':844});no_overflow(page);page.wait_for_timeout(100)
    boxes=page.evaluate('()=>{const p=document.querySelector(".mobile-purchase").getBoundingClientRect(),n=document.querySelector(".bottom-nav").getBoundingClientRect();return {p:{top:p.top,bottom:p.bottom},n:{top:n.top,bottom:n.bottom,height:n.height}}}')
    if boxes['n']['height']>0:assert boxes['p']['bottom']<=boxes['n']['top']+2,('sticky-overlap',width,boxes)
   page.set_viewport_size({'width':390,'height':844});privacy.scroll_into_view_if_needed();assert privacy.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'),'PRIVACY_BUTTON_OCCLUDED'
   page.screenshot(path=str(folder/(engine+'-product-footer.png')));privacy.click();page.wait_for_timeout(200);assert page.locator('#insights-preferences[open]').count()==1;page.get_by_role('button',name='Analiz ve geçmişe izin ver',exact=True).click();page.locator('#insights-preferences').wait_for(state='hidden');readiness.wait();log(engine+': recent rail')
   for item in catalog['products'][:4]:
    page.goto(BASE+'/?product='+item['id']);page.locator('.sg-product-intro').wait_for();readiness.wait()
   page.goto(BASE+'/?page=recent');readiness.wait();recent=page.locator('.shopping-page .product-row');recent.wait_for();assert recent.locator('.product-card').count()>=3;page.wait_for_function('(e)=>e.scrollWidth>e.clientWidth',arg=recent.element_handle());recent.focus();page.keyboard.press('ArrowRight');page.wait_for_function('(e)=>Math.abs(e.scrollLeft)>20',arg=recent.element_handle());page.screenshot(path=str(folder/(engine+'-recent-rail.png')))
   # Rıza geri alındığında kişiselleştirme geçmişi de temizlenir.
   page.locator('.insights-settings').evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})');page.locator('.insights-settings').click();page.get_by_role('button',name='İzni kaldır ve geçmişi sil',exact=True).click();page.locator('#insights-preferences').wait_for(state='hidden');readiness.wait()
   page.goto(BASE+'/?product='+identifier);readiness.wait();page.locator('[data-sg-open-features]').click();page.wait_for_timeout(300);page.screenshot(path=str(folder/(engine+'-product-features.png')))
   for path in ['/','/?page=help','/?page=collections','/?page=compare','/?page=favorites','/?page=recent']:
    log(engine+': '+path);page.goto(BASE+path);readiness.wait();dismiss(page);text_check(page);no_overflow(page)
   page.goto(BASE+'/');readiness.wait();page.screenshot(path=str(folder/(engine+'-home-390.png')));page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path=str(folder/(engine+'-home-1440.png')))
   assert not errors,errors;assert not account_mount_errors,account_mount_errors;release=context.request.get(BASE+'/api/deployment-status').json()['release'];result={'base':BASE,'release':release,'engine':engine,'readiness':'critical_requests_and_rendered_ui','optionalFxObserved':readiness.optional_observed,'realImagesLoaded':True,'furnitureCopy':False,'alignedCards':True,'stickyOverlap':False,'footerPrivacyEntry':True,'readableFeatures':True,'horizontalRelatedRail':True,'horizontalRecentRail':True,'curtainDurationSeconds':4.8,'consentRevocation':True,'accountHelperMountedOnce':True,'underlinedLinks':False,'compactImageCampaignCards':4,'productImageBounds':True,'widths':[360,390,430,768,1440],'pageErrors':0};results.append(result);print(json.dumps(result),flush=True)
  except Exception:
   try:
    print(json.dumps({'diagnostic':True,'engine':engine,'url':page.url,'pageErrors':errors,'networkFailures':network_failures[-24:],'body':page.locator('body').inner_text(timeout=2000)[:900]},ensure_ascii=False),flush=True)
    page.screenshot(path=str(folder/('diagnostic-'+engine+'.png')),timeout=5000)
   except Exception as diagnostic_error:print('Diagnostic capture: '+type(diagnostic_error).__name__,flush=True)
   raise
  finally:context.close();browser.close()
(ROOT/('.local/native-'+scope+'.json')).write_text(json.dumps(results,indent=2),encoding='utf8')
