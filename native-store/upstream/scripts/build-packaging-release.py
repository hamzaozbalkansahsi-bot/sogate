"""Prepare the requested home correction on the latest live, reviewed runtime."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys,urllib.request
R=Path(__file__).resolve().parents[1];E=R/'artifacts/packaging-fix-20261111'
spec=importlib.util.spec_from_file_location('packaging_release',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
with urllib.request.urlopen('https://nodenohome.com/api/health',timeout=40)as response:health=json.load(response)
candidates=[p.parent.parent for p in(R/'artifacts').glob('cpanel-release*/private/release.json')if json.loads(p.read_bytes()).get('releaseHash')==health['releaseHash']];assert len(candidates)==1
B=candidates[0];base=d.load_release(B);O=R/'artifacts/cpanel-release-packaging-20261111-r2';assert not O.exists()
changes={name:(R/'web'/name[7:]).read_bytes()for name in ['public/app.js','public/shop-i18n.js','public/styles.css']}
html=base['all_bytes']['private/index.html'].decode()
for filename in ['app.js','styles.css']:
 html,count=re.subn('/'+re.escape(filename)+r'\?v=[^"\s]+','/'+filename+'?v=nodeno-packaging-20261111-r2',html);assert count==1
changes['private/index.html']=html.encode()
for name in base['manifest']['files']:
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
files={name:hashlib.sha256((O/name).read_bytes()).hexdigest()for name in sorted(base['manifest']['files'])};fp=hashlib.sha256()
for name,value in files.items():fp.update((name+'\0'+value+'\0').encode())
manifest={**base['manifest'],'releaseHash':fp.hexdigest(),'files':files};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':base['manifest']['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'sourcePackage':'artifacts/cpanel-release-packaging-20261111-source-r2','catalogueMediaPricesAndCommerceUnchanged':True,'checkoutEnabledBefore':health['checkoutEnabled']};(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
