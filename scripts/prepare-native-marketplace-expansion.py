#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-marketplace-expansion.py
# Açıklama   : Donmuş ilk yayını koruyarak genişleyen kaynak kuyruğunu gerçek kanıt ve ayrı görsel incelemesiyle hazırlar.
import argparse,hashlib,json,os,re,sqlite3,time,concurrent.futures,threading
from pathlib import Path
from contextlib import closing
from PIL import Image
from native_marketplaces import fetch,props,minor,plain,marketplace_claim_review,detail_page
from native_catalog import make_product,gtin,GROUPS,loc,LANGUAGES,fold
ROOT=Path(__file__).resolve().parent.parent;BASE=Path('D:/sexogate-local-artifacts-20261114/private-installs');HOME=BASE/'marketplace-catalog-20261117';RESEARCH=BASE/'marketplace-expansion-20261117-research';FIRST=BASE/'marketplace-catalog-20261116'
def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),'utf8');temp.replace(path)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mutable():
 selection=ROOT/'.local/native-marketplace-selection.json'
 if selection.exists()and Path(json.loads(selection.read_text('utf8'))['path']).resolve()==(HOME/'prepared').resolve():raise ValueError('SELECTED_DATASET_IS_FROZEN')
 HOME.mkdir(exist_ok=True)
def snapshot():
 mutable();tmp=HOME/'research-next.sqlite'
 if tmp.exists():tmp.unlink()
 with closing(sqlite3.connect(RESEARCH.joinpath('research.sqlite').resolve().as_uri()+'?mode=ro',uri=True))as source,closing(sqlite3.connect(tmp))as target:source.backup(target)
 tmp.replace(HOME/'research.sqlite');(HOME/'raw').mkdir(exist_ok=True);copied=0
 with closing(sqlite3.connect(HOME/'research.sqlite'))as db:rows=db.execute("SELECT id,detail_json FROM products WHERE status='ready'").fetchall()
 def verify_raw(row):
   identifier,raw=row
   if not re.fullmatch(r'\d+',identifier):raise ValueError('SOURCE_ID_INVALID')
   detail=json.loads(raw);origin=RESEARCH/'raw'/(identifier+'.html');destination=HOME/'raw'/(identifier+'.html')
   if not origin.is_file()or sha(origin)!=detail['sourceSha256']:raise ValueError('SOURCE_RAW_HASH_MISMATCH')
   if destination.exists():
    if sha(destination)==detail['sourceSha256']:return 0
    destination.unlink()
   os.link(origin,destination);return 1
 with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:copied=sum(pool.map(verify_raw,rows))
 repair_codes()
 print(json.dumps({'snapshot':True,'rawLinksAdded':copied}),flush=True)

def repair_codes():
 mutable()
 with closing(sqlite3.connect(HOME/'research.sqlite'))as db:
  rows=db.execute("SELECT id,detail_json FROM products WHERE status='ready'").fetchall()
  for identifier,raw in rows:
   detail=json.loads(raw)
   if not detail['sourceCode']:
    raw_body=(HOME/'raw'/(identifier+'.html')).read_bytes();assert hashlib.sha256(raw_body).hexdigest()==detail['sourceSha256'],'SOURCE_RAW_HASH_MISMATCH'
    parsed=detail_page(raw_body,detail['sourceUrl'])
    if parsed['sourceCode']:
     detail.update(sourceCode=parsed['sourceCode'],sku=parsed['sku'],missingFields=parsed['missingFields'],sourceCodeReview='actual_source_internal_spaces_preserved')
     db.execute('UPDATE products SET detail_json=? WHERE id=?',(json.dumps(detail,ensure_ascii=False,separators=(',',':')),identifier))
  db.commit()
def copy_cache():
 cache={}
 for folder in [FIRST,HOME]:
  if(folder/'images.json').exists():
   for url,item in json.loads((folder/'images.json').read_text('utf8')).items():
    origin=folder/'media'/item['file'];target=HOME/'media'/item['file']
    if not origin.exists()or sha(origin)!=item['sha256']:raise ValueError('SOURCE_MEDIA_CACHE_CHANGED')
    if not target.exists():os.link(origin,target)
    cache[url]=item
 return cache
