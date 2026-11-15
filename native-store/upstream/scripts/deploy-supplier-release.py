"""Deploy only the reviewed supplier/admin delta; preserve account and media storage."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,secrets,sys
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1];E=R/'artifacts/supplier-expansion'
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,R/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
d=module('guarded_supplier_deploy','scripts/deploy-cpanel.py');sha=lambda b:hashlib.sha256(b).hexdigest()
def validate_unchanged_media(base,new):
 cleanup=json.loads((R/'artifacts/media-cleanup.json').read_bytes());approved=json.loads(base['all_bytes']['private/media-approved.json'])
 assert cleanup['publicationReady']is True and cleanup['references']==approved['references']
 for n in ['private/media-approved.json','private/media.json','private/door-catalog.json','private/cabinet-fronts.json']:assert base['all_bytes'][n]==new['all_bytes'][n]
 oldcat=json.loads(base['all_bytes']['private/catalog.json']);newcat=json.loads(new['all_bytes']['private/catalog.json']);assert [p['id']for p in oldcat['products']]==[p['id']for p in newcat['products']]
 for a,b in zip(oldcat['products'],newcat['products']):assert a['images']==b['images']
 for n in base['all_bytes']:
  if n.startswith(('public/assets/doors/','public/assets/fronts/')):assert base['all_bytes'][n]==new['all_bytes'][n]
 f=module('supplier_media_binding','scripts/finalize-media.py');assert cleanup['publicationAudit']['manifestBindingSha256']==f.publication_binding(cleanup)
 assert cleanup['publicationAudit']['policy']==f.PUBLICATION_POLICY['policy']
 parent=json.loads((R/'artifacts/project-commerce/model-fix-media-identity.json').read_bytes());assert parent['releaseHash']==base['manifest']['releaseHash']and parent['allCurrentSourceAndOutputHashesVerified']is True
 for key,row in approved['images'].items():
  current=cleanup['images'][key]
  for field in ['state','sourceSha','outputSha','mime','bytes','width','height']:assert current[field]==row[field]
  for field,hashfield,folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
   file=(R/current[field]).resolve();assert file.is_relative_to((R/'artifacts'/folder).resolve())and not file.is_symlink();assert sha(file.read_bytes())==row[hashfield]
 owner=module('supplier_owner_media','lib/owner_media_gate.py');owner.verify_owner_catalogues(R,new)
 return {'passed':True,'releaseHash':new['manifest']['releaseHash'],'parentAuditedRelease':base['manifest']['releaseHash'],'currentSourcesAndOutputsRehashed':True,'referenceCount':len(cleanup['references']),'noNewCustomerMedia':True,'publicationBindingVerified':True}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 proof=json.loads((E/'build.json').read_bytes());base=d.load_release(R/'artifacts/cpanel-release-projects-final-20261110');new=d.load_release(R/'artifacts/cpanel-release-suppliers-20261110')
 assert base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash']
 browser=json.loads((E/'browser/receipt.json').read_bytes());assert browser['passed']is True and browser['releaseHash']==proof['releaseHash']
 pricing=json.loads((E/'prices-validation-current.json').read_bytes());assert pricing['passed']is True and pricing['pricesSha256']==sha((R/'data/catalog-prices.json').read_bytes())
 print(json.dumps({'stage':'verify_existing_media_identity','releaseHash':proof['releaseHash']}),flush=True)
 media=validate_unchanged_media(base,new);(E/'media-identity-acceptance.json').write_text(json.dumps(media,indent=2)+'\n');print(json.dumps(media),flush=True)
 changed=[n for n in new['all_bytes']if n not in base['all_bytes']or new['all_bytes'][n]!=base['all_bytes'][n]];assert set(changed)-{'private/release.json'}==set(proof['changedFiles'])
 public=[n[7:]for n in changed if n.startswith('public/')];assert set(public)=={'admin.js','admin.css','admin.html','admin-suppliers.js'}
 backend=d.CpanelBackend(allow_writes=args.apply);assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];backend.public_paths=frozenset(public)
 originals={}
 for file in public:
  if 'public/'+file in base['all_bytes']:
   body=backend.public_read(file);assert body==base['all_bytes']['public/'+file];originals[file]=body
 if not args.apply:print(json.dumps({'stage':'plan_verified','changedPublic':public,'releaseHash':proof['releaseHash']}));return
 private=d.HOME+'/nodeno-releases/'+proof['releaseHash']+'/private';old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private'
 def pointer_upload(body):
  ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(backend.post('/execute/Fileman/upload_files',payload,ct))
 with d.deployment_lease(backend):
  assert backend.public_health()['releaseHash']==proof['baseReleaseHash']
  old_pointer=d.text_content(backend,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1
  new_pointer=old_pointer.replace(old_private.encode(),private.encode());backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-suppliers-'+secrets.token_hex(4)
  d.ensure_directory(backend,backup,private=True,permissions='0700');backend.upload(backup,{'nodeno-runtime.php':old_pointer,**originals})
  for file,body in {'nodeno-runtime.php':old_pointer,**originals}.items():assert d.text_content(backend,backup,file)==body
  d.ensure_directory(backend,private,private=True,permissions='0700');d.ensure_directory(backend,private+'/cache',private=True,permissions='0700')
  backend.upload(private,{n[8:]:b for n,b in new['all_bytes'].items()if n.startswith('private/')});assert d.text_content(backend,private,'release.json')==new['all_bytes']['private/release.json']
  print(json.dumps({'stage':'private_staged','releaseHash':proof['releaseHash']}),flush=True)
  try:
   # Dependency and styles precede their entrypoint. No storefront asset changes.
   for file in ['admin-suppliers.js','admin.css','admin.js','admin.html']:backend.upload(d.PUBLIC,{file:new['all_bytes']['public/'+file]})
   assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==old_pointer
   pointer_upload(new_pointer);assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==new_pointer
   live=backend.public_health();assert live['releaseHash']==proof['releaseHash']and live['mediaReady']is True and live['products']==1021 and live['checkoutEnabled']is False
   for file in public:assert backend.public_read(file)==new['all_bytes']['public/'+file]
  except Exception:
   for file,body in originals.items():backend.upload(d.PUBLIC,{file:body})
   pointer_upload(old_pointer);raise
 result={'passed':True,'releaseHash':proof['releaseHash'],'backupRoot':backup,'publicProducts':1021,'supplierRecords':proof['supplierRecords'],'privateDataPreserved':True,'publicImagesUnchanged':True}
 (E/'live-acceptance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
