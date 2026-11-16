#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-discovery.py
# Açıklama   : Gerçek pazaryeri kataloğunda ana sayfa, kategori gezintisi, filtre ve ilk HTML eşliğini iki tarayıcıda sınar.
import hashlib,json,os,re,sys
from pathlib import Path
from urllib.parse import parse_qs,urlencode,urlsplit
from playwright.sync_api import sync_playwright,expect
from native_browser_ready import NativePageReadiness
from native_test_errors import safe_error

sys.excepthook=safe_error
ROOT=Path(__file__).resolve().parent.parent
BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/')
SCOPE=os.environ.get('SEXOGATE_MARKETPLACE_SCOPE','local')
assert SCOPE in ['local','preview','remote']
assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
SCRIPT_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
WIDTHS=[360,390,430,768,1440]
MOUNT=urlsplit(BASE).path+'/'
FOLDER=ROOT/('docs/screenshots/native-store-marketplace-discovery-'+SCOPE)
FOLDER.mkdir(parents=True,exist_ok=True)

def url(**query):return BASE+'/?'+urlencode(query)

def dismiss(page):
 gate=page.locator('.sexogate-age-accept')
 if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
 consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
 if consent.count()and consent.is_visible():consent.click();consent.wait_for(state='hidden')

def query(page):return {k:v[0]for k,v in parse_qs(urlsplit(page.url).query).items()}

def family(categories,identifier):
 ids={identifier}
 while True:
  expanded=ids|{c['id']for c in categories if c.get('parentId')in ids}
  if expanded==ids:return ids
  ids=expanded

def members(products,categories,identifier):
 ids=family(categories,identifier)
 return [p for p in products if ids.intersection(p.get('categoryIds',[]))]

def option_labels(product,values):
 axes=product.get('variantSelection',{}).get('axes',[])
 return {a['id']:next(v['label']for v in a['values']if v['id']==values[a['id']])for a in axes if a['id']in values}

def real_choices(product):
 schema=product.get('variantSelection',{})
 axes={a['id']:a for a in schema.get('axes',[])}
 if not schema.get('required')or schema.get('blocked')or not product.get('brand','').strip()or not {'size','color'}<=set(axes):return None
 if schema.get('mode')=='matrix':
  active=next((v for v in schema.get('variants',[])if v.get('active')and {'size','color'}<=set(v.get('values',{}))),None)
  return option_labels(product,active['values'])if active else None
 return {field:axes[field]['values'][0]['label']for field in ['size','color']if axes[field]['values']}

def matches(product,selected):
 if selected.get('brand')and product.get('brand')!=selected['brand']:return False
 schema=product.get('variantSelection',{})
 axes={a['id']:a for a in schema.get('axes',[])}
 for field in ['size','color']:
  if selected.get(field)and not any(v['label']==selected[field]for v in axes.get(field,{}).get('values',[])):return False
 if schema.get('mode')=='matrix'and any(selected.get(k)for k in ['size','color']):
  return any(v.get('active')and all(not selected.get(k)or any(a['id']==v.get('values',{}).get(k)and a['label']==selected[k]for a in axes.get(k,{}).get('values',[]))for k in ['size','color'])for v in schema.get('variants',[]))
 return True

def select_input(dialog,field,value):
 chosen=next((n for n in dialog.locator('input[name="'+field+'"]').all()if n.input_value()==value),None)
 assert chosen is not None,('REAL_FACET_VALUE_MISSING',field,value)
 chosen.check()

def no_overflow(page,label):
 assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),label

def mounted_links(page,selector):
 links=page.locator(selector+' a[href^="/"]').evaluate_all('ns=>ns.map(e=>e.getAttribute("href"))')
 assert links and all(v.startswith(MOUNT)for v in links),('UNMOUNTED_LINK',links)

def facet_metadata(page):
 expect(page.locator('meta[name=robots]')).to_have_attribute('content','noindex,follow')
 canonical=page.locator('link[rel=canonical]').get_attribute('href')
 assert canonical and not {'brand','size','color','minPrice','maxPrice','sort'}&set(parse_qs(urlsplit(canonical).query)),('FACET_CANONICAL',canonical)

def listing_ids(page):return page.locator('#product-grid [data-add]').evaluate_all('ns=>ns.map(n=>n.dataset.add)')

def verify_listing(page,known,selected):
 ids=listing_ids(page)
 assert ids and all(identifier in known and matches(known[identifier],selected)for identifier in ids),('FACET_RESULT_MISMATCH',selected,ids)
 return ids

