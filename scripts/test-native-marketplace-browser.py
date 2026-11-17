#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-browser.py
# Açıklama   : Yeni gerçek ürünleri, kapak hash’lerini, kategori filtrelerini ve yönetim önizlemesini iki tarayıcıda doğrular.
import base64,hashlib,hmac,json,os,re,struct,sys,time,traceback
from decimal import Decimal
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from native_browser_ready import NativePageReadiness
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');SCOPE=os.environ.get('SEXOGATE_MARKETPLACE_SCOPE','local');assert SCOPE in ['local','preview','remote'];assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
remote=BASE.startswith('https://sexogate.com');access=json.loads((ROOT/'.local'/('php-stage-access.json'if remote else'php-access.json')).read_text('utf8'));selection=json.loads((ROOT/'.local/native-marketplace-selection.json').read_text('utf8'));prepared=Path(selection['path']);source=json.loads((prepared/'catalog-data.json').read_text('utf8'));expected={p['id']:p for p in source['products'][2194:]if p['visualApprovedIndices']and not p['eligibilityHold']and p['salePriceMinor']}
work={k:v for f in(prepared/'catalog-workbench').glob('*.json')for k,v in json.loads(f.read_text('utf8')).items()if k.startswith('sg_ty_')};folder=ROOT/('docs/screenshots/native-store-marketplace-'+SCOPE);folder.mkdir(parents=True,exist_ok=True);results=[]
def safe_error(kind,error,trace):
 text=str(error)
 for k in ['email','password','totpSecret']:text=text.replace(access[k],'[private]')
 text=re.sub(r'(?im)^.*(?:cookie:|authorization:|x-csrf-token:).*$', '[private headers]',text);print(kind.__name__+': '+text[:1700]+' '+str([(Path(f.filename).name,f.lineno)for f in traceback.extract_tb(trace)]),file=sys.stderr)
sys.excepthook=safe_error
def dismiss(page):
 gate=page.locator('.sexogate-age-accept')
 if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
 consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
 if consent.count()and consent.is_visible():consent.click()
