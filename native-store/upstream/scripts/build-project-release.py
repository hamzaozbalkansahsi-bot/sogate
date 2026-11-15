"""Extend the verified live catalogue without refreshing unrelated supplier prices."""
from pathlib import Path
import hashlib,json,shutil,subprocess,re
from PIL import Image
import importlib.util
R=Path(__file__).resolve().parents[1];BASE=R/'artifacts/cpanel-release-welcome-v2-20261103';OUT=R/'artifacts/cpanel-release-projects-20261110';E=R/'artifacts/project-commerce';E.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();manifest=json.loads((BASE/'private/release.json').read_bytes())
assert manifest['releaseHash']=='f72d422fc4c4b9b99e448374a840ac560c58381b5c45ab52cca27cec17828a5a'and not manifest.get('testOnly')
for name,h in manifest['files'].items():assert (BASE/name).is_file()and not(BASE/name).is_symlink()and sha((BASE/name).read_bytes())==h,name
assert json.loads((R/'artifacts/media-cleanup.json').read_bytes())['publicationReady']is True
spec=importlib.util.spec_from_file_location('owner_gate',R/'lib/owner_media_gate.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate);counts=gate.verify_owner_catalogues(R)
OUT.mkdir(exist_ok=True);patch={}
web=['app.js','shop-core.js','shopping-core.js','shopping-ui.js','furniture-set-core.js','seo-core.js','cabinet-front-core.js','cabinet-front-ui.js','currency.js','door-core.js','door-i18n.js','door-ui.js','door-commerce.css','wholesale.js']
changed={name for name in web if name.endswith('.js')};token='nodeno-projects-20261110-r1'
def imports(body):
 text=body.decode('utf8')
 for name in changed:text=re.sub(r'(\./'+re.escape(name)+r')\?v=[^\'"\s]+',lambda m:m[1]+'?v='+token,text)
 return text.encode('utf8')
# Every importer receives the same cache key for changed modules. Unrelated
# modules keep their verified bytes except for those dependency URLs.
for name in manifest['files']:
 if name.startswith('public/')and name.endswith('.js'):
  b=(R/'web'/name[7:]).read_bytes()if name[7:]in web else(BASE/name).read_bytes();new=imports(b)
  if new!=(BASE/name).read_bytes():patch[name]=new
for name in web:patch['public/'+name]=imports((R/'web'/name).read_bytes())if name.endswith('.js')else(R/'web'/name).read_bytes()
html=(BASE/'private/index.html').read_text(encoding='utf8');html=html.replace(' <main id="page"',' <div id="currency-toolbar" class="currency-toolbar"></div>\n <main id="page"').replace('</head>',' <link rel="stylesheet" href="/door-commerce.css?v='+token+'">\n</head>')
html=re.sub(r'(/app.js)\?v=[^"\s]+',lambda m:m[1]+'?v='+token,html);patch['private/index.html']=html.encode()
for name in ['account.php','social-auth.php','control-catalog.php','wholesale.php','seo.php','door-commerce.php','exchange-rates.php','cabinet-fronts.php']:patch['private/'+name]=(R/'hosting'/name).read_bytes()
patch['public/index.php']=(R/'hosting/index.php').read_bytes()
brand=json.loads((R/'data/brand.json').read_bytes());config=json.loads((BASE/'private/config.json').read_bytes());config['parentCompany']=brand['parentCompany'];patch['private/config.json']=json.dumps(config,ensure_ascii=False).encode()
for filename in ['door-catalog.json','cabinet-fronts.json']:
 d=json.loads((R/'data'/filename).read_bytes());patch['private/'+filename]=(R/'data'/filename).read_bytes()
 for a in d['assets'].values():patch['public'+a['path']]=(R/'web'/a['path'].lstrip('/')).read_bytes()
temp=E/'combined-catalog.json';subprocess.run(['node',str(R/'scripts/append-owner-catalogues.mjs'),str(R),str(BASE/'private/catalog.json'),str(temp)],check=True)
catalog=json.loads(temp.read_bytes());base_catalog=json.loads((BASE/'private/catalog.json').read_bytes());assert catalog['products'][:667]==base_catalog['products']
catalog['meta']['releaseHash']=sha(json.dumps({'base':manifest['releaseHash'],'doors':catalog['meta']['doorCatalogVersion'],'fronts':catalog['meta']['frontCatalogVersion']},sort_keys=True).encode());patch['private/catalog.json']=json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode()
expected=set(manifest['files'])|set(patch)|{'private/release.json'}
assert not any(p.is_symlink()for p in OUT.rglob('*'))and {p.relative_to(OUT).as_posix()for p in OUT.rglob('*')if p.is_file()}<=expected
for name in manifest['files']:
 target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/name,target)
for name,body in patch.items():
 target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
hashes={**manifest['files'],**{name:sha(body)for name,body in patch.items()}};fingerprint=hashlib.sha256()
for name in sorted(hashes):fingerprint.update((name+'\0'+hashes[name]+'\0').encode())
candidate={**manifest,'files':dict(sorted(hashes.items())),'releaseHash':fingerprint.hexdigest(),'workerReleaseHash':catalog['meta']['releaseHash'],'products':len(catalog['products']),'categories':len(catalog['categories']),'ownerCatalogues':counts}
(OUT/'private/release.json').write_text(json.dumps(candidate,indent=2)+'\n',encoding='utf8')
for name in ['media-approved.json','media.json']:assert(OUT/'private'/name).read_bytes()==(BASE/'private'/name).read_bytes()
proof={'baseReleaseHash':manifest['releaseHash'],'releaseHash':candidate['releaseHash'],'products':len(catalog['products']),'furnitureProductsPreserved':667,'ownerCatalogues':counts,'existingPricesAndCampaignsPreserved':True,'accountStorageUntouched':True,'mediaVersion':manifest['mediaVersion'],'publicationReady':True,'output':str(OUT)}
(E/'build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
