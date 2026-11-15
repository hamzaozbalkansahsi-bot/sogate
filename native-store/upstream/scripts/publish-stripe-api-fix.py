"""Publish the real-provider verified Stripe form fix; no public assets or persistent data change."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,secrets,sys,subprocess
R=Path(__file__).resolve().parents[1];E=R/'artifacts/stripe-checkout-20261110'
spec=importlib.util.spec_from_file_location('nodeno_stripe_fix_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
B=R/'artifacts/cpanel-release-stripe-20261110';O=R/'artifacts/cpanel-release-stripe-api-20261110';base=d.load_release(B);assert base['manifest']['releaseHash']=='a554e1db68f0f9bc726642f212e98e7273c8642e2ea98e60b1a6bf35c8d3e4e5'
probe=json.loads((E/'live-exact-form-preflight.json').read_bytes());assert probe['passed']is True and probe['live']is True and probe['phpGeneratedForm']is True and probe['realCharges']==0 and probe['paymentStatus']=='unpaid'
assert '\u2139 fail 0'in(E/'connection-tests.log').read_text(encoding='utf8')
O.mkdir(exist_ok=True)
for name,body in base['all_bytes'].items():
 if name=='private/release.json':continue
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():os.link(B/name,target)
replacement=(R/'hosting/payment-stripe.php').read_bytes();target=O/'private/payment-stripe.php'
if target.exists():target.unlink()
target.write_bytes(replacement);hashes={**base['manifest']['files'],'private/payment-stripe.php':hashlib.sha256(replacement).hexdigest()};h=hashlib.sha256()
for name in sorted(hashes):h.update((name+'\0'+hashes[name]+'\0').encode())
manifest={**base['manifest'],'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest()};target=O/'private/release.json'
if target.exists():target.unlink()
target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');new=d.load_release(O)
for name,body in base['all_bytes'].items():
 if name not in ['private/payment-stripe.php','private/release.json']:assert body==new['all_bytes'][name],name
subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(O)],check=True)
media=json.loads((E/'media-identity-acceptance.json').read_bytes());assert media['passed']is True and media['sourceReportSha256']==hashlib.sha256((R/'artifacts/media-cleanup.json').read_bytes()).hexdigest()
b=d.CpanelBackend(allow_writes=True);plan=d.make_plan(new,b);assert b.public_health()['releaseHash']==base['manifest']['releaseHash']
private=plan['privateRoot'];old_private=d.HOME+'/nodeno-releases/'+base['manifest']['releaseHash']+'/private'
def pointer(body):
 ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(b.post('/execute/Fileman/upload_files',payload,ct))
with d.deployment_lease(b):
 assert b.public_health()['releaseHash']==base['manifest']['releaseHash'];old_pointer=d.text_content(b,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1;new_pointer=old_pointer.replace(old_private.encode(),private.encode())
 backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-stripe-api-'+secrets.token_hex(4);d.ensure_directory(b,backup,private=True,permissions='0700');b.upload(backup,{'nodeno-runtime.php':old_pointer});assert d.text_content(b,backup,'nodeno-runtime.php')==old_pointer
 d.ensure_directory(b,private,private=True,permissions='0700');d.ensure_directory(b,private+'/cache',private=True,permissions='0700');b.upload(private,{name[8:]:body for name,body in new['all_bytes'].items()if name.startswith('private/')});assert d.text_content(b,private,'payment-stripe.php')==replacement;assert d.text_content(b,private,'release.json')==new['all_bytes']['private/release.json']
 try:
  pointer(new_pointer);assert d.text_content(b,d.HOME,'nodeno-runtime.php')==new_pointer;health=b.public_health();assert health['releaseHash']==manifest['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']is False
 except Exception:pointer(old_pointer);assert b.public_health()['releaseHash']==base['manifest']['releaseHash'];raise
 result={'passed':True,'releaseHash':manifest['releaseHash'],'baseReleaseHash':base['manifest']['releaseHash'],'backupRoot':backup,'changedPrivate':['payment-stripe.php'],'publicAssetsUnchanged':True,'accountStorageAndCredentialsPreserved':True,'checkoutEnabled':False,'realProviderPreflight':True};(E/'api-fix-deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