def otp():
 secret=access['totpSecret'];key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));d=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();i=d[-1]&15;return str((struct.unpack('>I',d[i:i+4])[0]&0x7fffffff)%1000000).zfill(6)
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  print(engine+': marketplace catalog',flush=True);browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=not remote,viewport={'width':390,'height':844});page=context.new_page();page.set_default_timeout(60000);ready=NativePageReadiness(page,BASE,60000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  try:
   status=context.request.get(BASE+'/api/deployment-status').json();catalog=context.request.get(BASE+'/api/catalog',timeout=60000).json();public=catalog['products'];assert {v['id']for v in public}==set(expected),'PUBLIC_SET_DIFFERS_FROM_REVIEW'
   for item in public:
    target=expected[item['id']];assert item['code']==target['code']and item['salePriceMinor']==target['salePriceMinor'];assert item['stockKnown']is False and item['stockQuantity']is None;assert 'privateRetailReference'not in item and 'sourceVendor'not in item
    imageUrl=item['images'][0];imageUrl=BASE+imageUrl if imageUrl.startswith('/media/')else BASE.split('/test')[0]+imageUrl;assert imageUrl.startswith(BASE+'/media/');photo=context.request.get(imageUrl,timeout=60000);assert photo.status==200;assert hashlib.sha256(photo.body()).hexdigest()==work[item['id']]['media'][target['coverIndex']]['sha256'],'MEDIA_HASH_CHANGED'
   private=next(v for v in source['products'][2194:]if v['id']not in expected and v['images']);assert context.request.get(BASE+'/media/'+private['id']+'/0').status==404,'DRAFT_PHOTO_PUBLIC'
   page.goto(BASE+'/?lang=tr');ready.wait();dismiss(page);ready.wait();assert page.locator('.sg-home-page').count()==1;assert page.locator('.sg-campaign-card').count()==4
   for width in [360,390,430,768,1440]:
    page.set_viewport_size({'width':width,'height':900});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth');page.evaluate('()=>document.fonts.ready')
    if width in [390,1440]:page.screenshot(path=str(folder/(engine+'-home-'+str(width)+'.png')))
   page.goto(BASE+'/?page=categories&lang=tr');ready.wait();assert page.locator('.sg-category-cards .category-tile').count()>0
   assert page.locator('.sg-category-cards img').evaluate_all('es=>es.every(e=>e.complete&&e.naturalWidth>0)')
   page.locator('[data-category-tile="sg_lingerie"]').click();ready.wait();assert page.locator('.sg-subcategory-tile').count()>1
   chosen=next(v for v in public if any(a['id']=='size'for a in v.get('variantSelection',{}).get('axes',[]))and not v['variantSelection']['blocked']);size=next(a['values'][0]['label']for a in chosen['variantSelection']['axes']if a['id']=='size')
   page.goto(BASE+'/?page=catalog&category=sg_lingerie&lang=tr');ready.wait();page.locator('[data-sg-facet=size]').click();dialog=page.locator('#filter-dialog[open]');dialog.wait_for()
   options=dialog.locator('input[name=size]');option=next(v for v in options.all()if v.input_value()==size);option.check();dialog.locator('button[type=submit]').click();ready.wait();ids=page.locator('#product-grid [data-add]').evaluate_all('ns=>ns.map(n=>n.dataset.add)');byId={v['id']:v for v in public};assert ids and all(any(a['id']=='size'and any(v['label']==size for v in a['values'])for a in byId[id]['variantSelection']['axes'])for id in ids)
   page.locator('.sg-sort-pill select').select_option('price-asc');ready.wait();ids=page.locator('#product-grid [data-add]').evaluate_all('ns=>ns.map(n=>n.dataset.add)');assert [byId[id]['salePriceMinor']for id in ids]==sorted(byId[id]['salePriceMinor']for id in ids)
   expect(page.locator('meta[name=robots]')).to_have_attribute('content','noindex,follow');page.screenshot(path=str(folder/(engine+'-filtered.png')))
   page.goto(BASE+'/?product='+chosen['id']+'&lang=tr');ready.wait();assert page.locator('h1').inner_text()==chosen['name']['tr'];assert page.locator('script[type="application/ld+json"]').count()>0;assert not re.search(r'Mağazaya git|Hızlı satıcı|sponsorlu',page.locator('#page').inner_text(),re.I)
   blocked=context.request.post(BASE+'/api/payments/checkout',data={},headers={'Origin':BASE.split('/test')[0]});assert blocked.status==409,'REAL_CHECKOUT_OPEN'
   print(engine+': native product editor',flush=True);page.goto(BASE+'/yonetim');ready.wait();page.locator('[name=email]').fill(access['email']);page.locator('[name=password]').fill(access['password']);page.get_by_role('button',name='Devam et',exact=True).click();page.locator('#verify').wait_for();time.sleep(30.1-time.time()%30);page.locator('[name=proof]').fill(otp());page.locator('#verify button[type=submit]').click();page.locator('.sidebar').wait_for();ready.wait()
   page.goto(BASE+'/yonetim#products?record='+chosen['id']);page.locator('#editor[open]').wait_for();page.reload(wait_until='domcontentloaded');ready.wait();form=page.locator('#editor[open] #record-form');form.wait_for();expect(form.locator('[name=sku]')).to_have_value(chosen['code']);assert int(Decimal(form.locator('[name=priceMinor]').input_value().replace(',','.'))*100)==chosen['salePriceMinor'];assert form.locator('[name=seoTitle_tr]').input_value();assert form.locator('[name=seoDescription_tr]').input_value()
   link=page.locator('[data-sg-view-product]');link.wait_for();assert link.inner_text()=='Ürüne git';page.screenshot(path=str(folder/(engine+'-admin-product.png')))
   with page.expect_popup()as opened:link.click()
   productPage=opened.value;productReady=NativePageReadiness(productPage,BASE,60000);productReady.wait();assert 'product='+chosen['id']in productPage.url;assert productPage.locator('h1').inner_text()==chosen['name']['tr'];productPage.close();assert not errors,errors
   results.append({'engine':engine,'base':BASE,'release':status['release'],'dataset':selection['dataset'],'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'loadedNew':selection['newProducts'],'visibleNew':len(public),'allMarketplaceProductsTransferred':False,'sourceCodesKept':True,'finalMarkup15':True,'noFakeInventory':True,'noLegacyProducts':True,'realImageHashes':True,'draftMediaPrivate':True,'categorySizeFilter':True,'priceSort':True,'facetNoindex':True,'singleStore':True,'adminMfa':True,'adminFieldsAndSeo':True,'adminGoToProductAfterReload':True,'checkoutClosed':True,'pageErrors':0,'widths':[360,390,430,768,1440]});print(json.dumps(results[-1]),flush=True)
  except Exception:
   try:page.screenshot(path=str(folder/(engine+'-diagnostic.png')))
   except Exception:pass
   raise
  finally:context.close();browser.close()
(ROOT/('docs/native-marketplace-'+SCOPE+'-results.json')).write_text(json.dumps({'base':BASE,'results':results},ensure_ascii=False,indent=2),'utf8')
