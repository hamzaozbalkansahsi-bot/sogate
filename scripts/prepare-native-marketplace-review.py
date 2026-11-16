#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-marketplace-review.py
# Açıklama   : Tek tek okunan ürünleri gerçek seçenekleri, nihai %15 fiyatı ve eksik alan raporuyla özel incelemeye hazırlar.
import hashlib,json,re,sqlite3,time
from pathlib import Path
from PIL import Image
from native_marketplaces import fetch
from native_catalog import make_product,LANGUAGES,plain,gtin
ROOT=Path(__file__).resolve().parent.parent
HOME=Path('D:/sexogate-local-artifacts-20261114/private-installs/marketplace-catalog-20261116');media=HOME/'media';media.mkdir(exist_ok=True)
db=sqlite3.connect(HOME/'research.sqlite');db.row_factory=sqlite3.Row
cacheFile=HOME/'images.json';cache=json.loads(cacheFile.read_text('utf8'))if cacheFile.exists()else {};products=[];work=[];categories={};errors=[]
factsKeys=['barcode','manufacturer','origin','materials','dimensions','sizeOptions','colorOptions','batteryInformation','shippingWeight','packageDimensions','ingredients','warranty','care','safety','documents','costMinor']
for row in db.execute("SELECT * FROM products WHERE status='ready' ORDER BY platform,id"):
 d=json.loads(row['detail_json']);attrs={v['name']:v['value']for v in d['attributes']if v['name']and v['value']};facts=dict.fromkeys(factsKeys)
 facts['sizeOptions']=', '.join(dict.fromkeys(v['size']for v in d['variants']if v['size']))or None
 for key,source in {'materials':['Materyal','Kumaş Tipi','Malzeme'],'dimensions':['Boy / Ölçü','Ürün Boyu'],'colorOptions':['Renk'],'origin':['Menşei','Menşei Ülke']}.items():facts[key]=next((attrs[a]for a in source if attrs.get(a)),None)
 variants=[]
 for v in d['variants']:
  if not v['size']:continue
  attributes=[{'name':'Beden','value':v['size']}]
  if facts['colorOptions']:attributes.append({'name':'Renk','value':facts['colorOptions']})
  variants.append({'id':v['sourceVariantId'],'sku':None,'isActive':v['sourceInStock'],'attributes':attributes,'observedPriceMinor':v['observedPriceMinor'],'sourceBarcode':v.get('barcode')})
 for v in d['variants']:
  if code:=gtin(v.get('barcode')):facts['barcode']=code if len(d['variants'])==1 else None
 sourceRow={'sourceUrl':d['sourceUrl'],'title':d['title'],'images':d['sourceImages'],'quotedRetailMinor':d['undiscountedPriceMinor'],'quotedCurrency':d['currency'],'publicInStock':d['publicInStock'],'observedAt':d['observedAt'],'sourceMethod':'individual_public_product_page'}
 detail={'sourceSku':d['sourceCode'],'brand':d['brand'],'facts':facts,'description':d['sourceDescription'],'variants':variants,'categories':d['categoryTree'],'sourceHtmlSha256':d['sourceSha256']}
 p,w=make_product(d['platform'],sourceRow,detail);oldId=p['id'];oldSku=p['sku'];identifier='sg_ty_'+hashlib.sha256(d['sourceUrl'].encode()).hexdigest()[:16];sku=d['sku']
 p.update(id=identifier,modelId=identifier,sku=sku,code=sku,catalogOrigin='sexogate-marketplaces-v1',salePriceMinor=d['salePriceMinor'],privateRetailReference=d['undiscountedPriceMinor'])
 for field in ['modelName','name','description','seoTitle','seoDescription']:
  p[field]={lang:text.replace(oldSku,sku or '')for lang,text in p[field].items()}
 p['slug']=p['slug'].rsplit('-',1)[0]+'-'+identifier[-8:];p['images']=[];p['visualApprovedIndices']=[]
 w.update(id=identifier,sku=sku,initialMarkupPercent=15,rights={'basis':'user_declaration','at':'2026-11-16','scope':'product_images_and_content_and_platform_supplier_watermarks','writtenContractClaimed':False},sourceAttributes=d['attributes'],priceEvidence=d['priceEvidence'],priceBasis=d['priceBasis'],publicationApproved=False,media=[])
 w['source']['vendor']=d['platform'];w['source']['sourceSku']=d['sourceCode'];w['source']['retailPriceMinor']=d['undiscountedPriceMinor']
 holds=list(d['missingFields'])
 if not sku:holds.append('source_code_required')
 if len({v['observedPriceMinor']for v in d['variants']if v['observedPriceMinor']})>1:holds.append('variant_price_review')
 if holds:p['eligibilityHold']=w['eligibilityHold']=True
 w['reviewHolds']=holds;w['sourceDescription']=d['sourceDescription'];w['sourceVariants']=variants
 for c in d['categoryTree']:
  if c.get('id')is not None:categories[str(c['id'])]={'id':str(c['id']),'title':c.get('name')or'','vendor':d['platform'],'metadataState':'observed_source_page'}
 # Original bytes stay untouched. Display approval is a separate visual decision.
 for url in d['sourceImages'][:1]:
  if url not in cache:
   try:
    raw=fetch(url);sha=hashlib.sha256(raw).hexdigest();temp=media/(sha+'.bin');temp.write_bytes(raw)
    with Image.open(temp)as im:
     im.verify();fmt=im.format
    extension={'JPEG':'jpg','PNG':'png','WEBP':'webp'}.get(fmt)
    if not extension:raise ValueError('IMAGE_FORMAT_REJECTED')
    file=media/(sha+'.'+extension);temp.replace(file);cache[url]={'file':file.name,'sha256':sha,'mime':{'JPEG':'image/jpeg','PNG':'image/png','WEBP':'image/webp'}[fmt],'sourceUrl':url,'originalBytesPreserved':True}
   except Exception as error:errors.append({'id':identifier,'error':type(error).__name__});continue
   cacheFile.write_text(json.dumps(cache,ensure_ascii=False),'utf8');time.sleep(.2)
  image={**cache[url],'bytes':(media/cache[url]['file']).stat().st_size};w['media'].append(image);p['images'].append('/media/'+identifier+'/'+str(len(p['images'])))
 products.append(p);work.append(w)
out={'schema':1,'sourceTag':'sexogate-marketplaces-v1','products':products,'workbench':work,'sourceCategories':list(categories.values()),'markupPercent':15,'additionalDiscountPercent':0,'allTransferred':False,'imagesReviewed':False,'published':0,'rightsBasis':'user_declaration_2026-11-16','checkoutEnabled':False}
(HOME/'catalog-source.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),'utf8')
report={'details':len(products),'coverFiles':len(cache),'sourceCategories':len(categories),'reviewHolds':sum(bool(w['reviewHolds'])for w in work),'mediaErrors':errors,'published':0,'fullCatalogue':False}
(ROOT/'.local/native-marketplace-review.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report))
