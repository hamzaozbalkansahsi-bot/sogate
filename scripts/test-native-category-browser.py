#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-category-browser.py
# Açıklama   : Kategori gezintisi, filtre, geri dönüş ve varyant güvenli sepet davranışını tarayıcıda sınar.
import hashlib,json,os,re,sys
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from playwright.sync_api import sync_playwright,expect
from native_browser_ready import NativePageReadiness
from native_test_errors import safe_error
sys.excepthook=safe_error
ROOT=Path(__file__).resolve().parent.parent
SCRIPT_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/')
SCOPE=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','categories-local')
assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
assert re.fullmatch('categories-(local|preview|remote)',SCOPE)
folder=ROOT/('docs/screenshots/native-store-'+SCOPE);folder.mkdir(parents=True,exist_ok=True)
results=[]
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(60000);ready=NativePageReadiness(page,BASE,60000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  try:
   page.goto(BASE+'/?page=categories&lang=tr',wait_until='domcontentloaded');ready.wait()
   gate=page.locator('.sexogate-age-accept')
   if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
   consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
   if consent.count()and consent.is_visible():consent.click();consent.wait_for(state='hidden');ready.wait()
   expect(page.locator('.sg-category-cards .category-tile')).to_have_count(5)
   assert page.locator('.sg-category-cards img').evaluate_all('nodes=>nodes.every(i=>i.complete&&i.naturalWidth>0)'),'CATEGORY_IMAGES'
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),'LANDING_OVERFLOW'
    assert page.locator('.sg-category-cards .category-tile').evaluate_all('nodes=>nodes.every(e=>e.getBoundingClientRect().height<=170)'),'OVERSIZED_CATEGORY_CARD'
   page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(folder/(engine+'-category-landing.png')))
   page.locator('[data-category-tile="sg_lingerie"]').click();ready.wait();expect(page.locator('.sg-category-tabs [aria-current]')).to_have_count(1)
   assert 'sg_lingerie' in page.url
   assert page.locator('.sg-subcategory-tile').count()>2
   page.screenshot(path=str(folder/(engine+'-category-explorer.png')))
   rail=page.locator('.sg-category-rail a').nth(1);rail.click();ready.wait();assert 'section=' in page.url
   assert page.locator('.sg-category-rail [aria-current]').count()==1
   page.locator('.sg-category-section-heading .category-view-all').click();ready.wait();assert '?page=catalog' in page.url
   page.go_back();ready.wait();assert 'section=' in page.url and page.locator('.sg-category-rail [aria-current]').count()==1
   page.goto(BASE+'/?page=catalog&category=sg_lingerie&lang=tr',wait_until='domcontentloaded');ready.wait()
   page.locator('[data-sg-facet="size"]').click();dialog=page.locator('#filter-dialog[open]');dialog.wait_for()
   expect(dialog.locator('[data-sg-filter-group="size"]')).to_have_attribute('open','')
   chosen=dialog.locator('input[name=size][value="XL"]');chosen.check();dialog.locator('button[type=submit]').click();ready.wait();page.wait_for_url(re.compile(r'.*size=XL.*'))
   expect(page.locator('.sg-filter-strip [data-sg-facet=all] b')).to_have_text('1')
   product_ids=page.locator('#product-grid [data-add]').evaluate_all('nodes=>nodes.map(e=>e.dataset.add)')
   data=context.request.get(BASE+'/api/catalog',max_retries=1,timeout=60000).json();products=data.get('catalog',data)['products'];by_id={v['id']:v for v in products}
   assert product_ids and all(any(a['id']=='size'and any(v['label']=='XL'for v in a['values'])for a in by_id[pid]['variantSelection']['axes'])for pid in product_ids),'SIZE_FILTER_MISMATCH'
   page.reload(wait_until='domcontentloaded');ready.wait();expect(page.locator('.sg-filter-strip [data-sg-facet=all] b')).to_have_text('1')
   page.locator('.sg-sort-pill select').select_option('price-asc');ready.wait();assert 'size=XL' in page.url and 'sort=price-asc' in page.url
   ids=page.locator('#product-grid [data-add]').evaluate_all('nodes=>nodes.map(e=>e.dataset.add)');prices=[by_id[pid]['salePriceMinor']for pid in ids];assert prices==sorted(prices),'PRICE_SORT'
   page.locator('#product-grid [data-add]').first.click();picker=page.locator('.sg-variant-dialog');picker.wait_for();assert picker.locator('.sg-variant-add').is_disabled();page.keyboard.press('Escape');picker.wait_for(state='detached')
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),'LISTING_OVERFLOW'
   page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(folder/(engine+'-filtered-listing.png')))
   page.locator('.sg-filter-strip [data-sg-facet=price]').click();dialog=page.locator('#filter-dialog[open]');dialog.locator('[name=minPrice]').fill('1000');dialog.locator('[name=maxPrice]').fill('1');dialog.locator('button[type=submit]').click();assert dialog.is_visible()and not dialog.locator('[name=maxPrice]').evaluate('e=>e.checkValidity()'),'INVALID_PRICE_NOT_REJECTED'
   dialog.locator('[name=minPrice]').fill('');dialog.locator('[name=maxPrice]').fill('');dialog.locator('.filter-heading a').click();ready.wait();assert not parse_qs(urlsplit(page.url).query).get('size')
   page.locator('[data-sg-facet=brand]').click();dialog=page.locator('#filter-dialog[open]');brand=dialog.locator('[name=brand]').nth(1);value=brand.input_value();brand.check();dialog.locator('button[type=submit]').click();ready.wait();ids=page.locator('#product-grid [data-add]').evaluate_all('nodes=>nodes.map(e=>e.dataset.add)');assert ids and all(by_id[pid]['brand']==value for pid in ids),'BRAND_FILTER_MISMATCH'
   trigger=page.locator('[data-sg-facet=color]');trigger.focus();page.keyboard.press('Enter');dialog=page.locator('#filter-dialog[open]');dialog.wait_for();assert dialog.locator('[data-sg-filter-group=color]').evaluate('e=>e.open&&e.contains(document.activeElement)'),'DRAWER_FOCUS'
   color=dialog.locator('[name=color]').nth(1);color_value=color.input_value();color.check();dialog.locator('button[type=submit]').click();ready.wait();expect(page.locator('.sg-filter-strip [data-sg-facet=all] b')).to_have_text('2')
   ids=page.locator('#product-grid [data-add]').evaluate_all('nodes=>nodes.map(e=>e.dataset.add)');assert ids and all(any(a['id']=='color'and any(v['label']==color_value for v in a['values'])for a in by_id[pid]['variantSelection']['axes'])for pid in ids),'COLOR_FILTER_MISMATCH'
   page.locator('[data-sg-facet=color]').click();page.locator('#filter-dialog[open]').wait_for();page.keyboard.press('Escape');page.locator('#filter-dialog').wait_for(state='hidden')
   page.goto(BASE+'/?page=categories&category=sg_lingerie&lang=ar',wait_until='domcontentloaded');ready.wait();assert page.locator('html').get_attribute('dir')=='rtl';assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(folder/(engine+'-category-rtl.png')))
   page.goto(BASE+'/?page=catalog&category=sg_lingerie&lang=tr',wait_until='domcontentloaded');ready.wait();page.locator('#sg-category-query').fill('gecelik');page.locator('[data-sg-category-search] button').click();ready.wait();assert 'q=gecelik' in page.url
   assert not any(word in page.locator('.sg-listing-page').inner_text().lower()for word in ['mağazaya git','hızlı satıcı','sponsorlu','sponsored']),'MARKETPLACE_BLOCK'
   page.goto(BASE+'/?page=catalog&brand=Liona&lang=tr',wait_until='domcontentloaded');ready.wait();expect(page.locator('meta[name=robots]')).to_have_attribute('content','noindex,follow');assert 'brand='not in page.locator('link[rel=canonical]').get_attribute('href')
   for field,value in [('brand','Liona'),('size','XL'),('material','Pamuk')]:
    document=context.request.get(BASE+'/?page=catalog&'+field+'='+value+'&lang=tr',max_retries=1,timeout=60000);assert document.status==200 and re.search(r'<meta[^>]+name="robots"[^>]+content="noindex,follow"',document.text()),('FACET_SERVER_NOINDEX',field)
   assert not errors,errors
   ssr=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),java_script_enabled=False,viewport={'width':390,'height':844});initial=ssr.new_page()
   for path,selector in [('?page=categories&lang=tr','.sg-category-cards .category-tile'),('?page=categories&category=sg_lingerie&lang=tr','.sg-subcategory-grid .sg-subcategory-tile'),('?page=categories&category=sg_lingerie&section=sg_lingerie_costumes&lang=tr','.sg-category-picks .product-card')]:
    initial.goto(BASE+'/'+path,wait_until='load');assert initial.locator(selector).count()>0,('SERVER_CATEGORY_LAYOUT',path);assert initial.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
   ssr.close()
   results.append({'engine':engine,'base':BASE,'release':context.request.get(BASE+'/api/deployment-status',max_retries=1).json()['release'],'widths':[360,390,430,768,1440],'categoryImages':True,'hierarchy':True,'backRestoresSelection':True,'sizeFilter':True,'brandFilter':True,'colorFilter':True,'sortPreservesFilters':True,'invalidPriceRejected':True,'variantSelectionRequired':True,'search':True,'rtl':True,'singleStore':True,'serverCategoryLayout':True,'keyboardDrawer':True,'facetNoindex':True,'pageErrors':0,'scriptSha256':SCRIPT_SHA256})
  except Exception:
   try:page.screenshot(path=str(folder/(engine+'-diagnostic.png')),timeout=5000)
   except Exception:pass
   print(json.dumps({'engine':engine,'errors':errors}),flush=True);raise
  finally:context.close();browser.close()
(ROOT/('.local/native-'+SCOPE+'.json')).write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results),flush=True)
