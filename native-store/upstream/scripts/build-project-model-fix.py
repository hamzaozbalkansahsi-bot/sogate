"""Data-only correction; all product facts and every media byte remain pinned."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1];B=R/'artifacts/cpanel-release-projects-20261110';O=R/'artifacts/cpanel-release-projects-final-20261110';E=R/'artifacts/project-commerce';sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((B/'private/release.json').read_bytes())
for name,h in manifest['files'].items():assert sha((B/name).read_bytes())==h
old=json.loads((B/'private/cabinet-fronts.json').read_bytes());new=json.loads(json.dumps(old))
for p in new['products']:
 if p['productType']=='cabinet-profile':p['modelId']=p['modelId'].replace('model-front-','model-front-accessory-',1)
for a,b in zip(old['products'],new['products']):assert {k:v for k,v in a.items()if k!='modelId'}=={k:v for k,v in b.items()if k!='modelId'}
assert old['assets']==new['assets']and old['review']==new['review']and old['sourceDocuments']==new['sourceDocuments']
new_bytes=(json.dumps(new,ensure_ascii=False,indent=2)+'\n').encode();(R/'data/cabinet-fronts.json').write_bytes(new_bytes)
catalog=json.loads((B/'private/catalog.json').read_bytes());changed={p['id']:p['modelId']for p in new['products']};count=0
for p in catalog['products']:
 if p['id']in changed:
  count+=p['modelId']!=changed[p['id']];p['modelId']=changed[p['id']]
catalog['meta']['frontCatalogVersion']=sha(new_bytes);catalog['meta']['modelCount']=len({p.get('modelId',p['id'])for p in catalog['products']});catalog['meta']['releaseHash']=sha((manifest['releaseHash']+sha(new_bytes)).encode())
patch={'private/catalog.json':json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode(),'private/cabinet-fronts.json':new_bytes}
O.mkdir(exist_ok=True);assert not any(p.is_symlink()for p in O.rglob('*'))
for name in manifest['files']:
 path=O/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/name,path)
for name,body in patch.items():(O/name).write_bytes(body)
hashes={**manifest['files'],**{name:sha(body)for name,body in patch.items()}};fingerprint=hashlib.sha256()
for name in sorted(hashes):fingerprint.update((name+'\0'+hashes[name]+'\0').encode())
final={**manifest,'files':dict(sorted(hashes.items())),'releaseHash':fingerprint.hexdigest(),'workerReleaseHash':catalog['meta']['releaseHash']};(O/'private/release.json').write_text(json.dumps(final,indent=2)+'\n')
proof={'baseReleaseHash':manifest['releaseHash'],'releaseHash':final['releaseHash'],'changedFiles':list(patch)+['private/release.json'],'productFactsAndPricesPreserved':True,'allPublicBytesPreserved':True,'allMediaBytesPreserved':True,'accessoryModelIdsSeparated':count,'output':str(O)};(E/'model-fix-build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
