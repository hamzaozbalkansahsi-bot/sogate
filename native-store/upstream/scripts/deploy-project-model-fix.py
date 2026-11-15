"""Publish a model-grouping correction with identical, already audited media.

Only two private JSON files may differ. Product facts, prices, references and all
public bytes must equal the release that passed the complete pixel/media audit.
"""
from pathlib import Path
import importlib.util,sys,json,hashlib,requests,secrets
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1];E=R/'artifacts/project-commerce';s=importlib.util.spec_from_file_location('guarded_model_fix',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d)
base=d.load_release(R/'artifacts/cpanel-release-projects-20261110');new=d.load_release(R/'artifacts/cpanel-release-projects-final-20261110');proof=json.loads((E/'model-fix-build.json').read_bytes())
assert base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash']
log=[json.loads(line)for line in(E/'deployment.log').read_text().splitlines()if line.startswith('{')]
assert any(r.get('stage')=='all_media_verified'and r.get('releaseHash')==proof['baseReleaseHash']for r in log)
assert any(r.get('stage')=='uploaded_verified_health'and r.get('releaseHash')==proof['baseReleaseHash']for r in log)
assert {n for n in base['all_bytes']if base['all_bytes'][n]!=new['all_bytes'].get(n)}=={'private/catalog.json','private/cabinet-fronts.json','private/release.json'}
assert set(base['all_bytes'])==set(new['all_bytes'])
for name in base['all_bytes']:
 if name.startswith('public/'):assert base['all_bytes'][name]==new['all_bytes'][name]
old_front=json.loads(base['all_bytes']['private/cabinet-fronts.json']);new_front=json.loads(new['all_bytes']['private/cabinet-fronts.json'])
for a,b in zip(old_front['products'],new_front['products']):
 assert {k:v for k,v in a.items()if k!='modelId'}=={k:v for k,v in b.items()if k!='modelId'}
 assert b['modelId']==(a['modelId'].replace('model-front-','model-front-accessory-',1)if a['productType']=='cabinet-profile'else a['modelId'])
assert {k:v for k,v in old_front.items()if k!='products'}=={k:v for k,v in new_front.items()if k!='products'}
old_catalog=json.loads(base['all_bytes']['private/catalog.json']);new_catalog=json.loads(new['all_bytes']['private/catalog.json'])
for a,b in zip(old_catalog['products'],new_catalog['products']):assert {k:v for k,v in a.items()if k!='modelId'}=={k:v for k,v in b.items()if k!='modelId'}
assert len(old_catalog['products'])==len(new_catalog['products'])and len(old_front['products'])==len(new_front['products'])
assert {k:v for k,v in old_catalog.items()if k not in ['products','meta']}=={k:v for k,v in new_catalog.items()if k not in ['products','meta']}
assert {k:v for k,v in old_catalog['meta'].items()if k not in ['frontCatalogVersion','modelCount','releaseHash']}=={k:v for k,v in new_catalog['meta'].items()if k not in ['frontCatalogVersion','modelCount','releaseHash']}
# Validate every current source/output byte against the exact approved reference
# set. The full pixel/object audit is the successful parent deployment above.
cleanup=json.loads((R/'artifacts/media-cleanup.json').read_bytes());approved=json.loads(base['all_bytes']['private/media-approved.json']);assert cleanup['publicationReady']is True and cleanup['references']==approved['references']
for key,row in approved['images'].items():
 current=cleanup['images'][key]
 for field in ['state','sourceSha','outputSha','mime','bytes','width','height']:assert current[field]==row[field]
 for field,hashfield,folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
  relative=current[field];assert relative.startswith('artifacts/'+folder+'/')and '..'not in Path(relative).parts
  path=R/relative;assert not path.is_symlink()and hashlib.sha256(path.read_bytes()).hexdigest()==row[hashfield]
owner_spec=importlib.util.spec_from_file_location('model_fix_owner_gate',R/'lib/owner_media_gate.py');owner=importlib.util.module_from_spec(owner_spec);owner_spec.loader.exec_module(owner);owner.verify_owner_catalogues(R,new)
local=json.loads((E/'local-supplement.json').read_bytes());assert local['passed']is True and local['releaseHash']==proof['releaseHash']
class UnchangedPublicBackend(d.CpanelBackend):
 def public_read(self,relative):
  assert relative in self.public_paths
  return base['all_bytes']['public/'+relative]
 def upload(self,directory,files):
  if directory==d.PUBLIC or directory.startswith(d.PUBLIC+'/'):
   prefix='public/'+(''if directory==d.PUBLIC else directory[len(d.PUBLIC)+1:]+'/')
   for name,body in files.items():assert base['all_bytes'][prefix+name]==body
   return
  super().upload(directory,files)
backend=UnchangedPublicBackend(allow_writes=True);health=backend.public_health();assert health['releaseHash']==proof['baseReleaseHash']and health['mediaReady']is True
receipt={'parentFullMediaAudit':proof['baseReleaseHash'],'releaseHash':proof['releaseHash'],'mediaVersion':health['mediaVersion'],'references':len(cleanup['references']),'allCurrentSourceAndOutputHashesVerified':True,'allOwnerImagesDecodedAndVerified':True,'allPublicBytesUnchanged':True,'onlyModelGroupingChanged':True}
(E/'model-fix-media-identity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
# This correction changes no public asset. Stage an immutable private release
# and replace only its protected runtime pointer. Public-file backup limits and
# the general publisher are left intact; there is no public upload to roll back.
private=d.HOME+'/nodeno-releases/'+proof['releaseHash']+'/private';old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private'
def pointer_upload(body):
 content_type,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(backend.post('/execute/Fileman/upload_files',payload,content_type))
with d.deployment_lease(backend):
 assert backend.public_health()['releaseHash']==proof['baseReleaseHash']
 old_pointer=d.text_content(backend,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1
 new_pointer=old_pointer.replace(old_private.encode(),private.encode())
 backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-model-'+secrets.token_hex(4)
 d.ensure_directory(backend,backup,private=True,permissions='0700');backend.upload(backup,{'nodeno-runtime.php':old_pointer})
 assert d.text_content(backend,backup,'nodeno-runtime.php')==old_pointer
 d.ensure_directory(backend,private,private=True,permissions='0700')
 d.ensure_directory(backend,private+'/cache',private=True,permissions='0700')
 backend.upload(private,{name[len('private/'):]:body for name,body in new['all_bytes'].items()if name.startswith('private/')})
 # cPanel's text reader refuses files above 1 MB. Read the signed manifest
 # here; public_health below hashes every deployed private/public file against
 # it, including both multi-megabyte JSON catalogues and binary geo data.
 assert d.text_content(backend,private,'release.json')==new['all_bytes']['private/release.json']
 print(json.dumps({'stage':'private_model_data_staged','releaseHash':proof['releaseHash'],'backupRoot':backup}),flush=True)
 try:
  assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==old_pointer
  pointer_upload(new_pointer);assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==new_pointer
  live=backend.public_health();assert live['releaseHash']==proof['releaseHash']and live['mediaReady']is True and live['checkoutEnabled']is False
 except Exception:
  pointer_upload(old_pointer);assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==old_pointer
  print(json.dumps({'stage':'private_pointer_restored','backupRoot':backup}),flush=True);raise
 result={'stage':'model_data_verified_live','releaseHash':proof['releaseHash'],'backupRoot':backup,'publicBytesUnchanged':True,'accountDataUntouched':True}
 (E/'model-fix-live.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
