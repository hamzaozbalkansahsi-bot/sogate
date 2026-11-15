"""Publish the reviewed, disabled-by-default payment release with backups and rollback."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,secrets,sys,subprocess
R=Path(__file__).resolve().parents[1];E=R/'artifacts/stripe-checkout-20261110'
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
spec=importlib.util.spec_from_file_location('stripe_guarded_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
base=d.load_release(R/'artifacts/cpanel-release-measurements-20261110');new=d.load_release(R/'artifacts/cpanel-release-stripe-20261110');proof=json.loads((E/'build.json').read_bytes());browser=json.loads((E/'browser.json').read_bytes())
assert proof['baseReleaseHash']==base['manifest']['releaseHash']and proof['releaseHash']==new['manifest']['releaseHash']
assert browser['passed']is True and browser['scenarios']==12 and browser['live']is False and browser['providerTest']is False and browser['releaseHash']==proof['releaseHash']
assert '\u2139 fail 0' in (E/'payment-tests.log').read_text(encoding='utf8')
audit=json.loads((R/'artifacts/measurement-orders/full-media-audit.json').read_bytes());cleanup_path=R/'artifacts/media-cleanup.json';cleanup=json.loads(cleanup_path.read_bytes());approved=json.loads(new['all_bytes']['private/media-approved.json'])
assert audit['passed']is True and audit['sourceReportSha256']==hashlib.sha256(cleanup_path.read_bytes()).hexdigest()and audit['mediaVersion']==new['manifest']['mediaVersion']
assert cleanup['publicationReady']is True and cleanup['references']==approved['references']and set(cleanup['images'])==set(approved['images'])
for name,h in audit['files'].items():assert hashlib.sha256(new['all_bytes'][name]).hexdigest()==h,name
for key,row in approved['images'].items():
 current=cleanup['images'][key]
 for field in ['state','sourceSha','outputSha','mime','bytes','width','height']:assert current[field]==row[field],(key,field)
 for field,hashfield,folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
  candidate=R/current[field];allowed=R/'artifacts'/folder;assert not candidate.is_symlink()and not allowed.is_symlink();file=candidate.resolve();assert file.is_relative_to(allowed.resolve());assert hashlib.sha256(file.read_bytes()).hexdigest()==row[hashfield],key
owner_spec=importlib.util.spec_from_file_location('stripe_owner_media_gate',R/'lib/owner_media_gate.py');owner=importlib.util.module_from_spec(owner_spec);owner_spec.loader.exec_module(owner);owner.verify_owner_catalogues(R,new)
for name in base['all_bytes']:
 if '/assets/'in name or name in ['private/catalog.json','private/config.json','private/media.json','private/media-approved.json','private/door-catalog.json','private/cabinet-fronts.json']:
  assert base['all_bytes'][name]==new['all_bytes'][name],name
subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(new['directory'])],check=True)
(E/'media-identity-acceptance.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'sourceReportSha256':audit['sourceReportSha256'],'priorFullAuditReleaseHash':audit['auditReleaseHash'],'currentSourcesAndOutputsRehashed':True,'catalogueAndMediaBytesPreserved':True},indent=2)+'\n')
changed={name[7:]:body for name,body in new['all_bytes'].items()if name.startswith('public/')and base['all_bytes'].get(name)!=body}
assert set(changed)=={'index.php','app.js','styles.css','payments.js','admin-payments.js','admin.js','admin.html','door-ui.js'}
backend=d.CpanelBackend(allow_writes=args.apply);plan=d.make_plan(new,backend);assert backend.public_health()['releaseHash']==proof['baseReleaseHash']
if not args.apply:
 print(json.dumps({'planVerified':True,'releaseHash':proof['releaseHash'],'publicDelta':sorted(changed),'checkoutEnabled':False}));sys.exit(0)
backend.public_paths=frozenset(set(changed)-{'index.php'});originals={};created=[];existing=d.listing(backend,d.PUBLIC)
for name in changed:
 if 'public/'+name in base['all_bytes']:
  body=d.text_content(backend,d.PUBLIC,name)if name=='index.php'else backend.public_read(name);assert body==base['all_bytes']['public/'+name],name;originals[name]=body
 else:assert name not in existing;created.append(name)
assert sum(map(len,originals.values()))<=d.PUBLIC_BACKUP_MAX_BYTES
old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';private=plan['privateRoot']
def pointer(body):
 ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(backend.post('/execute/Fileman/upload_files',payload,ct))
with d.deployment_lease(backend):
 assert backend.public_health()['releaseHash']==proof['baseReleaseHash']
 old_pointer=d.text_content(backend,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1;new_pointer=old_pointer.replace(old_private.encode(),private.encode())
 backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-stripe-'+secrets.token_hex(4)
 d.ensure_directory(backend,backup,private=True,permissions='0700');d.ensure_directory(backend,backup+'/public',private=True,permissions='0700')
 backend.upload(backup,{'nodeno-runtime.php':old_pointer,'delta.json':json.dumps({'baseReleaseHash':proof['baseReleaseHash'],'targetReleaseHash':proof['releaseHash'],'createdPublic':created},indent=2).encode()});backend.upload(backup+'/public',originals)
 assert d.text_content(backend,backup,'nodeno-runtime.php')==old_pointer
 for name,body in originals.items():assert d.text_content(backend,backup+'/public',name)==body
 d.ensure_directory(backend,private,private=True,permissions='0700');d.ensure_directory(backend,private+'/cache',private=True,permissions='0700')
 backend.upload(private,{name[8:]:body for name,body in new['all_bytes'].items()if name.startswith('private/')})
 assert d.text_content(backend,private,'release.json')==new['all_bytes']['private/release.json']
 try:
  for name in sorted(set(changed)-{'index.php'},key=lambda n:(n in ['app.js','admin.js','admin.html'],n)):backend.upload(d.PUBLIC,{name:changed[name]})
  for name,body in changed.items():
   if name!='index.php':assert backend.public_read(name)==body
  pointer(new_pointer);backend.upload(d.PUBLIC,{'index.php':changed['index.php']})
  assert d.text_content(backend,d.PUBLIC,'index.php')==changed['index.php'];assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==new_pointer
  health=backend.public_health();assert health['releaseHash']==proof['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']is False
 except Exception:
  backend.upload(d.PUBLIC,{'index.php':originals['index.php']});pointer(old_pointer);backend.upload(d.PUBLIC,{n:b for n,b in originals.items()if n!='index.php'})
  for name in created:
   if name in d.listing(backend,d.PUBLIC):assert backend.public_read(name)==changed[name];backend.api2('fileop',op='trash',sourcefiles=d.PUBLIC+'/'+name,doubledecode='0')
  assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];raise
 result={'passed':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'backupRoot':backup,'publicFilesChanged':sorted(changed),'catalogueAndMediaUnchanged':True,'accountStoragePreserved':True,'checkoutEnabled':False,'providerTest':False}
 (E/'deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
