"""Correct only the server RSS transport in the already accepted social release."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-engine-20261112';B=R/'artifacts/cpanel-release-social-engine-20261112-r5';O=R/'artifacts/cpanel-release-social-engine-20261112-r6'
spec=importlib.util.spec_from_file_location('trend_release_backend',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
base=d.load_release(B);expected='92909677fb6c9aa42c548c53dc2077818d1a1455f7bf4e8ff3c66edfabde4b41';assert base['manifest']['releaseHash']==expected and d.CpanelBackend(allow_writes=False).public_health()['releaseHash']==expected
assert not O.exists(),'do not overwrite immutable release'
for name in base['manifest']['files']:
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name=='private/social-worker.php':target.write_bytes((R/'hosting/social-worker.php').read_bytes())
 else:os.link(B/name,target)
hashes={name:d.sha256((O/name).read_bytes())for name in sorted(base['manifest']['files'])};fingerprint=hashlib.sha256()
for name,digest in hashes.items():fingerprint.update((name+'\0'+digest+'\0').encode())
manifest={**base['manifest'],'files':hashes,'releaseHash':fingerprint.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');new=d.load_release(O)
assert {n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b}=={'private/social-worker.php','private/release.json'}
old=json.loads((E/'release.json').read_bytes());(E/'initial-release.json').write_text(json.dumps(old,indent=2)+'\n');(E/'initial-deployment.json').write_bytes((E/'deployment.json').read_bytes())
proof={**old,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':expected,'releaseHash':manifest['releaseHash'],'changedFiles':['private/social-worker.php'],'correction':'rss_transport'};(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
