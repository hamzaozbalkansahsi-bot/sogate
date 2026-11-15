"""Prepare the user's country-aware date policy over the exact current live release."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/date-time-20261112'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def changes_for(base):
 policy=load('nodeno_date_policy','lib/date_time_policy.py');changes={'public/date-time.js':(R/'web/date-time.js').read_bytes(),'private/date-time.php':(R/'hosting/date-time.php').read_bytes(),'private/date-time-regions.json':(R/'data/date-time-regions.json').read_bytes()}
 for name in['app.js','admin.js','admin-social.js','admin-suppliers.js','admin-analytics.js']:
  key='public/'+name
  if key in base['all_bytes']:
   value=policy.rewrite(name,base['all_bytes'][key])
   if value!=base['all_bytes'][key]:changes[key]=value
 for key,script in[('private/index.html','app.js'),('public/admin.html','admin.js')]:
  value=policy.html_revision(base['all_bytes'][key],script)
  if value!=base['all_bytes'][key]:changes[key]=value
 # Existing signed order-document snapshots are immutable. Only future document generation changes.
 key='private/payment-documents.php'
 if key in base['all_bytes']:
  value=base['all_bytes'][key];old=b"gmdate('Y-m-d H:i:s',(int)$order['created_at']).' UTC";new=b"$e(nodenoHumanDateTime((int)$order['created_at'],(string)($quote['country']??$contact['delivery']['country']??'TR'))).'"
  if old in value:
   value=value.replace(old,new).replace(b"declare(strict_types=1);",b"declare(strict_types=1);\nrequire_once __DIR__.'/date-time.php';",1);changes[key]=value
 return {k:v for k,v in changes.items()if base['all_bytes'].get(k)!=v}
def main():
 d=load('date_prepare_deploy','scripts/deploy-cpanel.py');health=d.CpanelBackend().public_health();live=health['releaseHash'];B=None
 for file in(R/'artifacts').glob('cpanel-release*/private/release.json'):
  try:
   if json.loads(file.read_bytes()).get('releaseHash')==live:B=file.parent.parent;break
  except (OSError,json.JSONDecodeError):pass
 if B is None:raise RuntimeError('current_live_base_not_available')
 base=d.load_release(B);changes=changes_for(base);digest=hashlib.sha256(b''.join(k.encode()+hashlib.sha256(v).digest()for k,v in sorted(changes.items()))).hexdigest()[:12];O=R/('artifacts/cpanel-release-date-time-20261112-'+digest)
 if O.exists():raise RuntimeError('date_candidate_already_exists')
 for name in sorted(set(base['manifest']['files'])|set(changes)):
  target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
  if name in changes:target.write_bytes(changes[name])
  else:os.link(B/name,target)
 files={n:hashlib.sha256((O/n).read_bytes()).hexdigest()for n in sorted(set(base['manifest']['files'])|set(changes))};fp=hashlib.sha256()
 for name,value in files.items():fp.update((name+'\0'+value+'\0').encode())
 manifest={**base['manifest'],'files':files,'releaseHash':fp.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
 proof={'prepared':True,'feature':'date-time','base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':live,'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'publicProducts':health['products'],'expectedCheckoutEnabled':health['checkoutEnabled'],'sharedSourceEditorFilesModified':False,'customerDataModified':False};E.mkdir(exist_ok=True);(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
