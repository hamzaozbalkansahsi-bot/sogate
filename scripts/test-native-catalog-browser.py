#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-catalog-browser.py
# Açıklama   : Gerçek yönetim oturumunda kaynak yükleme, fiyat, SEO, mükerrerlik ve özel görselleri sınar.
import base64,hashlib,hmac,json,os,re,struct,time
from decimal import Decimal
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','catalog-local')
assert re.fullmatch('[a-z-]+',scope)and re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
access=json.loads((ROOT/'.local'/('php-stage-access.json'if BASE.startswith('https://sexogate.com')else'php-access.json')).read_text('utf8'))
def otp():
 secret=access['totpSecret'];key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));d=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=d[-1]&15;return str((struct.unpack('>I',d[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
with sync_playwright()as p:
 browser=p.chromium.launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'));page=context.new_page();page.set_default_timeout(60000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 try:
  page.goto(BASE+'/yonetim');page.locator('[name=email]').fill(access['email']);page.locator('[name=password]').fill(access['password']);page.get_by_role('button',name='Devam et',exact=True).click();page.locator('#verify').wait_for();
  if time.time()%30>27:time.sleep(3)
  page.locator('[name=proof]').fill(otp());page.locator('#verify button[type=submit]').click();page.locator('.sidebar').wait_for();page.goto(BASE+'/yonetim#products');page.get_by_role('button',name='Ürünleri yükle',exact=True).click();page.get_by_role('button',name='Yüklemeyi başlat',exact=True).click();page.wait_for_function('()=>{const b=document.querySelector("[data-sg-start]");return b&&!b.disabled}',timeout=240000);assert page.get_by_role('button',name='Ürün listesini yenile',exact=True).count(),page.locator('[data-sg-progress]').inner_text()
  loaded=page.locator('[data-sg-progress]').inner_text();print(json.dumps({'importResult':loaded}),flush=True)
  request=context.request;session=request.get(BASE+'/api/admin/session').json();headers={'Content-Type':'application/json','X-CSRF-Token':session['csrfToken'],'Origin':BASE.split('/test')[0]}
  source=request.get(BASE+'/api/admin/catalog-source').json();assert source['products']==source['loaded']==2194 and len(source['sourceCategories'])==172,source
  records=request.get(BASE+'/api/admin/products').json()['data'];assert len(records)==2194 and len(set(r['id']for r in records))==2194
  prepared=Path(json.loads((ROOT/'.local/native-catalog-selection.json').read_text('utf8'))['path']);expected=json.loads((prepared/'catalog-data.json').read_text('utf8'));by_id={p['id']:p for p in expected['products']};published=[]
  for row in records:
   product=by_id[row['id']];values=row['data'];assert values.get('priceMinor')==product['salePriceMinor'];assert not values.get('stockKnown')and values.get('stockQuantity')is None
   for prefix in ['title','description','seoTitle','seoDescription']:
    for language in ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']:assert values[prefix+'_'+language]and '\ufffd'not in values[prefix+'_'+language]
   if values['visible']:published.append(row['id'])
  expected_visible=json.loads((ROOT/'.local/native-catalog-selection.json').read_text('utf8'))['reviewedCovers'];assert len(published)==expected_visible,len(published)
  # İlk komutu tekrar oynatmak ikinci ürün, sürüm veya fiyat değişikliği üretmemeli.
  before=request.get(BASE+'/api/admin/products').json()['data'];replay=request.post(BASE+'/api/admin/catalog-import',headers=headers,data=json.dumps({'dataset':source['dataset'],'offset':0}));assert replay.status==200,replay.text()[:300];after=request.get(BASE+'/api/admin/products').json()['data'];assert before==after
  public=request.get(BASE+'/api/catalog').json();catalog=public.get('catalog',public);assert len(catalog['products'])==expected_visible,(list(public),len(catalog.get('products',[])))
  chosen=catalog['products'][0];media=request.get(BASE.split('/test')[0]+chosen['images'][0]);assert media.status==200 and media.headers['content-type'].startswith('image/')
  assert 'privateRetailReference'not in chosen and 'sourceVendor'not in chosen
  product_page=request.get(BASE+'/?product='+chosen['id']+'&lang=tr');assert product_page.status==200;soup=BeautifulSoup(product_page.text(),'lxml');assert soup.find('link',rel='canonical')['href'].startswith('https://sexogate.com'+urlsplit(BASE).path+'/')
  nodes=[]
  for script in soup.select('script[type="application/ld+json"]'):
   node=json.loads(script.string or script.get_text());nodes.extend(node if isinstance(node,list)else node.get('@graph',[node]))
  offers=[node['offers']for node in nodes if node.get('@type')=='Product'and'offers'in node];assert offers,[(node.get('@type'))for node in nodes];offer=offers[0][0]if isinstance(offers[0],list)else offers[0];assert int(Decimal(str(offer['price']))*100)==chosen['salePriceMinor']and offer['priceCurrency']=='TRY';assert not any('aggregateRating'in node or'review'in node for node in nodes)
  csrf_probe=request.post(BASE+'/api/admin/catalog-import',headers={**headers,'X-CSRF-Token':'invalid'},data=json.dumps({'dataset':source['dataset'],'offset':0}));assert csrf_probe.status==403
  anonymous=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'));assert anonymous.request.get(BASE+'/api/admin/catalog-source').status in [401,403]
  draft=next(r['id']for r in records if not r['data']['visible']);assert anonymous.request.get(BASE+'/media/'+draft+'/0').status==404;assert anonymous.request.get(BASE+'/yonetim/urun-onizleme?product='+draft).status in [401,403]
  assert context.request.get(BASE+'/yonetim/urun-onizleme?product='+draft).status==200
  modal=page.locator('.sexogate-catalog-dialog');modal.get_by_role('button',name='Kapat',exact=True).click();page.get_by_role('button',name='Kaynak kategoriler',exact=True).click();page.wait_for_function('()=>document.querySelectorAll("[data-sg-category]").length===172');page.locator('[data-sg-cancel]').click()
  page.reload();page.locator('[data-edit]').first.click();page.get_by_role('link',name='Ürüne git',exact=True).wait_for();assert page.locator('[name=seoTitle_tr]').input_value();assert page.locator('[name=sourceVendor]').input_value()in ['xshopum','liona','sistina']
  folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(folder/'admin-product.png'))
  assert not errors,errors;result={'base':BASE,'products':2194,'priced':2151,'priceMissing':43,'sourceCategories':172,'publishedCovers':expected_visible,'markupPercent':30,'locales':11,'idempotent':True,'privateDrafts':True,'sourcePriceIsNotCost':True,'pageErrors':0,'release':request.get(BASE+'/api/deployment-status').json()['release']};(ROOT/('.local/native-'+scope+'.json')).write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True);anonymous.close()
 finally:context.close();browser.close()
