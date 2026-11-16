#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-marketplace-payload.py
# Açıklama   : Pazaryeri incelemesini eski arşiv kayıtlarını koruyan, fiyat/medya kanıtlı özel pakete dönüştürür.
import hashlib,json,re,shutil
from pathlib import Path
from native_catalog import GROUPS,loc,fold
from native_catalog_taxonomy import apply_taxonomy
from native_marketplaces import marketplace_group,marketplace_claim_review
ROOT=Path(__file__).resolve().parent.parent;BASE=Path('D:/sexogate-local-artifacts-20261114/private-installs')
HOME=BASE/'marketplace-catalog-20261116';OLD=BASE/'native-catalog-20261115/prepared';source=json.loads((HOME/'catalog-source.json').read_text('utf8'));review=json.loads((HOME/'cover-review.json').read_text('utf8'));reviews={r['id']:r for r in review}
old=json.loads((OLD/'catalog-data.json').read_text('utf8'));assert len(old['products'])==2194 and old['catalogOrigin']=='sexogate-suppliers-v1'
products=list(old['products']);buckets={p.name:json.loads(p.read_text('utf8'))for p in(OLD/'catalog-workbench').glob('*.json')};work=[w for bucket in buckets.values()for w in bucket.values()];codes={p['code']for p in products};deferred=[];added=[]
for p,w in zip(source['products'],source['workbench']):
 assert p['id']==w['id']and p['catalogOrigin']=='sexogate-marketplaces-v1'and not p['published']and p['hidden']and p['stockQuantity']is None
 if not p['code']or p['code']in codes:
  deferred.append({'id':p['id'],'sourceUrl':w['source']['url'],'code':p['code'],'reason':'source_code_missing'if not p['code']else'source_code_collision'});continue
 codes.add(p['code']);r=reviews[p['id']];assert r['sha256']==w['media'][0]['sha256']and r['originalBytesChanged']is False
 group=marketplace_group(p['name']['tr'],w['sourceCategories']);previous=w['group']
 if group!=previous:
  for field in ['modelName','name','description','seoTitle','seoDescription']:
   p[field]={lang:value.replace(loc(GROUPS[previous])[lang],loc(GROUPS[group])[lang])for lang,value in p[field].items()}
 w['group']=group;p['categoryIds']=['sg_'+group]
 if marketplace_claim_review(p['name']['tr']):p['eligibilityHold']=w['eligibilityHold']=True;w['reviewHolds'].append('manufacturer_claim_review')
 p['visualApprovedIndices']=[0]if r['coverApproved']else[];w['publicationApproved']=bool(p['visualApprovedIndices']);w['coverReview']=r
 p['referencePriceVerified']=False;p['additionalDiscountPercent']=0
 work.append(w);products.append(p);added.append(p['id']);key=p['id'].rsplit('_',1)[1][:2]+'.json';buckets.setdefault(key,{})[p['id']]=w
data={'products':products,'categories':old['categories'],'workbench':work};categories=apply_taxonomy(data);assert products[:2194]==old['products'],'LEGACY_CATALOG_CHANGED'
games=loc(['Çift Oyunları','Couples Games','Игры для пар','ألعاب للأزواج','Spiele für Paare','Cüt oyunları','Жұптарға арналған ойындар','Jübüt oýunlary','Juftliklar o‘yinlari','Жубайлар оюндары','بازی‌های زوج‌ها'])
gameIds=[]
for p in products:
 if p['id']in added and p['categoryIds'][0]=='sg_couples'and re.search(r'\b(?:zar|kamasutra|kart|tombala)\b|denge oyunu',fold(p['name']['tr'])):p['categoryIds']=['sg_couples','sg_couples_games'];gameIds.append(p['id'])
if gameIds and not any(c['id']=='sg_couples_games'for c in categories):categories.append({'id':'sg_couples_games','parentId':'sg_couples','name':games,'slug':'couples-games'})
dataset=hashlib.sha256((OLD/'catalog-data.json').read_bytes()+(HOME/'catalog-source.json').read_bytes()+(HOME/'cover-review.json').read_bytes()+Path(__file__).read_bytes()+(ROOT/'scripts/native_catalog_taxonomy.py').read_bytes()+(ROOT/'scripts/native_marketplaces.py').read_bytes()).hexdigest()[:32];prepared=HOME/'prepared';prepared.mkdir(exist_ok=True);(prepared/'catalog-workbench').mkdir(exist_ok=True)
dump=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),'utf8')
for name,bucket in buckets.items():dump(prepared/'catalog-workbench'/name,bucket)
manifest=json.loads((OLD/'catalog-sources.json').read_text('utf8'));manifest.update(dataset=dataset,products=len(products),sourceCategories=manifest['sourceCategories']+source['sourceCategories'],storeCategories=len(categories),markupPercent=None,pricingSummary='Yeni pazaryeri ürünlerinde kaynak indirimsiz fiyat +%15 nihai satış fiyatı; ek kampanya indirimi yok. Önceki arşiv kayıtları ve yönetici fiyatları korunur.',marketplaceProducts=len(added),marketplaceFetched=len(source['products']),marketplaceDeferred=deferred,allMarketplaceProductsTransferred=False)
manifest['sources'].append({'vendor':'trendyol','file':'individual_product_pages','sha256':hashlib.sha256((HOME/'catalog-source.json').read_bytes()).hexdigest(),'products':len(added),'markupPercent':15,'additionalDiscountPercent':0});manifest['sources'].append({'vendor':'hepsiburada','products':0,'state':'individual_http_403'})
dump(prepared/'catalog-sources.json',manifest);dump(prepared/'catalog-data.json',{'products':products,'categories':categories,'catalogOrigin':'sexogate-catalog-v2','dataset':dataset});shutil.copy2(OLD/'catalog-spec-labels.json',prepared/'catalog-spec-labels.json')
allMedia=json.loads((OLD/'media-manifest.json').read_text('utf8'))+[image for w in source['workbench']for image in w['media']];dump(prepared/'media-manifest.json',list({m['file']:m for m in allMedia}.values()))
dump(ROOT/'.local/native-marketplace-selection.json',{'path':str(prepared),'dataset':dataset,'sha256':hashlib.sha256((prepared/'catalog-data.json').read_bytes()).hexdigest(),'products':len(products),'newProducts':len(added),'sourceProducts':len(source['products']),'mediaRoot':str(HOME/'media'),'legacyMediaRoot':str(BASE/'native-catalog-20261115/media')})
report={'prepared':True,'newProducts':len(added),'deferred':len(deferred),'fetched':len(source['products']),'publishCandidates':sum(p['id']in added and not p['eligibilityHold']and bool(p['visualApprovedIndices'])for p in products),'archivedRecordsPreserved':2194,'published':0,'fullCatalogue':False}
dump(ROOT/'.local/native-marketplace-payload.json',report);print(json.dumps(report))
