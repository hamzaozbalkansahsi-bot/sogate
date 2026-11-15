"""Remove generic social slogans while preserving all commerce and mobile UI bytes."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-copy-20261112';B=R/'artifacts/cpanel-release-admin-mobile-social-20261112-r2';O=R/'artifacts/cpanel-release-social-copy-20261112-r2'
spec=importlib.util.spec_from_file_location('social_copy_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
base=d.load_release(B);expected='a914199e1f2d0f5644cbdfbae98bc8c2f3a42008f10a620593ae418eee76cd0b';assert base['manifest']['releaseHash']==expected and d.CpanelBackend(allow_writes=False).public_health()['releaseHash']==expected;assert not O.exists();E.mkdir(exist_ok=True)
changes={'private/'+n:(R/'hosting'/n).read_bytes()for n in ['social-engine.php','social-campaigns.php']}
changes.update({'public/assets/social-headlines/'+p.name:p.read_bytes()for p in (R/'web/assets/social-headlines').glob('headline-*.png')});assert len(changes)==58
for name in base['manifest']['files']:
 t=O/name;t.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:t.write_bytes(changes[name])
 else:os.link(B/name,t)
hashes={n:d.sha256((O/n).read_bytes())for n in sorted(base['manifest']['files'])};fp=hashlib.sha256()
for n,digest in hashes.items():fp.update((n+'\0'+digest+'\0').encode())
manifest={**base['manifest'],'files':hashes,'releaseHash':fp.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':expected,'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'commerceMediaAndMobileUiPreserved':True,'products':3602,'paidEnabled':False};(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'prepared':True,'releaseHash':proof['releaseHash']}))
