"""Prepare a bounded payment fix on the current verified release, retaining its catalogue/media."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys,urllib.request
R=Path(__file__).resolve().parents[1];E=R/'artifacts/stripe-sandbox-20261110';E.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('nodeno_payment_fix_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
with urllib.request.urlopen('https://nodenohome.com/api/health',timeout=25)as response:health=json.load(response)
candidates=[]
for directory in(R/'artifacts').glob('cpanel-release*'):
 manifest=directory/'private/release.json'
 if manifest.is_file()and json.loads(manifest.read_bytes()).get('releaseHash')==health['releaseHash']:candidates.append(directory)
if len(candidates)!=1:raise RuntimeError('Unique verified live release artifact required')
B=candidates[0];base=d.load_release(B);O=R/'artifacts/cpanel-release-stripe-sandbox-20261110';O.mkdir(exist_ok=True)
changes={}
for filename in ['payment-store.php','payment-admin.php','payment-stripe.php','payments.php']:changes['private/'+filename]=(R/'hosting'/filename).read_bytes()
for filename in ['payments.js','admin-payments.js']:changes['public/'+filename]=(R/'web'/filename).read_bytes()
app=base['all_bytes']['public/app.js'].decode();old="function statusLabel(value){const labels=";new="function statusLabel(value){if(['paid','refunded','partially_refunded'].includes(value))return paymentText(locale,value==='partially_refunded'?'partiallyRefunded':value);const labels="
assert app.count(old)==1 and app.count('payments.js?v=nodeno-payments-20261110-r1')==1
changes['public/app.js']=app.replace(old,new).replace('payments.js?v=nodeno-payments-20261110-r1','payments.js?v=nodeno-payments-20261110-r2').encode()
admin=base['all_bytes']['public/admin.js'].decode();assert admin.count('admin-payments.js?v=nodeno-payments-20261110-r1')==1;changes['public/admin.js']=admin.replace('admin-payments.js?v=nodeno-payments-20261110-r1','admin-payments.js?v=nodeno-payments-20261110-r2').encode()
for filename,entry in [('private/index.html','app'),('public/admin.html','admin')]:
 text=base['all_bytes'][filename].decode();text,count=re.subn('/'+entry+r'\.js\?v=[^"\s]+','/'+entry+'.js?v=nodeno-refunds-20261110-r1',text);assert count==1;changes[filename]=text.encode()
for name in base['manifest']['files']:
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:
  if target.exists():target.unlink()
  target.write_bytes(changes[name])
 elif not target.exists():os.link(B/name,target)
hashes={name:hashlib.sha256((O/name).read_bytes()).hexdigest()for name in base['manifest']['files']};fingerprint=hashlib.sha256()
for name in sorted(hashes):fingerprint.update((name+'\0'+hashes[name]+'\0').encode())
manifest={**base['manifest'],'releaseHash':fingerprint.hexdigest(),'files':dict(sorted(hashes.items()))};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');release=d.load_release(O)
for name,body in base['all_bytes'].items():
 if name not in changes and name!='private/release.json':assert release['all_bytes'][name]==body,name
record={'prepared':True,'base':str(B.relative_to(R)),'release':str(O.relative_to(R)),'baseReleaseHash':base['manifest']['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'catalogueAndMediaUnchanged':True,'liveCheckoutWasEnabled':health['checkoutEnabled']};(E/'release-preparation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
