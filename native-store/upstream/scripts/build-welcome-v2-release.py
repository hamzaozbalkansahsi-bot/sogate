"""Strict country-map/opt-out UI overlay on the reviewed c828 welcome release."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/cpanel-release-welcome-base-c828'
OUT=ROOT/'artifacts/cpanel-release-welcome-v2-20261103'
EVIDENCE=ROOT/'artifacts/welcome-poster-v2';EVIDENCE.mkdir(exist_ok=True)
sha=lambda body:hashlib.sha256(body).hexdigest()
manifest=json.loads((BASE/'private/release.json').read_bytes())
assert manifest['releaseHash']=='c828f61dd4d92e909ea1cd1f4d1ec0604e2c81f47a7a981fa7efefbd8e11236d'
assert json.loads((ROOT/'artifacts/media-cleanup.json').read_bytes())['publicationReady']is True
assert not manifest.get('testOnly')
for name,digest in manifest['files'].items():
 source=BASE/name;assert source.is_file()and not source.is_symlink()and sha(source.read_bytes())==digest,name
source=(ROOT/'web/app.js').read_text(encoding='utf8')
before=source.replace("./welcome-poster.js?v=nodeno-welcome-20261103-r2","./welcome-poster.js?v=nodeno-welcome-20261103-r1")
assert before==(BASE/'public/app.js').read_text(encoding='utf8'),'Unreviewed app changes outside this feature'
patches={'public/'+name:(ROOT/'web'/name).read_bytes()for name in ['app.js','welcome-poster.js','welcome-poster.css','welcome-country-map.js','welcome-map-data.js']}
html=(BASE/'private/index.html').read_text(encoding='utf8')
assert html.count('nodeno-welcome-20261103-r1')==2
patches['private/index.html']=html.replace('nodeno-welcome-20261103-r1','nodeno-welcome-20261103-r2').encode()
expected=set(manifest['files'])|set(patches)|{'private/release.json'}
OUT.mkdir(exist_ok=True)
assert not any(p.is_symlink()for p in OUT.rglob('*'))
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
(EVIDENCE/'build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