results=[]
with sync_playwright()as playwright:
 for engine in ['chromium','webkit']:
  browser=getattr(playwright,engine).launch()
  context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844})
  page=context.new_page();page.set_default_timeout(60000);ready=NativePageReadiness(page,BASE,60000);errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  try:
   health=context.request.get(BASE+'/api/deployment-status',timeout=60000).json();release=health['release']
   data=context.request.get(BASE+'/api/catalog',timeout=60000).json();data=data.get('catalog',data)
   products=data['products'];categories=data['categories'];known={p['id']:p for p in products}
   assert len(products)>=8 and all(p['id'].startswith('sg_ty_')for p in products),'NEW_PUBLIC_CATALOG_REQUIRED'
   roots=[c for c in categories if not c.get('parentId')and members(products,categories,c['id'])]
   choices=[]
   for root in roots:
    children=[c for c in categories if c.get('parentId')==root['id']and members(products,categories,c['id'])]
    for product in members(products,categories,root['id']):
     values=real_choices(product)
     if children and values and {'size','color'}<=set(values):choices.append((len(children),root,children,product,values))
   assert choices,'CATALOG_REQUIRES_REAL_SIZE_BRAND_COLOR_COMBINATION'
   _,root,children,product,values=max(choices,key=lambda item:item[0]);root_id=root['id'];section_id=children[0]['id']
   selected_values={'brand':product['brand'],'size':values['size'],'color':values['color']}
   print(engine+': marketplace home and discovery',flush=True)
   page.goto(url(lang='tr'),wait_until='domcontentloaded');ready.wait();dismiss(page);ready.wait()
   expect(page.locator('.sg-home-page')).to_have_count(1)
   assert not re.search(r'Çok satan|Flaş|Kupon|Mağazaya git|kişinin sepetinde',page.locator('.sg-home-page').inner_text(),re.I),'UNVERIFIED_HOME_CLAIM'
   assert page.locator('[data-home-shortcut]').count()>=len(roots),'REAL_CATEGORY_SHORTCUTS'
   assert page.locator('[data-home-shelf=selection]').evaluate('e=>e.compareDocumentPosition(document.querySelector(".sg-home-campaigns"))&Node.DOCUMENT_POSITION_FOLLOWING'),'PRODUCT_RAIL_NOT_FIRST'
   selection_ids=page.locator('[data-home-shelf=selection] [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)')
   assert len(selection_ids)==len(set(selection_ids))==8 and set(selection_ids)<=set(known),'SELECTION_NOT_EIGHT_UNIQUE_REAL_PRODUCTS'
   for width in WIDTHS:
    page.set_viewport_size({'width':width,'height':1000});page.evaluate('()=>document.fonts.ready');no_overflow(page,('HOME_OVERFLOW',width))
    assert page.locator('.sg-campaign-card').evaluate_all('ns=>ns.length===4&&ns.every(e=>e.getBoundingClientRect().height<240)'),'COMPACT_CAMPAIGN_CARDS'
    assert page.locator('.store-header').evaluate('e=>e.getBoundingClientRect().height')<=(180 if width<=900 else 160),'OVERSIZED_HEADER'
    metrics=page.locator('[data-home-shelf=selection] .product-card').evaluate_all('ns=>ns.map(e=>({price:e.querySelector(".card-price-compact").getBoundingClientRect().top,add:e.querySelector(".card-add").getBoundingClientRect().top}))')
    assert max(v['price']for v in metrics)-min(v['price']for v in metrics)<2,('HOME_PRICE_ALIGNMENT',width,metrics)
    assert max(v['add']for v in metrics)-min(v['add']for v in metrics)<2,('HOME_BUTTON_ALIGNMENT',width,metrics)
    if width in [390,1440]:page.screenshot(path=str(FOLDER/(engine+'-home-'+str(width)+'.png')))
   mounted_links(page,'.sg-home-page')
   page.set_viewport_size({'width':390,'height':844});rail=page.locator('[data-home-shelf=selection] .product-row');rail.scroll_into_view_if_needed();rail.focus();page.keyboard.press('ArrowRight');page.wait_for_function('e=>Math.abs(e.scrollLeft)>20',arg=rail.element_handle())
   discovery=page.locator('#sg-home-discovery');discovery.scroll_into_view_if_needed();start=page.evaluate('()=>scrollY')
   tab=discovery.locator('[data-home-category="'+root_id+'"]');tab.click();expect(discovery).to_have_attribute('data-selected-category',root_id)
   assert abs(page.evaluate('()=>scrollY')-start)<3,'TAB_SCROLL_JUMP'
   assert query(page).get('homeCategory')==root_id,'TAB_DEEP_LINK'
   expect(page.locator('meta[name=robots]')).to_have_attribute('content','noindex,follow')
   home_ids=page.locator('#sg-home-results [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)')
   assert home_ids and set(home_ids)<={p['id']for p in members(products,categories,root_id)},'DISCOVERY_WRONG_CATEGORY'
   tab.focus();page.keyboard.press('Home');expect(page.locator('[data-home-category=""]')).to_have_attribute('aria-selected','true')
   assert page.locator('[data-home-category=""]').evaluate('e=>e===document.activeElement'),'TAB_FOCUS_LOST'
   page.locator('[data-home-category="'+root_id+'"]').click();page.reload(wait_until='domcontentloaded');ready.wait();expect(discovery).to_have_attribute('data-selected-category',root_id)
   home_ids_after_reload=page.locator('#sg-home-results [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)');assert home_ids_after_reload==home_ids,'DISCOVERY_RELOAD_PARITY'
   page.locator('[data-home-blog]').click();page.wait_for_url(re.compile(r'.*/blog.*'));assert page.locator('.sg-home-page').count()==0,'BLOG_LINK_RETURNED_HOME'

   print(engine+': marketplace hierarchy and real facets',flush=True)
   page.goto(url(page='categories',lang='tr'),wait_until='domcontentloaded');ready.wait()
   tiles=page.locator('.sg-category-cards [data-category-tile]')
   assert set(tiles.evaluate_all('ns=>ns.map(e=>e.dataset.categoryTile)'))=={c['id']for c in roots},'OCCUPIED_CATEGORY_ROOTS'
   assert page.locator('.sg-category-cards img').evaluate_all('ns=>ns.length>0&&ns.every(e=>e.complete&&e.naturalWidth>0)'),'CATEGORY_IMAGES'
   for width in WIDTHS:
    page.set_viewport_size({'width':width,'height':900});no_overflow(page,('CATEGORY_LANDING_OVERFLOW',width))
    assert tiles.evaluate_all('ns=>ns.every(e=>e.getBoundingClientRect().height<=170)'),'OVERSIZED_CATEGORY_CARD'
   page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(FOLDER/(engine+'-category-landing.png')))
   page.locator('[data-category-tile="'+root_id+'"]').click();ready.wait();expect(page.locator('.sg-category-tabs [aria-current]')).to_have_count(1)
   assert query(page).get('category')==root_id and page.locator('.sg-subcategory-tile').count()==len(children)+1,'CATEGORY_HIERARCHY'
   section=next(link for link in page.locator('.sg-category-rail a').all()if parse_qs(urlsplit(link.get_attribute('href')).query).get('section')==[section_id])
   section.click();ready.wait();assert query(page).get('section')==section_id
   expect(page.locator('.sg-category-rail [aria-current]')).to_have_count(1)
   section_ids=page.locator('.sg-category-picks [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)')
   assert section_ids and set(section_ids)<={p['id']for p in members(products,categories,section_id)},'SECTION_PRODUCTS'
   page.locator('.sg-category-section-heading .category-view-all').click();ready.wait();assert query(page).get('page')=='catalog'and query(page).get('category')==section_id
   page.go_back();ready.wait();assert query(page).get('section')==section_id and page.locator('.sg-category-rail [aria-current]').count()==1,'BACK_LOST_CATEGORY_SELECTION'
   page.screenshot(path=str(FOLDER/(engine+'-category-hierarchy.png')))
   page.goto(url(page='catalog',category=root_id,lang='tr'),wait_until='domcontentloaded');ready.wait()
   page.locator('[data-sg-facet=size]').click();dialog=page.locator('#filter-dialog[open]');dialog.wait_for()
   expect(dialog.locator('[data-sg-filter-group=size]')).to_have_attribute('open','')
   select_input(dialog,'size',values['size']);dialog.locator('button[type=submit]').click();ready.wait()
   assert query(page).get('size')==values['size'];verify_listing(page,known,{'size':values['size']})
   expect(page.locator('.sg-filter-strip [data-sg-facet=all] b')).to_have_text('1')
   page.reload(wait_until='domcontentloaded');ready.wait();verify_listing(page,known,{'size':values['size']})
   assert query(page).get('size')==values['size'],'FILTER_RELOAD_LOST'
   page.locator('.sg-sort-pill select').select_option('price-asc');ready.wait();assert query(page).get('size')==values['size']and query(page).get('sort')=='price-asc','SORT_LOST_FILTER'
   ids=verify_listing(page,known,{'size':values['size']});prices=[known[i]['salePriceMinor']for i in ids];assert prices==sorted(prices),'PRICE_SORT'
   required=next(i for i in ids if known[i].get('variantSelection',{}).get('required')and not known[i]['variantSelection']['blocked'])
   page.locator('#product-grid [data-add="'+required+'"]').click();picker=page.locator('.sg-variant-dialog');picker.wait_for();assert picker.locator('.sg-variant-add').is_disabled(),'VARIANT_SELECTION_BYPASSED';page.keyboard.press('Escape');picker.wait_for(state='detached')
   for width in WIDTHS:
    page.set_viewport_size({'width':width,'height':900});no_overflow(page,('LISTING_OVERFLOW',width))
   page.set_viewport_size({'width':390,'height':844})
   page.locator('[data-sg-facet=price]').click();dialog=page.locator('#filter-dialog[open]');dialog.wait_for();dialog.locator('[name=minPrice]').fill('1000');dialog.locator('[name=maxPrice]').fill('1');dialog.locator('button[type=submit]').click()
   assert dialog.is_visible()and not dialog.locator('[name=maxPrice]').evaluate('e=>e.checkValidity()'),'INVALID_PRICE_NOT_REJECTED'
   dialog.locator('[name=minPrice]').fill('');dialog.locator('[name=maxPrice]').fill('');dialog.locator('.filter-heading a').click();ready.wait();assert 'size'not in query(page),'FILTER_CLEAR_FAILED'
   page.locator('[data-sg-facet=brand]').click();dialog=page.locator('#filter-dialog[open]');dialog.wait_for();select_input(dialog,'brand',product['brand']);dialog.locator('button[type=submit]').click();ready.wait();verify_listing(page,known,{'brand':product['brand']})
   page.locator('[data-sg-facet=size]').click();dialog=page.locator('#filter-dialog[open]');dialog.wait_for();select_input(dialog,'size',values['size']);dialog.locator('button[type=submit]').click();ready.wait();verify_listing(page,known,{'brand':product['brand'],'size':values['size']})
   trigger=page.locator('[data-sg-facet=color]');trigger.focus();page.keyboard.press('Enter');dialog=page.locator('#filter-dialog[open]');dialog.wait_for()
   assert dialog.locator('[data-sg-filter-group=color]').evaluate('e=>e.open&&e.contains(document.activeElement)'),'DRAWER_KEYBOARD_FOCUS'
   select_input(dialog,'color',values['color']);dialog.locator('button[type=submit]').click();ready.wait();verify_listing(page,known,selected_values)
   assert all(query(page).get(k)==v for k,v in selected_values.items()),'COMBINED_FILTER_URL'
   expect(page.locator('.sg-filter-strip [data-sg-facet=all] b')).to_have_text('3')
   page.locator('.sg-sort-pill select').select_option('price-asc');ready.wait();assert all(query(page).get(k)==v for k,v in selected_values.items()),'SORT_LOST_COMBINED_FILTERS'
   ids=verify_listing(page,known,selected_values);assert [known[i]['salePriceMinor']for i in ids]==sorted(known[i]['salePriceMinor']for i in ids),'COMBINED_PRICE_SORT'
   facet_metadata(page);page.screenshot(path=str(FOLDER/(engine+'-combined-filters.png')))
   page.locator('[data-sg-facet=color]').click();page.locator('#filter-dialog[open]').wait_for();page.keyboard.press('Escape');page.locator('#filter-dialog').wait_for(state='hidden')
   assert not any(word in page.locator('.sg-listing-page').inner_text().lower()for word in ['mağazaya git','hızlı satıcı','sponsorlu','sponsored']),'MARKETPLACE_SELLER_BLOCK'
   mounted_links(page,'.sg-listing-page')
   search_term=next(word for word in re.findall(r'[^\W\d_]{4,}',product['name']['tr'])if word.casefold()not in product['brand'].casefold())
   page.locator('#sg-category-query').fill(search_term);page.locator('[data-sg-category-search] button').click();ready.wait();assert query(page).get('q')==search_term and listing_ids(page),'CATEGORY_SEARCH'

   page.goto(url(lang='ar',homeCategory=root_id),wait_until='domcontentloaded');ready.wait();assert page.locator('html').get_attribute('dir')=='rtl';no_overflow(page,'HOME_RTL_OVERFLOW')
   page.locator('#sg-home-discovery').screenshot(path=str(FOLDER/(engine+'-home-rtl.png')))
   page.goto(url(page='categories',category=root_id,lang='ar'),wait_until='domcontentloaded');ready.wait();assert page.locator('html').get_attribute('dir')=='rtl';no_overflow(page,'CATEGORY_RTL_OVERFLOW');page.screenshot(path=str(FOLDER/(engine+'-category-rtl.png')))
   ssr=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),java_script_enabled=False,viewport={'width':390,'height':844})
   initial=ssr.new_page();initial.set_default_timeout(60000)
   try:
    initial.goto(url(lang='tr',homeCategory=root_id),wait_until='load');expect(initial.locator('.sg-home-page')).to_have_count(1);expect(initial.locator('#sg-home-discovery')).to_have_attribute('data-selected-category',root_id)
    assert initial.locator('[data-home-shelf=selection] [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)')==selection_ids,'SSR_CLIENT_SELECTION_ORDER'
    assert initial.locator('#sg-home-results [data-add]').evaluate_all('ns=>ns.map(e=>e.dataset.add)')==home_ids,'SSR_CLIENT_DISCOVERY_ORDER'
    assert initial.locator('.sg-campaign-card').count()==4,'SSR_COMPACT_CARDS';mounted_links(initial,'.sg-home-page');no_overflow(initial,'SSR_HOME_OVERFLOW')
    initial.screenshot(path=str(FOLDER/(engine+'-home-no-javascript.png')))
    for params,selector in [({'page':'categories','lang':'tr'},'.sg-category-cards [data-category-tile]'),({'page':'categories','category':root_id,'lang':'tr'},'.sg-subcategory-grid .sg-subcategory-tile'),({'page':'categories','category':root_id,'section':section_id,'lang':'tr'},'.sg-category-picks .product-card')]:
     initial.goto(url(**params),wait_until='load');assert initial.locator(selector).count()>0,('SSR_CATEGORY_LAYOUT',params);mounted_links(initial,'.sg-categories');no_overflow(initial,('SSR_CATEGORY_OVERFLOW',params))
    for field,value in selected_values.items():
     response=initial.goto(url(page='catalog',lang='tr',**{field:value}),wait_until='load');assert response.status==200;facet_metadata(initial)
   finally:ssr.close()
   assert context.request.get(BASE+'/api/deployment-status',timeout=60000).json()['release']==release,'RELEASE_CHANGED_DURING_DISCOVERY_TEST'
   assert not errors,errors
   result={'engine':engine,'base':BASE,'release':release,'scriptSha256':SCRIPT_SHA,'scope':SCOPE,'widths':WIDTHS,'publicProducts':len(products),'occupiedRoots':len(roots),'exampleProduct':product['id'],'exampleCategory':root_id,'exampleSection':section_id,'realFacetValues':selected_values,'productFirstLayout':True,'compactHeader':True,'compactCampaignCards':True,'balancedSelection':True,'alignedCards':True,'realCategoryTabs':True,'tabsPreserveScrollAndFocus':True,'tabDeepLink':True,'keyboardRail':True,'variantSelectionRequired':True,'blogRoute':True,'serverClientParity':True,'mountedServerLinks':True,'categoryImages':True,'hierarchy':True,'backRestoresSelection':True,'sizeFilter':True,'brandFilter':True,'colorFilter':True,'validCombinedFacets':True,'sortPreservesFilters':True,'invalidPriceRejected':True,'keyboardDrawer':True,'facetNoindex':True,'facetCanonical':True,'search':True,'rtl':True,'singleStore':True,'serverCategoryLayout':True,'pageErrors':0,'realPayments':False,'adminAccessed':False}
   results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
  except Exception:
   try:page.screenshot(path=str(FOLDER/(engine+'-diagnostic.png')),timeout=5000)
   except Exception:pass
   print(json.dumps({'engine':engine,'pageErrors':errors,'path':urlsplit(page.url).path,'query':urlsplit(page.url).query}),flush=True)
   raise
  finally:context.close();browser.close()
(ROOT/('docs/native-marketplace-discovery-'+SCOPE+'-results.json')).write_text(json.dumps({'base':BASE,'scope':SCOPE,'results':results},ensure_ascii=False,indent=2),'utf8')
