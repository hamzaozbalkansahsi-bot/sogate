"""Apply the measurement UI/runtime delta to the verified live release.

Supplier prices, catalogue facts, media, accounts and FX job are not rebuilt.
"""
from pathlib import Path
import json,hashlib,re,shutil,importlib.util,subprocess
R=Path(__file__).resolve().parents[1];B=R/'artifacts/cpanel-release-checkout-alignment-20261110';O=R/'artifacts/cpanel-release-measurements-20261110';E=R/'artifacts/measurement-orders';E.mkdir(exist_ok=True)
sha=lambda value:hashlib.sha256(value).hexdigest();manifest=json.loads((B/'private/release.json').read_bytes())
assert manifest['releaseHash']=='f2ece0ebe194b0fc997ff9a5db256605b948d18bf29694200f7f0b3f90c72109'
for name,h in manifest['files'].items():assert sha((B/name).read_bytes())==h,name
explicit=['app.js','door-core.js','door-ui.js','measurement-core.js','measurement-ui.js','measurement-i18n.js','door-commerce.css']
source={name[7:]:(B/name).read_bytes()for name in manifest['files']if name.startswith('public/')and name.endswith('.js')}
source.update({name:(R/'web'/name).read_bytes()for name in explicit if name.endswith('.js')});changed={name for name in explicit if name.endswith('.js')};token='nodeno-measurements-20261110-r1'
while True:
 before=set(changed)
 for name,body in source.items():
  if any(re.search(rb'\./'+re.escape(dep.encode())+rb'(?:\?v=[^\s\'\"]+)?[\'\"]',body)for dep in before):changed.add(name)
 if changed==before:break
patch={}
for name in changed:
 body=source[name]
 for dep in changed:body=re.sub(rb'(\./'+re.escape(dep.encode())+rb')(?:\?v=[^\s\'\"]+)?(?=[\'\"])',lambda m:m[1]+b'?v='+token.encode(),body)
 patch['public/'+name]=body
patch['public/door-commerce.css']=(R/'web/door-commerce.css').read_bytes();patch['private/door-commerce.php']=(R/'hosting/door-commerce.php').read_bytes()
catalog_output=E/'customer-catalog.json';subprocess.run(['node',str(R/'scripts/apply-door-measurement-policy.mjs'),str(B/'private/catalog.json'),str(catalog_output)],check=True);patch['private/catalog.json']=catalog_output.read_bytes()
html=(B/'private/index.html').read_bytes()
for name in ['app.js','door-commerce.css']:html=re.sub(rb'(/'+re.escape(name.encode())+rb')\?v=[^\"\s]+',lambda m:m[1]+b'?v='+token.encode(),html)
patch['private/index.html']=html
O.mkdir(exist_ok=True);assert not any(p.is_symlink()for p in O.rglob('*'))
for name in manifest['files']:
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/name,target)
for name,body in patch.items():target=O/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
hashes={**manifest['files'],**{name:sha(body)for name,body in patch.items()}};fingerprint=hashlib.sha256()
for name in sorted(hashes):fingerprint.update((name+'\0'+hashes[name]+'\0').encode())
final={**manifest,'files':dict(sorted(hashes.items())),'releaseHash':fingerprint.hexdigest()};(O/'private/release.json').write_text(json.dumps(final,indent=2)+'\n')
for name in ['config.json','media.json','media-approved.json','door-catalog.json','cabinet-fronts.json']:assert(O/'private'/name).read_bytes()==(B/'private'/name).read_bytes()
before=json.loads((B/'private/catalog.json').read_bytes());after=json.loads(patch['private/catalog.json'])
for a,b in zip(before['products'],after['products']):
 if a.get('productType')!='door':assert a==b
 else:
  assert {k:v for k,v in a.items()if k not in ['description','door']}=={k:v for k,v in b.items()if k not in ['description','door']}
  assert {k:v for k,v in a['door'].items()if k!='baseFrameDepthMaxCm'}=={k:v for k,v in b['door'].items()if k!='baseFrameDepthMaxCm'}
assert all((O/name).read_bytes()==(B/name).read_bytes()for name in manifest['files']if '/assets/'in name)
spec=importlib.util.spec_from_file_location('measurement_owner_gate',R/'lib/owner_media_gate.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate);gate.verify_owner_catalogues(R)
result={'baseReleaseHash':manifest['releaseHash'],'releaseHash':final['releaseHash'],'changedFiles':sorted(patch),'sourcePricesAndProductIdentitiesPreserved':True,'ownerFramePolicyAppliedToDescriptions':True,'allMediaBytesPreserved':True,'privateStorageUntouched':True,'output':str(O)};(E/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
