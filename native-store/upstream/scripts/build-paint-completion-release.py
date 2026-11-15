"""Append reviewed paint variants to the exact current live release."""
from pathlib import Path
import hashlib,json,os,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/paint-completion-20261112';O=R/'artifacts/cpanel-release-paint-completion-20261112-r1'
INCLUDE_ADMIN=True
sha=lambda b:hashlib.sha256(b).hexdigest()
def encoded(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()
def main():
 if O.exists():raise RuntimeError('immutable_output_exists')
 baseproof=json.loads((E/'base.json').read_bytes());B=R/baseproof['releases'][0];base=json.loads((B/'private/release.json').read_bytes());assert base['releaseHash']==baseproof['health']['releaseHash']
 for n,h in base['files'].items():assert sha((B/n).read_bytes())==h,n
 prepared=json.loads((E/'catalogue-prepared.json').read_bytes());review=json.loads((E/'visual-review.json').read_bytes());assert review['passed']and not review['testOnly']
 for sheet in review['sheets']:assert sha((R/sheet['file']).read_bytes())==sheet['sha256']
 assert review['products']==len(prepared['products'])and review['images']==len(prepared['assets'])
 catalog=json.loads((B/'private/catalog.json').read_bytes());oldids={p['id']for p in catalog['products']};oldcodes={p['code']for p in catalog['products']};assert not oldids.intersection(p['id']for p in prepared['products']);assert not oldcodes.intersection(p['code']for p in prepared['products'])
 oldcats={c['id']for c in catalog['categories']};newcats=[c for c in prepared['categories']if c['id']not in oldcats];catalog['products']+=prepared['products'];catalog['categories']+=newcats
 catalog['meta']['paintPublication']={'date':'2026-11-12','products':sum(p['id'].startswith('paint-ty-')for p in catalog['products']),'reviewedImages':len(prepared['assets']),'source':'Trendyol','markupPercent':30}
 idx=json.loads((B/'private/supplier-details.json').read_bytes());blob=bytearray((B/'private/supplier-details.bin').read_bytes())
 for p in prepared['products']:
  frame=encoded({'id':p['id'],'description':prepared['descriptions'][p['id']]});h=sha(frame);idx['products'][p['id']]={'offset':len(blob),'bytes':len(frame),'sha256':h};blob.extend(frame);p['supplierDetailsHash']=h
 seed=json.loads((B/'private/supplier-catalog.json').read_bytes());supplierids={s['id']for s in seed['suppliers']};offers={p['sourceProductId']:p for p in json.loads((E/'offers.json').read_bytes())['products']}
 for p in prepared['seed']:
  if p['supplierId']not in supplierids:
   offer=offers[p['sourceVariant']['productId']];merchant=offer['merchant'];seed['suppliers'].append({'id':p['supplierId'],'title':'Trendyol / '+merchant['name'],'url':'https://www.trendyol.com','markupPercent':30,'priceListRequired':False,'merchantId':str(merchant['id']),'verifiedScore':merchant['score'],'authorizedSeller':bool(merchant['authorized']),'manufacturerVerification':offer.get('merchantVerification')});supplierids.add(p['supplierId'])
 seed['products']+=prepared['seed'];reviewrows=json.loads((E/'review-list.json').read_bytes());seed['paintImport']={'held':[r for r in reviewrows if r['group']!='source'],'sourcePending':[r for r in reviewrows if r['group']=='source'],'reviewRows':reviewrows,'checkedAt':json.loads((E/'selected-offers.json').read_bytes())['checkedAt']}
 approval=json.loads((B/'private/supplier-media-approved.json').read_bytes());assets={}
 for path,row in prepared['assets'].items():
  body=(R/row['file']).read_bytes();assert sha(body)==row['sha256'];assets['public'+path]=body;approval['images'][path]={'sourceSha256':row['sha256'],'outputSha256':row['sha256'],'visualReview':True,'reviewedAt':'2026-11-12'}
 approval['references']={p['id']+':'+str(i):u for p in catalog['products']if p.get('productType')=='supplier-item'for i,u in enumerate(p['images'])}
 patch={'private/catalog.json':encoded(catalog),'private/supplier-catalog.json':encoded(seed),'private/supplier-details.json':encoded(idx),'private/supplier-details.bin':bytes(blob),'private/supplier-media-approved.json':encoded(approval),'private/suppliers.php':(R/'hosting/suppliers.php').read_bytes(),'private/supplier-watch.php':(R/'hosting/supplier-watch.php').read_bytes(),'public/admin-suppliers.js':(R/'web/admin-suppliers.js').read_bytes(),'public/date-time.js':(R/'web/date-time.js').read_bytes(),**assets}
 for path,module in [('public/admin.js','admin-suppliers.js'),('public/admin.html','admin.js')]:
  old=(B/path).read_text(encoding='utf-8');new,n=re.subn(r'('+re.escape(module)+r'\?v=)[^"\s\x27]+',r'\g<1>paint-completion-20261112-r1',old);assert n>=1;patch[path]=new.encode()
 patch={n:b for n,b in patch.items()if not(B/n).exists()or(B/n).read_bytes()!=b}
 if not INCLUDE_ADMIN:patch={n:b for n,b in patch.items()if n.startswith('public/assets/')or n in ['private/catalog.json','private/supplier-catalog.json','private/supplier-details.json','private/supplier-details.bin','private/supplier-media-approved.json']}
 for n in set(base['files'])|set(patch):
  dest=O/n;dest.parent.mkdir(parents=True,exist_ok=True)
  if n in patch:dest.write_bytes(patch[n])
  else:os.link(B/n,dest)
 hashes={**base['files'],**{n:sha(b)for n,b in patch.items()}};h=hashlib.sha256()
 for n in sorted(hashes):h.update((n+'\0'+hashes[n]+'\0').encode())
 manifest={**base,'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest(),'products':len(catalog['products']),'categories':len(catalog['categories'])};(O/'private/release.json').write_bytes(encoded(manifest))
 projectionpath=R/'data/supplier-storefront.json';before=projectionpath.read_bytes();projection=json.loads(before)
 assert projection['products']==[p for p in json.loads((B/'private/catalog.json').read_bytes())['products']if p.get('productType')=='supplier-item'],'canonical_base_changed'
 (E/'supplier-storefront-before.json').write_bytes(before);projection['products']=[p for p in catalog['products']if p.get('productType')=='supplier-item'];projection.update(mediaSha256=sha(patch['private/supplier-media-approved.json']),detailIndexSha256=sha(patch['private/supplier-details.json']),detailBlobSha256=sha(patch['private/supplier-details.bin']));projection['categories']+=newcats
 for row in prepared['seed']:projection['priceBindings'][row['id']]={'sourcePriceMinor':row['sourcePriceMinor'],'markupPercent':30,'platform':'trendyol','sourceUrl':row['sourceUrl']}
 for f in ['catalogue-prepared.json','media-review.json','selected-offers.json','visual-review.json']+(['trusted-merchants.json','manufacturer-documents.json','decisions.json']if E.name=='paint-alternatives-20261112'else[]):
  path=E.relative_to(R).as_posix()+'/'+f;projection['review']['files'].append({'path':path,'sha256':sha((R/path).read_bytes())})
 projectionpath.write_bytes(encoded(projection))
 for name in ['supplier-catalog.json','supplier-media-approved.json','supplier-details.json','supplier-details.bin']:(R/'data'/name).write_bytes(patch['private/'+name])
 for path in prepared['assets']:
  dest=R/'web'/path.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(assets['public'+path])
 proof={'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':base['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(patch),'newProducts':len(prepared['products']),'newImages':len(assets),'publicProducts':len(catalog['products']),'mediaVersion':base['mediaVersion'],'customerStoragePreserved':True}
 (E/'release.json').write_bytes(encoded(proof));print(json.dumps(proof))
if __name__=='__main__':main()
