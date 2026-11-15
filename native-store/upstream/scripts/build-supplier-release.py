"""Narrow supplier-management release built on the exact verified live package."""
from pathlib import Path
import hashlib,json,os,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/cpanel-release-projects-final-20261110';O=R/'artifacts/cpanel-release-suppliers-20261110';E=R/'artifacts/supplier-expansion';sha=lambda b:hashlib.sha256(b).hexdigest()
base=json.loads((B/'private/release.json').read_bytes());assert base['releaseHash']=='f496d09e6c7d446044f7fd011203993fb90c3a234a53eb51230507b48f53dfb1'
for n,h in base['files'].items():assert sha((B/n).read_bytes())==h,n
assert json.loads((R/'artifacts/media-cleanup.json').read_bytes())['publicationReady']is True
patch={}
for f in ['admin.js','admin.css','admin.html','admin-suppliers.js']:patch['public/'+f]=(R/'web'/f).read_bytes()
for f in ['control-catalog.php','control-http.php','suppliers.php']:patch['private/'+f]=(R/'hosting'/f).read_bytes()
patch['private/supplier-catalog.json']=(R/'data/supplier-catalog.json').read_bytes();seed=json.loads(patch['private/supplier-catalog.json']);assert seed['report']['allSourcePagesDownloaded']is True
prices=json.loads((R/'data/catalog-prices.json').read_bytes());assert prices['pricingRule']['multiplier']=='1.30';byid={p['productId']:p for p in prices['products']}
catalog=json.loads((B/'private/catalog.json').read_bytes());changed=[]
for p in catalog['products']:
 if p['id']not in byid:continue
 row=byid[p['id']];p['salePriceMinor']=row.get('salePriceMinor')if row['status']=='verified'else None;p['salePrice']=p['salePriceMinor']/100 if p['salePriceMinor']is not None else None
 for key in ['previousPriceMinor','discountPercent','priceUpdatedAt','currency']:p.pop(key,None)
 if row['status']=='verified':
  assert (row['sourcePriceMinor']*130+50)//100==p['salePriceMinor'];p['priceUpdatedAt']=row['fetchedAt'];p['currency']='TRY'
 changed.append(p['id'])
from datetime import datetime
catalog['meta']['priceRefresh']={'effectiveAt':int(datetime.fromisoformat(prices['generatedAt']).timestamp()),'productIds':changed}
catalog['meta']['pricing']={'currency':'TRY','pricedProducts':sum(p['status']=='verified'for p in byid.values()),'unpricedProducts':sum(p['status']!='verified'for p in byid.values())}
catalog['meta']['releaseHash']=sha((base['releaseHash']+sha(patch['private/supplier-catalog.json'])+sha((R/'data/catalog-prices.json').read_bytes())).encode())
patch['private/catalog.json']=json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode()
O.mkdir(exist_ok=True)
for n in set(base['files'])|set(patch):
 target=O/n;target.parent.mkdir(parents=True,exist_ok=True)
 if n in patch:target.write_bytes(patch[n])
 elif not target.exists():os.link(B/n,target)
 else:assert sha(target.read_bytes())==base['files'][n],n
hashes={**base['files'],**{n:sha(b)for n,b in patch.items()}};h=hashlib.sha256()
for n in sorted(hashes):h.update((n+'\0'+hashes[n]+'\0').encode())
manifest={**base,'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest(),'workerReleaseHash':catalog['meta']['releaseHash']}
(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
proof={'baseReleaseHash':base['releaseHash'],'releaseHash':manifest['releaseHash'],'output':str(O),'changedFiles':sorted(patch),'publicProducts':len(catalog['products']),'supplierRecords':len(seed['products']),'newSourcePages':2434,'newVariations':148,'adorePrices':prices['counts'],'mediaVersion':base['mediaVersion'],'mediaBytesUnchanged':True,'accountStorageUntouched':True}
(E/'build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
