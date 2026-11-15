"""Add the welcome UI to the exact verified live release; never rebuild prices."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/cpanel-release-media-20261102-whole-objects'
OUT=ROOT/'artifacts/cpanel-release-welcome-20261103'
EVIDENCE=ROOT/'artifacts/welcome-poster';EVIDENCE.mkdir(exist_ok=True)
sha=lambda body:hashlib.sha256(body).hexdigest()
manifest=json.loads((BASE/'private/release.json').read_bytes())
receipt=json.loads((ROOT/'artifacts/media-object-removal-20261102/deployment.json').read_bytes())
assert manifest['releaseHash']==receipt['releaseHash']=='f08acdc8a42747af23ba302e9aa98b50a5174e84fdc92f99caadde8be4ffa248'
assert json.loads((ROOT/'artifacts/media-cleanup.json').read_bytes())['publicationReady'] is True
assert not manifest.get('testOnly')
for name,digest in manifest['files'].items():
 source=BASE/name
 assert source.is_file() and not source.is_symlink() and sha(source.read_bytes())==digest,name

# Prove that the only storefront source edits are this feature's import and mount.
source=(ROOT/'web/app.js').read_text(encoding='utf8')
before=source.replace("import {mountWelcomePoster} from './welcome-poster.js?v=nodeno-welcome-20261103-r1';\n",'').replace("if(typeof document!=='undefined')void init().then(()=>{\n if(catalogStatus==='ready')mountWelcomePoster({state:()=>({locale,route:currentRoute()})});\n});","if(typeof document!=='undefined')void init();")
assert before==(BASE/'public/app.js').read_text(encoding='utf8'),'Unreviewed app changes outside this feature'

patches={
 'public/app.js':(ROOT/'web/app.js').read_bytes(),
 'public/welcome-poster.js':(ROOT/'web/welcome-poster.js').read_bytes(),
 'public/welcome-poster.css':(ROOT/'web/welcome-poster.css').read_bytes(),
 'public/assets/brand/international-map.svg':(ROOT/'web/assets/brand/international-map.svg').read_bytes()
}
html=(BASE/'private/index.html').read_text(encoding='utf8')
old=' <script type="module" src="/app.js?v=nodeno-market-20261102-r1"></script>'
assert html.count(old)==1 and 'welcome-poster' not in html
html=html.replace(old,' <link rel="stylesheet" href="/welcome-poster.css?v=nodeno-welcome-20261103-r1">\n <script type="module" src="/app.js?v=nodeno-welcome-20261103-r1"></script>')
patches['private/index.html']=html.encode()
expected=set(manifest['files'])|set(patches)|{'private/release.json'}
OUT.mkdir(exist_ok=True)
assert not any(p.is_symlink() for p in OUT.rglob('*'))
assert {p.relative_to(OUT).as_posix()for p in OUT.rglob('*')if p.is_file()}<=expected,'Unexpected files in output'
for name in manifest['files']:
 target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/name,target)
for name,body in patches.items():
 target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
hashes={**manifest['files'],**{name:sha(body)for name,body in patches.items()}}
fingerprint=hashlib.sha256()
for name in sorted(hashes):fingerprint.update((name+'\0'+hashes[name]+'\0').encode())
candidate={**manifest,'files':dict(sorted(hashes.items())),'releaseHash':fingerprint.hexdigest()}
(OUT/'private/release.json').write_text(json.dumps(candidate,indent=2)+'\n',encoding='utf8')
assert (OUT/'private/catalog.json').read_bytes()==(BASE/'private/catalog.json').read_bytes()
proof={'baseReleaseHash':manifest['releaseHash'],'releaseHash':candidate['releaseHash'],'changedFiles':sorted([*patches,'private/release.json']),'catalogueBytesPreserved':True,'accountCodePreserved':True,'mediaVersion':manifest['mediaVersion'],'publicationReady':True,'output':str(OUT)}
(EVIDENCE/'build.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
