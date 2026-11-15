"""Correct coffee-colour disambiguation; preserve all accepted frontend bytes."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/admin-mobile-social-20261112';B=R/'artifacts/cpanel-release-admin-mobile-social-20261112-r1';O=R/'artifacts/cpanel-release-admin-mobile-social-20261112-r2'
spec=importlib.util.spec_from_file_location('home_topic_backend',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
base=d.load_release(B);expected='8727a68aef1301e322d908b87c4e70eac189d99bbc0a550f55efb7eb37530965';assert base['manifest']['releaseHash']==expected and d.CpanelBackend(allow_writes=False).public_health()['releaseHash']==expected;assert not O.exists()
for name in base['manifest']['files']:
 t=O/name;t.parent.mkdir(parents=True,exist_ok=True)
 if name=='private/social-campaigns.php':t.write_bytes((R/'hosting/social-campaigns.php').read_bytes())
 else:os.link(B/name,t)
hashes={n:d.sha256((O/n).read_bytes())for n in sorted(base['manifest']['files'])};fp=hashlib.sha256()
for n,digest in hashes.items():fp.update((n+'\0'+digest+'\0').encode())
manifest={**base['manifest'],'files':hashes,'releaseHash':fp.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
old=json.loads((E/'release.json').read_bytes());(E/'initial-release.json').write_text(json.dumps(old,indent=2)+'\n');(E/'initial-deployment.json').write_bytes((E/'deployment.json').read_bytes())
proof={**old,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':expected,'releaseHash':manifest['releaseHash'],'changedFiles':['private/social-campaigns.php'],'correction':'coffee_colour'};(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'prepared':True,'releaseHash':proof['releaseHash']}))
