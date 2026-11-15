"""Extend the exact live release; preserve customer storage and unrelated operations."""
from pathlib import Path
import hashlib,importlib.util,json,os,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/bianca-20261112';B=R/'artifacts/cpanel-release-brand-reference-20261112-r2';O=R/'artifacts/cpanel-release-paints-20261112-r5'
sha=lambda b:hashlib.sha256(b).hexdigest()
def encoded(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()
def patch_app(body):
 s=body.decode();needle='function productExtraSections(p,ask){';assert s.count(needle)==1
 s="import {renderPaintRecommendations} from './paint-recommendations.js?v=paints-20261112-r5';\n"+s
 needle='return `<section class="detail-section product-questions"';assert s.count(needle)==1
 s=s.replace(needle,'return `${renderPaintRecommendations(p,catalog.products,locale,{esc,renderCard:productCard})}<section class="detail-section product-questions"')
 s=s.replace("${questionLink('questionAssembly')}","${questionLink(p.paintUse?'questionAsk':'questionAssembly')}")
 s=s.replace("${esc(t('assemblyCare'))}","${esc(t(p.paintUse?'viewAllSpecs':'assemblyCare'))}")
 s=s.replace("${esc(t('assemblyCareBody'))}","${esc(p.paintUse?loc(p.paintGuide):t('assemblyCareBody'))}")
 return s.encode()
def main():
 if O.exists():raise RuntimeError('immutable_output_exists')
 base=json.loads((B/'private/release.json').read_bytes());assert base['releaseHash']=='5ced93f0a6240d5ba096d8d2c3248b19de171f0902d3385339cdc96081d3929b'
 for n,h in base['files'].items():assert sha((B/n).read_bytes())==h,n
 prepared=json.loads((E/'catalogue-prepared.json').read_bytes());review=json.loads((E/'media-review.json').read_bytes());assert review['publicationReady']and review['contactSheetsInspected']and not review['testOnly']
 for sheet in review['sheets']:assert sha((R/sheet['file']).read_bytes())==sheet['sha256']
 catalog=json.loads((B/'private/catalog.json').read_bytes());oldids={p['id']for p in catalog['products']};oldcodes={p['code']for p in catalog['products']};assert not oldids.intersection(p['id']for p in prepared['products']);assert not oldcodes.intersection(p['code']for p in prepared['products'])
 raw=set(prepared['unpaintedWoodIds'])
 for p in catalog['products']:
  if p['id']in raw:p.update(finishState='unpainted',paintSurface='wood')
 catalog['products']+=prepared['products'];catalog['categories']+=prepared['categories'];catalog['meta']['paintPublication']={'date':'2026-11-12','products':len(prepared['products']),'reviewedImages':len(prepared['assets']),'source':'Trendyol','markupPercent':30}
 idx=json.loads((B/'private/supplier-details.json').read_bytes());blob=bytearray((B/'private/supplier-details.bin').read_bytes())
 for p in prepared['products']:
  frame=encoded({'id':p['id'],'description':prepared['descriptions'][p['id']]});h=sha(frame);idx['products'][p['id']]={'offset':len(blob),'bytes':len(frame),'sha256':h};blob.extend(frame);p['supplierDetailsHash']=h
 seed=json.loads((B/'private/supplier-catalog.json').read_bytes());supplierids={s['id']for s in seed['suppliers']};offers={p['sourceProductId']:p for p in json.loads((E/'offers.json').read_bytes())['products']}
 for p in prepared['seed']:
  if p['supplierId']not in supplierids:
   merchant=offers[p['sourceVariant']['productId']]['merchant'];seed['suppliers'].append({'id':p['supplierId'],'title':'Trendyol / '+merchant['name'],'url':'https://www.trendyol.com','markupPercent':30,'priceListRequired':False,'merchantId':str(merchant['id']),'verifiedScore':merchant['score'],'authorizedSeller':True});supplierids.add(p['supplierId'])
 seed['products']+=prepared['seed'];seed['paintImport']={'held':prepared['held'],'sourcePending':json.loads((E/'offers.json').read_bytes())['held'],'checkedAt':'2026-11-12'}
 approval=json.loads((B/'private/supplier-media-approved.json').read_bytes());assets={}
 for path,row in prepared['assets'].items():
  body=(R/row['file']).read_bytes();assert sha(body)==row['sha256'];assets['public'+path]=body;approval['images'][path]={'sourceSha256':row['sha256'],'outputSha256':row['sha256'],'visualReview':True,'reviewedAt':'2026-11-12'}
 approval['references']={p['id']+':'+str(i):u for p in catalog['products']if p.get('productType')=='supplier-item'for i,u in enumerate(p['images'])}
 patch={'private/catalog.json':encoded(catalog),'private/supplier-catalog.json':encoded(seed),'private/supplier-details.json':encoded(idx),'private/supplier-details.bin':bytes(blob),'private/supplier-media-approved.json':encoded(approval),'public/app.js':patch_app((B/'public/app.js').read_bytes()),'public/paint-recommendations.js':(R/'web/paint-recommendations.js').read_bytes(),'public/admin-suppliers.js':(R/'web/admin-suppliers.js').read_bytes(),**assets}
 for name in ['suppliers.php','supplier-watch.php','supplier-products.php']:patch['private/'+name]=(R/'hosting'/name).read_bytes()
 for path,module in [('public/admin.js','admin-suppliers.js'),('public/admin.html','admin.js'),('private/index.html','app.js')]:
  old=(B/path).read_text(encoding='utf-8');new,n=re.subn(r'('+re.escape(module)+r'\?v=)[^"\s\x27]+',r'\g<1>paints-20261112-r5',old);assert n>=1,(path,module);patch[path]=new.encode()
 for n in set(base['files'])|set(patch):
  dest=O/n;dest.parent.mkdir(parents=True,exist_ok=True)
  if n in patch:dest.write_bytes(patch[n])
  else:os.link(B/n,dest)
 hashes={**base['files'],**{n:sha(b)for n,b in patch.items()}};h=hashlib.sha256()
 for n in sorted(hashes):h.update((n+'\0'+hashes[n]+'\0').encode())
 manifest={**base,'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest(),'products':len(catalog['products']),'categories':len(catalog['categories'])};(O/'private/release.json').write_bytes(encoded(manifest))
 # Canonical Worker projection and existing approval gates must match the release exactly.
 projection=json.loads((E/'supplier-storefront-before.json').read_bytes());projection['products']=[p for p in catalog['products']if p.get('productType')=='supplier-item'];projection.update(mediaSha256=sha(patch['private/supplier-media-approved.json']),detailIndexSha256=sha(patch['private/supplier-details.json']),detailBlobSha256=sha(patch['private/supplier-details.bin']))
 projection['categories']+=prepared['categories']
 for row in prepared['seed']:projection['priceBindings'][row['id']]={'sourcePriceMinor':row['sourcePriceMinor'],'markupPercent':30,'platform':'trendyol','sourceUrl':row['sourceUrl']}
 for f in ['catalogue-prepared.json','media-review.json','selected-offers.json']:
  path='artifacts/bianca-20261112/'+f;projection['review']['files'].append({'path':path,'sha256':sha((R/path).read_bytes())})
 (R/'data/supplier-storefront.json').write_bytes(encoded(projection))
 for key in ['supplier-catalog.json','supplier-media-approved.json','supplier-details.json','supplier-details.bin']:(R/'data'/key).write_bytes(patch['private/'+key])
 # Source app gets the same narrowly scoped insertion, retaining all other local work.
 source=R/'web/app.js'
 if 'renderPaintRecommendations'not in source.read_text(encoding='utf-8'):
  tmp=source.with_suffix('.tmp');tmp.write_bytes(patch_app(source.read_bytes()));tmp.replace(source)
 proof={'base':str(B.relative_to(R)).replace('\\','/'),'release':str(O.relative_to(R)).replace('\\','/'),'baseReleaseHash':base['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(patch),'newProducts':len(prepared['products']),'newImages':len(assets),'publicProducts':len(catalog['products']),'mediaVersion':base['mediaVersion'],'unpaintedWoodMatches':len(raw),'sourcePending':len(seed['paintImport']['sourcePending']),'reviewHeld':len(prepared['held']),'retailMarkupPercent':30,'customerStoragePreserved':True}
 (E/'release.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in proof.items()if k!='changedFiles'}))
if __name__=='__main__':main()