def generate(alternates=False):
 mutable();(HOME/'media').mkdir(exist_ok=True);cache=copy_cache();reviews={r['id']:r for r in json.loads((FIRST/'cover-review.json').read_text('utf8'))};plan=json.loads((HOME/'editorial-review.json').read_text('utf8'))if(HOME/'editorial-review.json').exists()else{};products=[];work=[];categories={};downloads={};errors=[]
 extended=set(json.loads((HOME/'extended-gallery-ids.json').read_text('utf8')))if(HOME/'extended-gallery-ids.json').exists()else set()
 with closing(sqlite3.connect(HOME/'research.sqlite'))as db:rows=db.execute("SELECT id,detail_json FROM products WHERE status='ready' ORDER BY platform,id").fetchall()
 for identifier,raw in rows:
  d=json.loads(raw);attrs={a['name']:a['value']for a in d['attributes']if a['name']and a['value']};facts=dict.fromkeys(['barcode','manufacturer','origin','materials','dimensions','sizeOptions','colorOptions','batteryInformation','shippingWeight','packageDimensions','ingredients','warranty','care','safety','documents','costMinor'])
  facts['sizeOptions']=', '.join(dict.fromkeys(v['size']for v in d['variants']if v['size']))or None
  for key,names in {'materials':['Materyal','Kumaş Tipi','Malzeme'],'dimensions':['Boy / Ölçü','Ürün Boyu'],'colorOptions':['Renk'],'origin':['Menşei','Menşei Ülke']}.items():facts[key]=next((attrs[n]for n in names if attrs.get(n)),None)
  variants=[{'id':v['sourceVariantId'],'sku':None,'isActive':v['sourceInStock'],'attributes':[{'name':'Beden','value':v['size']}]+([{'name':'Renk','value':facts['colorOptions']}]if facts['colorOptions']else[]),'observedPriceMinor':v['observedPriceMinor'],'sourceBarcode':v.get('barcode')}for v in d['variants']if v['size']]
  for v in d['variants']:
   if len(d['variants'])==1 and(code:=gtin(v.get('barcode'))):facts['barcode']=code
  row={'sourceUrl':d['sourceUrl'],'title':d['title'],'images':d['sourceImages'],'quotedRetailMinor':d['undiscountedPriceMinor'],'quotedCurrency':d['currency'],'publicInStock':d['publicInStock'],'observedAt':d['observedAt'],'sourceMethod':'individual_public_product_page'};detail={'sourceSku':d['sourceCode'],'brand':d['brand'],'facts':facts,'description':d['sourceDescription'],'variants':variants,'categories':d['categoryTree'],'sourceHtmlSha256':d['sourceSha256']}
  p,w=make_product(d['platform'],row,detail);oldsku=p['sku'];pid='sg_ty_'+hashlib.sha256(d['sourceUrl'].encode()).hexdigest()[:16];sku=d['sku'];p.update(id=pid,modelId=pid,sku=sku,code=sku,catalogOrigin='sexogate-marketplaces-v1',salePriceMinor=d['salePriceMinor'],privateRetailReference=d['undiscountedPriceMinor'])
  for field in ['name','modelName','description','seoTitle','seoDescription']:p[field]={lang:text.replace(oldsku,sku or'')for lang,text in p[field].items()}
  p['slug']=p['slug'].rsplit('-',1)[0]+'-'+pid[-8:];p['images']=[];p['visualApprovedIndices']=[];holds=list(d['missingFields']);review=plan.get(pid,{})
  if not sku:holds.append('source_code_required')
  if len({v['observedPriceMinor']for v in d['variants']if v['observedPriceMinor']})>1:holds.append('variant_price_review')
  if any(re.search(r'\b\d+\s*[-–/]?\s*\d*\s*(?:AY|YAŞ|MONTH|YEAR)\b',v.get('size',''),re.I)for v in d['variants']):holds.append('inconsistent_youth_size_source')
  w.update(id=pid,sku=sku,initialMarkupPercent=15,sourceAttributes=d['attributes'],priceEvidence=d['priceEvidence'],priceBasis=d['priceBasis'],publicationApproved=False,media=[],sourceDescription=d['sourceDescription'],sourceVariants=variants,sourceVariantsUnfiltered=variants,rawSourceTitle=d['title'],rawSourceId=identifier,editorialReview=review,rights={'basis':'user_declaration','at':'2026-11-16','scope':'product_images_and_content_and_platform_supplier_watermarks','writtenContractClaimed':False})
  w['source'].update(vendor=d['platform'],sourceSku=d['sourceCode'],retailPriceMinor=d['undiscountedPriceMinor']);w['reviewHolds']=sorted(set(holds));w['eligibilityHold']=p['eligibilityHold']=bool(holds)or p['eligibilityHold']or marketplace_claim_review(d['title']);w['originalEligibilityHold']=p['eligibilityHold'];w['originalCoverReview']=reviews.get(pid)
  for c in d['categoryTree']:
   if c.get('id')is not None:categories[str(c['id'])]={'id':str(c['id']),'title':c.get('name')or'','vendor':d['platform'],'metadataState':'observed_source_page'}
  urls=d['sourceImages'][:1]
  if alternates and pid in reviews and not reviews[pid]['coverApproved']:urls=d['sourceImages'][:4]
  if pid in extended:urls=d['sourceImages'][:12]
  w['candidateImageUrls']=urls
  for url in urls:
   if url not in cache:downloads.setdefault(url,[]).append(pid)
  products.append(p);work.append(w)
 stopped=threading.Event()
 def download(url):
  if stopped.is_set():return url,None,'SOURCE_ACCESS_BLOCKED'
  try:
   raw=fetch(url);digest=hashlib.sha256(raw).hexdigest();temp=HOME/'media'/(digest+'-'+str(threading.get_ident())+'.tmp');temp.write_bytes(raw)
   with Image.open(temp)as image:image.verify();fmt=image.format
   extension={'JPEG':'jpg','PNG':'png','WEBP':'webp'}.get(fmt)
   if not extension:raise ValueError('IMAGE_FORMAT_REJECTED')
   target=HOME/'media'/(digest+'.'+extension)
   if target.exists():temp.unlink()
   else:temp.replace(target)
   return url,{'file':target.name,'sha256':digest,'mime':{'JPEG':'image/jpeg','PNG':'image/png','WEBP':'image/webp'}[fmt],'sourceUrl':url,'originalBytesPreserved':True},None
  except PermissionError:stopped.set();return url,None,'SOURCE_ACCESS_BLOCKED'
  except Exception as e:return url,None,type(e).__name__
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  for count,(url,item,error)in enumerate(pool.map(download,downloads),1):
   if item:cache[url]=item
   else:errors.append({'url':url,'error':error})
   if count%25==0:dump(HOME/'images.json',cache);print(json.dumps({'mediaRead':count,'mediaPlanned':len(downloads),'errors':len(errors)}),flush=True)
 dump(HOME/'images.json',cache)
 for p,w in zip(products,work):
  for url in w['candidateImageUrls']:
   if url in cache:
    item={**cache[url],'bytes':(HOME/'media'/cache[url]['file']).stat().st_size};w['media'].append(item);p['images'].append('/media/'+p['id']+'/'+str(len(p['images'])))
 out={'schema':1,'sourceTag':'sexogate-marketplaces-v1','products':products,'workbench':work,'sourceCategories':list(categories.values()),'markupPercent':15,'additionalDiscountPercent':0,'allTransferred':False,'imagesReviewed':False,'published':0,'rightsBasis':'user_declaration_2026-11-16','checkoutEnabled':False};dump(HOME/'catalog-source.json',out);dump(HOME/'media-errors.json',errors);print(json.dumps({'sourceDetails':len(products),'sourceCategories':len(categories),'cachedImages':len(cache),'mediaErrors':len(errors),'published':0}),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--snapshot',action='store_true');parser.add_argument('--repair-codes',action='store_true');parser.add_argument('--alternates',action='store_true');args=parser.parse_args()
 if args.snapshot:snapshot()
 elif args.repair_codes:repair_codes()
 generate(args.alternates)
