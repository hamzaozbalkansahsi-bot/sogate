"""Publish a bounded UI/PHP delta, preserving immutable media and account data.

The standard full media audit and final byte/hash checks remain mandatory.
Only changed root-level JS/CSS files are uploaded and backed up in memory;
unchanged catalogue images are never overwritten. The previous publisher's
100 MB backup bound is retained for this much smaller delta.
"""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,sys,hashlib,secrets,subprocess,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/measurement-orders'
s=importlib.util.spec_from_file_location('guarded_measurement_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d)
base=d.load_release(R/'artifacts/cpanel-release-checkout-alignment-20261110');new=d.load_release(R/'artifacts/cpanel-release-measurements-20261110');proof=json.loads((E/'build.json').read_bytes());audit=json.loads((E/'full-media-audit.json').read_bytes());local=json.loads((E/'local-acceptance.json').read_bytes())
assert proof['baseReleaseHash']==base['manifest']['releaseHash']and proof['releaseHash']==new['manifest']['releaseHash']
assert local['passed']is True and local['scenarios']==12 and local['releaseHash']==proof['releaseHash']and not local['live']
assert audit['passed']is True and audit['sourceReportSha256']==hashlib.sha256((R/'artifacts/media-cleanup.json').read_bytes()).hexdigest()
assert audit['mediaVersion']==new['manifest']['mediaVersion']
for name,h in audit['files'].items():assert hashlib.sha256(new['all_bytes'][name]).hexdigest()==h
for name in base['all_bytes']:
 if '/assets/'in name or name in ['private/config.json','private/media.json','private/media-approved.json','private/door-catalog.json','private/cabinet-fronts.json']:
  assert base['all_bytes'][name]==new['all_bytes'][name]
subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(new['directory'])],check=True)
changed={name[7:]:body for name,body in new['all_bytes'].items()if name.startswith('public/')and base['all_bytes'].get(name)!=body}
assert changed and all(re.fullmatch(r'[a-z0-9-]+\.(?:js|css)',name)for name in changed)
assert {name for name in proof['changedFiles']if name.startswith('public/')}=={'public/'+name for name in changed}
b=d.CpanelBackend(allow_writes=True);plan=d.make_plan(new,b);assert b.public_health()['releaseHash']==proof['baseReleaseHash']
b.public_paths=frozenset(changed);existing=d.listing(b,d.PUBLIC);originals={};created=[]
for name in sorted(changed):
 if 'public/'+name in base['all_bytes']:
  originals[name]=b.public_read(name);assert originals[name]==base['all_bytes']['public/'+name]
 else:assert name not in existing;created.append(name)
assert sum(map(len,originals.values()))<=d.PUBLIC_BACKUP_MAX_BYTES
old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';private=plan['privateRoot']
def pointer(body):
 content_type,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(b.post('/execute/Fileman/upload_files',payload,content_type))
with d.deployment_lease(b):
 assert b.public_health()['releaseHash']==proof['baseReleaseHash']
 old_pointer=d.text_content(b,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1;new_pointer=old_pointer.replace(old_private.encode(),private.encode())
 for name,body in originals.items():assert b.public_read(name)==body
 backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-measurements-'+secrets.token_hex(4)
 d.ensure_directory(b,backup,private=True,permissions='0700');d.ensure_directory(b,backup+'/public',private=True,permissions='0700')
 b.upload(backup,{'nodeno-runtime.php':old_pointer,'delta.json':json.dumps({'baseReleaseHash':proof['baseReleaseHash'],'targetReleaseHash':proof['releaseHash'],'createdPublic':created,'overwrittenPublic':{name:hashlib.sha256(body).hexdigest()for name,body in originals.items()}},indent=2).encode()})
 b.upload(backup+'/public',originals)
 assert d.text_content(b,backup,'nodeno-runtime.php')==old_pointer
 for name,body in originals.items():assert d.text_content(b,backup+'/public',name)==body
 d.ensure_directory(b,private,private=True,permissions='0700');d.ensure_directory(b,private+'/cache',private=True,permissions='0700')
 b.upload(private,{name[8:]:body for name,body in new['all_bytes'].items()if name.startswith('private/')})
 assert d.text_content(b,private,'release.json')==new['all_bytes']['private/release.json']
 d.emit('measurement_private_staged',releaseHash=proof['releaseHash'],backupRoot=backup)
 try:
  # Dependencies precede the application entrypoint. The new HTML cache keys
  # become active only after the protected private pointer changes.
  for name in sorted(changed,key=lambda name:(name=='app.js',name)):b.upload(d.PUBLIC,{name:changed[name]})
  for name,body in changed.items():assert b.public_read(name)==body
  assert d.text_content(b,d.HOME,'nodeno-runtime.php')==old_pointer
  pointer(new_pointer);assert d.text_content(b,d.HOME,'nodeno-runtime.php')==new_pointer
  health=b.public_health();assert health['releaseHash']==proof['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']is False
 except Exception:
  pointer(old_pointer)
  b.upload(d.PUBLIC,originals)
  for name in created:
   if name in d.listing(b,d.PUBLIC):
    assert b.public_read(name)==changed[name];b.api2('fileop',op='trash',sourcefiles=d.PUBLIC+'/'+name,doubledecode='0')
  assert d.text_content(b,d.HOME,'nodeno-runtime.php')==old_pointer
  assert b.public_health()['releaseHash']==proof['baseReleaseHash']
  d.emit('measurement_delta_rolled_back',backupRoot=backup);raise
 result={'passed':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'backupRoot':backup,'publicFilesChanged':len(changed),'unchangedMediaNotOverwritten':True,'allDeployedFileHashesVerifiedByHealth':True,'privateAccountsAndFxJobUntouched':True,'checkoutEnabled':False,'mediaAuditReleaseHash':audit['auditReleaseHash'],'identicalMediaInputsReverified':True}
 (E/'deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
