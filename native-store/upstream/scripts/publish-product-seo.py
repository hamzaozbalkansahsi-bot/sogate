"""Publish a tested SEO delta with the established media gates and exact-live-base protection."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util,sys,subprocess,re,secrets,argparse,time
R=Path(__file__).resolve().parents[1];E=R/'artifacts/seo-products'
a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args();s=importlib.util.spec_from_file_location('seo_publish',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d)
proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);release=d.load_release(R/proof['release']);assert release['manifest']['releaseHash']==proof['releaseHash']and base['manifest']['releaseHash']==proof['baseReleaseHash'];browser=json.loads((E/'browser.json').read_bytes());assert browser['passed']and browser['releaseHash']==proof['releaseHash']and len(browser['checks'])>=10
old=json.loads(base['all_bytes']['private/catalog.json']);new=json.loads(release['all_bytes']['private/catalog.json']);assert [p['id']for p in old['products']]==[p['id']for p in new['products']]
for left,right in zip(old['products'],new['products']):assert {k:v for k,v in left.items()if k not in ['name','modelName','description','supplierDetailsHash']}=={k:v for k,v in right.items()if k not in ['name','modelName','description','supplierDetailsHash']}
changed={k:v for k,v in release['all_bytes'].items()if base['all_bytes'].get(k)!=v};private_allowed={'private/catalog.json','private/seo.php','private/supplier-details.bin','private/supplier-details.json','private/index.html','private/release.json'};public_allowed={'public/app.js','public/seo-core.js','public/seo-ui.js','public/catalog-pagination.js','public/styles.css','public/index.php'}
assert all(k in private_allowed|public_allowed or re.fullmatch(r'public/[a-f0-9]{32}\.txt',k)for k in changed)
# Replay current approval identity and source/output hashes; no image bytes are changed by this release.
audit=json.loads((R/'artifacts/measurement-orders/full-media-audit.json').read_bytes());cleanupfile=R/'artifacts/media-cleanup.json';cleanup=json.loads(cleanupfile.read_bytes());assert audit['passed']and audit['sourceReportSha256']==d.sha256(cleanupfile.read_bytes())and cleanup['publicationReady']is True
assert base['all_bytes']['private/media-approved.json']==release['all_bytes']['private/media-approved.json']and audit['mediaVersion']==release['manifest']['mediaVersion']
for name in audit['files']:assert base['all_bytes'][name]==release['all_bytes'][name]
for row in cleanup['images'].values():
 for path,field,folder in [(row['sourcePath'],'sourceSha','media-originals'),(row['path'],'outputSha','media-cleaned')]:
  file=R/path;assert not file.is_symlink()and file.resolve().is_relative_to((R/'artifacts'/folder).resolve())and d.sha256(file.read_bytes())==row[field]
d.validate_supplier_publication(R,release,new)
spec=importlib.util.spec_from_file_location('seo_owner',R/'lib/owner_media_gate.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner);owner.verify_owner_catalogues(R,release);subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(release['directory'])],check=True)
backend=d.CpanelBackend(allow_writes=args.apply);health=backend.public_health();assert health['releaseHash']==proof['baseReleaseHash'];plan=d.make_plan(release,backend);public={k[7:]:v for k,v in changed.items()if k.startswith('public/')}
print(json.dumps({'ready':True,'products':len(new['products']),'mediaUnchanged':True,'publicDelta':len(public)}),flush=True)
if not args.apply:sys.exit(0)
private=plan['privateRoot'];oldprivate=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private'
def pointer(body):
 ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(backend.post('/execute/Fileman/upload_files',payload,ct))
with d.deployment_lease(backend):
 assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];originals={name:d.text_content(backend,d.PUBLIC,name)for name in public if 'public/'+name in base['all_bytes']}
 for name,body in originals.items():assert body==base['all_bytes']['public/'+name]
 oldpointer=d.text_content(backend,d.HOME,'nodeno-runtime.php');assert oldpointer.count(oldprivate.encode())==1;newpointer=oldpointer.replace(oldprivate.encode(),private.encode());backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-seo-'+secrets.token_hex(4);d.ensure_directory(backend,backup,private=True,permissions='0700');d.ensure_directory(backend,backup+'/public',private=True,permissions='0700');backend.upload(backup,{'nodeno-runtime.php':oldpointer});backend.upload(backup+'/public',originals)
 d.ensure_directory(backend,private,private=True,permissions='0700');d.ensure_directory(backend,private+'/cache',private=True,permissions='0700');backend.upload(private,{k[8:]:v for k,v in release['all_bytes'].items()if k.startswith('private/')});assert d.text_content(backend,private,'release.json')==release['all_bytes']['private/release.json']
 assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==oldpointer
 try:
  for name in sorted(public,key=lambda n:(n in ['app.js','index.php'],n)):
   backend.upload(d.PUBLIC,{name:public[name]});assert d.text_content(backend,d.PUBLIC,name)==public[name]
  pointer(newpointer)
  for attempt in range(4):
   current=backend.public_health()
   if current.get('releaseHash')==proof['releaseHash']:break
   time.sleep(1)
  assert current['releaseHash']==proof['releaseHash']and current['products']==3602 and current['mediaReady']and current['checkoutEnabled']==health['checkoutEnabled']
 except Exception:
  pointer(oldpointer);backend.upload(d.PUBLIC,originals);assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];raise
 record={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'products':3602,'backupRoot':backup,'pricesCodesUnitsAndImagesPreserved':True,'customerAndPaymentStoragePreserved':True};(E/'deployment.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
