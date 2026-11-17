#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-marketplace-expansion-payload.py
# Açıklama   : Yeni kaynak dilimini gerçek görsel ve içerik kararlarıyla, eski kayıt kimliklerini koruyarak dondurur.
import hashlib,json,re,shutil,sqlite3
from contextlib import closing
from pathlib import Path
from native_catalog import GROUPS,loc,LANGUAGES
from native_marketplace_taxonomy import classify_marketplace
from native_marketplace_review_rules import apply_review
ROOT=Path(__file__).resolve().parent.parent;BASE=Path('D:/sexogate-local-artifacts-20261114/private-installs')
HOME=BASE/'marketplace-catalog-20261117';FIRST=BASE/'marketplace-catalog-20261116';OLD=BASE/'native-catalog-20261115/prepared'

def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),'utf8');temp.replace(path)

def build():
 selected=ROOT/'.local/native-marketplace-selection.json'
 if selected.exists()and Path(json.loads(selected.read_text('utf8'))['path']).resolve()==(HOME/'prepared').resolve():raise ValueError('SELECTED_DATASET_IS_FROZEN')
 source=json.loads((HOME/'catalog-source.json').read_text('utf8'));reviews={r['id']:r for r in json.loads((HOME/'cover-review.json').read_text('utf8'))}
 audit={r['id']:r for r in json.loads((ROOT/'.local/catalog-expansion-held-audit.json').read_text('utf8'))['products']}
 decisions=json.loads((HOME/'editorial-review.json').read_text('utf8'))
 old=json.loads((OLD/'catalog-data.json').read_text('utf8'));first=json.loads((FIRST/'prepared/catalog-data.json').read_text('utf8'))['products'][2194:];priority={p['id']:n for n,p in enumerate(first)}
 products=list(old['products']);buckets={p.name:json.loads(p.read_text('utf8'))for p in(OLD/'catalog-workbench').glob('*.json')};codes={p['code']for p in products};deferred=[];added=[];media=[];categories={c['id']:c for c in old['categories']}
 with closing(sqlite3.connect(HOME/'research.sqlite'))as db:details={json.loads(row[0])['sourceUrl']:json.loads(row[0])for row in db.execute("SELECT detail_json FROM products WHERE status='ready'")}
 frozen_db=FIRST/'research.sqlite';frozen_wal=Path(str(frozen_db)+'-wal')
 if frozen_wal.exists()and frozen_wal.stat().st_size:raise ValueError('FROZEN_SOURCE_HAS_ACTIVE_WAL')
 with closing(sqlite3.connect(frozen_db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True))as db:audited_details={json.loads(row[0])['sourceUrl']:json.loads(row[0])for row in db.execute("SELECT detail_json FROM products WHERE status='ready'")}
 rows=sorted(zip(source['products'],source['workbench']),key=lambda pair:(priority.get(pair[0]['id'],100000),pair[0]['id']))
 for p,w in rows:
  assert p['id']==w['id']and p['catalogOrigin']=='sexogate-marketplaces-v1'and not p['published']and p['hidden']and p['stockQuantity']is None
  if not p['code']or p['code']in codes or p['salePriceMinor']is None:
   deferred.append({'id':p['id'],'sourceUrl':w['source']['url'],'code':p['code'],'reason':'source_code_missing'if not p['code']else'source_code_collision'if p['code']in codes else'source_price_missing'});continue
  codes.add(p['code']);detail=details[w['source']['url']];decision=decisions.get(p['id'],{});entry=dict(audit.get(p['id'],{}))
  if decision:
   original=audited_details.get(w['source']['url']);assert original and p['id']in audit,'AUDITED_SOURCE_REQUIRED'
   entry['rawSha256']=entry.get('rawSha256')or(entry.get('priceWinnerEvidence')or{}).get('sha256')or original['sourceSha256']
  p,w=apply_review(p,w,detail,(HOME/'raw'/(detail['sourceId']+'.html')).read_bytes()if decision else b'',decision,entry)
  if not w.get('copyReviewApplied')and any(str(c.get('id'))=='5242'for c in w['sourceCategories'])and re.search(r'prezervatif|kondom|condom',w['rawSourceTitle'],re.I):
   w['reviewHolds'].append('sleeve_contraceptive_identity_claim_review');p['eligibilityHold']=w['eligibilityHold']=True
  classification=classify_marketplace(w['rawSourceTitle'],w['sourceCategories'],w['source']['vendor']);w['taxonomyReview']=classification
  if classification['needsReview']:w['reviewHolds'].append('category_identity_review');w['eligibilityHold']=p['eligibilityHold']=True
  else:
   previous=w['group'];group=classification['group']
   if group!=previous:
    for field in ['name','modelName','description','seoTitle','seoDescription']:p[field]={lang:text.replace(loc(GROUPS[previous])[lang],loc(GROUPS[group])[lang])for lang,text in p[field].items()}
   w['group']=group;p['categoryIds']=classification['categoryIds'];categories.update({c['id']:c for c in classification['categories']})
  r=reviews[p['id']];approved=r['approvedIndices'];assert isinstance(approved,list)and len(set(approved))==len(approved)
  for index in approved:
   assert type(index)is int and 0<=index<len(w['media'])and r['imageHashes'][index]==w['media'][index]['sha256']and w['media'][index]['originalBytesPreserved']is True
  p['visualApprovedIndices']=approved;p['coverIndex']=approved[0]if approved else 0;w['publicationApproved']=bool(approved);w['coverReview']=r
  p['referencePriceVerified']=False;p['additionalDiscountPercent']=0;w['reviewHolds']=sorted(set(w['reviewHolds']));products.append(p);added.append(p['id']);media.extend(w['media']);buckets.setdefault(p['id'].rsplit('_',1)[1][:2]+'.json',{})[p['id']]=w
 assert products[:2194]==old['products'],'LEGACY_CATALOG_CHANGED'
 assert set(priority).issubset(added),'FIRST_IMPORTED_PRODUCT_LOST'
 dependencies=[OLD/'catalog-data.json',HOME/'catalog-source.json',HOME/'cover-review.json',HOME/'editorial-review.json',Path(__file__),ROOT/'scripts/native_marketplace_taxonomy.py',ROOT/'scripts/native_marketplace_review_rules.py']
 dataset=hashlib.sha256(b''.join(p.read_bytes()for p in dependencies)).hexdigest()[:32];prepared=HOME/'prepared';prepared.mkdir(exist_ok=True)
 for name,bucket in buckets.items():dump(prepared/'catalog-workbench'/name,bucket)
 manifest=json.loads((OLD/'catalog-sources.json').read_text('utf8'));manifest.update(dataset=dataset,products=len(products),sourceCategories=manifest['sourceCategories']+source['sourceCategories'],storeCategories=len(categories),markupPercent=None,pricingSummary='Yeni pazaryeri ürünlerinde kaynak indirimsiz fiyat +%15 nihai satış fiyatı; ek kampanya indirimi yok. Eski arşiv ve yönetici fiyatları korunur.',marketplaceProducts=len(added),marketplaceFetched=len(source['products']),marketplaceDeferred=deferred,allMarketplaceProductsTransferred=False)
 manifest['sources'].extend([{'vendor':'trendyol','file':'individual_product_pages','sha256':hashlib.sha256((HOME/'catalog-source.json').read_bytes()).hexdigest(),'products':len(added),'markupPercent':15,'additionalDiscountPercent':0},{'vendor':'hepsiburada','products':0,'state':'individual_http_403'}])
 dump(prepared/'catalog-sources.json',manifest);dump(prepared/'catalog-data.json',{'products':products,'categories':list(categories.values()),'catalogOrigin':'sexogate-catalog-v2','dataset':dataset});shutil.copy2(OLD/'catalog-spec-labels.json',prepared/'catalog-spec-labels.json')
 all_media=json.loads((OLD/'media-manifest.json').read_text('utf8'))+media;dump(prepared/'media-manifest.json',list({m['file']:m for m in all_media}.values()))
 report={'prepared':True,'dataset':dataset,'newProducts':len(added),'deferred':len(deferred),'fetched':len(source['products']),'publishCandidates':sum(p['id']in added and not p['eligibilityHold']and bool(p['visualApprovedIndices'])and bool(p['salePriceMinor'])for p in products),'archivedRecordsPreserved':2194,'storeCategories':len(categories),'published':0,'fullCatalogue':False}
 dump(ROOT/'.local/native-marketplace-selection.json',{'path':str(prepared),'dataset':dataset,'sha256':hashlib.sha256((prepared/'catalog-data.json').read_bytes()).hexdigest(),'products':len(products),'newProducts':len(added),'sourceProducts':len(source['products']),'mediaRoot':str(HOME/'media'),'legacyMediaRoot':str(BASE/'native-catalog-20261115/media')});dump(ROOT/'.local/native-marketplace-payload.json',report);print(json.dumps(report),flush=True)
if __name__=='__main__':build()
