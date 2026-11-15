"""Prepare only the product/business editor fix over the exact live release."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/admin-editor-20261112';B=R/'artifacts/cpanel-release-brand-reference-20261112-r2';O=R/'artifacts/cpanel-release-admin-editor-20261112-r1'
BASE='5ced93f0a6240d5ba096d8d2c3248b19de171f0902d3385339cdc96081d3929b'
spec=importlib.util.spec_from_file_location('editor_release',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
base=d.load_release(B);assert base['manifest']['releaseHash']==BASE and d.CpanelBackend().public_health()['releaseHash']==BASE
assert not O.exists()
changes={'private/'+n:(R/'hosting'/n).read_bytes()for n in ['control-catalog.php','control-http.php']}
changes.update({'public/'+n:(R/'web'/n).read_bytes()for n in ['admin.js','admin.html','admin-editor.js']})
for name in sorted(set(base['manifest']['files'])|set(changes)):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
files={n:d.sha256((O/n).read_bytes())for n in sorted(set(base['manifest']['files'])|set(changes))};fp=hashlib.sha256()
for name,digest in files.items():fp.update((name+'\0'+digest+'\0').encode())
manifest={**base['manifest'],'files':files,'releaseHash':fp.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
assert all((O/n).read_bytes()==body for n,body in base['all_bytes'].items()if n not in changes and n!='private/release.json')
proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':BASE,'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'cataloguePricesBrandMediaAndCommerceUnchanged':True}
(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
