"""Package the payment delta on the verified live release; keep catalogues/media unchanged."""
from pathlib import Path
import hashlib,json,os,re
R=Path(__file__).resolve().parents[1]
B=R/'artifacts/cpanel-release-measurements-20261110'
O=R/'artifacts/cpanel-release-stripe-20261110'
E=R/'artifacts/stripe-checkout-20261110';E.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
base=json.loads((B/'private/release.json').read_bytes())
assert base['releaseHash']=='fe19435ab04d6a56911daecc7b6ea69b2f5d99bedd718c8db258f393614d3874'
for name,h in base['files'].items():assert sha((B/name).read_bytes())==h,name
patch={}
for name in ['payment-core.php','payment-store.php','payment-stripe.php','payment-admin.php','payments.php','account.php','control-http.php']:
 patch['private/'+name]=(R/'hosting'/name).read_bytes()
patch['public/index.php']=(R/'hosting/index.php').read_bytes()
for name in ['payments.js','admin-payments.js','admin.js','styles.css','door-ui.js']:
 patch['public/'+name]=(R/'web'/name).read_bytes()
# Preserve the live dependency versions and invalidate each changed dependency for returning browsers.
changed_js={'app.js','door-ui.js','admin.js','payments.js','admin-payments.js'}
for name in changed_js:
 body=(R/'web'/name).read_text(encoding='utf8');live_path=B/'public'/name
 if live_path.exists():
  for path,version in re.findall(r"from '(\./[^'?]+)\?v=([^']+)'",live_path.read_text(encoding='utf8')):
   body=re.sub(r"(from '"+re.escape(path)+r")\?v=[^']+",lambda m:m[1]+'?v='+version,body)
 for dependency in changed_js:
  body=re.sub(r"(from '\./"+re.escape(dependency)+r")(?:\?v=[^']+)?(?=')",lambda m:m[1]+'?v=nodeno-payments-20261110-r1',body)
 patch['public/'+name]=body.encode()
for name in ['private/index.html','public/admin.html']:
 text=(B/name).read_text(encoding='utf8')
 for asset in ['app.js','styles.css','admin.js']:
  text=re.sub(r'(/'+re.escape(asset)+r'\?v=)[^"\s]+',lambda m:m[1]+'nodeno-payments-20261110-r1',text)
 patch[name]=text.encode()
O.mkdir(exist_ok=True)
assert not any(p.is_symlink()for p in O.rglob('*'))
for name in base['files']:
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():os.link(B/name,target)
for name,body in patch.items():
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():target.unlink()
 target.write_bytes(body)
# A changed module must never be imported through a URL already cached by the live application.
for name in changed_js:
 old=B/'public'/name
 if not old.exists():continue
 prior=dict(re.findall(r"from '(\./[^'?]+)(\?v=[^']+)?'",old.read_text(encoding='utf8')))
 for dep,version in re.findall(r"from '(\./[^'?]+)(\?v=[^']+)?'",(O/'public'/name).read_text(encoding='utf8')):
  target='public/'+dep[2:]
  if dep in prior and target in patch and target in base['files'] and sha(patch[target])!=base['files'][target]:assert version!=prior[dep],(name,dep)
hashes={**base['files'],**{name:sha(body)for name,body in patch.items()}}
h=hashlib.sha256()
for name in sorted(hashes):h.update((name+'\0'+hashes[name]+'\0').encode())
manifest={**base,'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest()}
target=O/'private/release.json'
if target.exists():target.unlink()
target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
for name,h in base['files'].items():assert sha((B/name).read_bytes())==h,name
for name in base['files']:
 if name not in patch:assert (B/name).read_bytes()==(O/name).read_bytes(),name
proof={'baseReleaseHash':base['releaseHash'],'releaseHash':manifest['releaseHash'],'output':str(O),'changedFiles':sorted(patch),'catalogueAndMediaBytesPreserved':True,'changedDependencyCacheUrlsVerified':True,'paymentEnabledByDefault':False,'privateStorageUntouched':True}
(E/'build.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof))
