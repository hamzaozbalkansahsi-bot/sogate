"""Align short help with the already published legal policies; preserve tested checkout code."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys,urllib.request
R=Path(__file__).resolve().parents[1];E=R/'artifacts/legal-20261110';old=json.loads((E/'release-preparation.json').read_bytes());assert old['release'].endswith('-r3')
spec=importlib.util.spec_from_file_location('legal_copy_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d);B=R/old['release'];base=d.load_release(B)
with urllib.request.urlopen('https://nodenohome.com/api/health',timeout=30)as response:assert json.load(response)['releaseHash']==base['manifest']['releaseHash']
O=R/'artifacts/cpanel-release-legal-20261110-r4';assert not O.exists()
app=base['all_bytes']['public/app.js'].replace(b'shop-i18n.js?v=nodeno-legal-20261110-r1',b'shop-i18n.js?v=nodeno-legal-20261110-r2');assert app!=base['all_bytes']['public/app.js']
html=base['all_bytes']['private/index.html'].replace(b'app.js?v=nodeno-legal-20261110-r1',b'app.js?v=nodeno-legal-20261110-r2');assert html!=base['all_bytes']['private/index.html']
changes={'public/app.js':app,'public/shop-i18n.js':(R/'web/shop-i18n.js').read_bytes(),'private/index.html':html}
for name in base['manifest']['files']:
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
hashes={name:hashlib.sha256((O/name).read_bytes()).hexdigest()for name in sorted(base['manifest']['files'])};fingerprint=hashlib.sha256()
for name,digest in hashes.items():fingerprint.update((name+'\0'+digest+'\0').encode())
manifest={**base['manifest'],'releaseHash':fingerprint.hexdigest(),'files':hashes};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
(E/'release-r3-preparation.json').write_text(json.dumps(old,indent=2)+'\n');record={'prepared':True,'base':str(B.relative_to(R)),'release':str(O.relative_to(R)),'baseReleaseHash':base['manifest']['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'sourceEvidenceRelease':str(B.relative_to(R)),'catalogueAndMediaUnchanged':True,'liveCheckoutPreserved':True,'shortHelpAlignedWithPublishedPolicies':True};(E/'release-preparation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
