"""Publish only a reviewed ready batch, preserving the exact live base and persistent data."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,concurrent.futures,hashlib,importlib.util,io,json,secrets,sys,zipfile,subprocess,time
R=Path(__file__).resolve().parents[1];E=R/'artifacts/supplier-expansion/publication'
parser=argparse.ArgumentParser();parser.add_argument('--release',default='artifacts/cpanel-release-suppliers-ready-20261110-r2');parser.add_argument('--base',default='artifacts/cpanel-release-stripe-api-20261110');parser.add_argument('--resume',action='store_true');parser.add_argument('--apply',action='store_true');args=parser.parse_args()
spec=importlib.util.spec_from_file_location('supplier_ready_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
base=d.load_release(R/args.base);new=d.load_release(R/args.release);proof=json.loads((E/(Path(args.release).name+'-proof.json')).read_bytes());browser=json.loads((E/'browser/acceptance.json').read_bytes())
assert proof['publicationReady']is True and proof['baseReleaseHash']==base['manifest']['releaseHash']and proof['releaseHash']==new['manifest']['releaseHash'];assert browser['passed']is True and len(browser['scenarios'])==8
if browser['releaseHash']!=proof['releaseHash']:
 assert proof.get('browserEquivalentReleaseHash')==browser['releaseHash']==base['manifest']['releaseHash']and proof.get('adminVisibilityVerified')is True
 unchanged=lambda r:{k:v for k,v in r['all_bytes'].items()if k not in ['private/supplier-catalog.json','private/release.json']}
 assert unchanged(base)==unchanged(new),'The browser-tested storefront must remain byte-identical'
for name in ['config.json','media.json','media-approved.json','door-catalog.json','cabinet-fronts.json','payment-core.php','payment-stripe.php']:
 assert base['all_bytes']['private/'+name]==new['all_bytes']['private/'+name],name
oldcat=json.loads(base['all_bytes']['private/catalog.json']);cat=json.loads(new['all_bytes']['private/catalog.json']);assert cat['categories'][:len(oldcat['categories'])]==oldcat['categories']
for previous,current in zip(oldcat['products'],cat['products']):
 if previous.get('productType')!='supplier-item':assert previous==current
 else:
  allowed={'name','modelName','description','specs','variantLabel','modelId','variationSelectionRequired','scopeNote','supplierDetailsHash','productBrand'}
  assert {k:v for k,v in previous.items()if k not in allowed}=={k:v for k,v in current.items()if k not in allowed},previous['id']
  assert current['supplierDetailsHash']and all(current['name'].get(l)for l in ['tr','en','ru','ar'])
added=cat['products'][len(oldcat['products']):];assert {p['id']for p in added}==set(proof['productIds'])
for p in added:
 assert p['productType']=='supplier-item'and all(p['name'].get(l)and p['description'].get(l)for l in ['tr','en','ru','ar'])
 for url in p['images']:
  name=url.lstrip('/');row=proof['assets'][name];assert d.sha256(new['all_bytes']['public/'+name])==row['outputSha256'];assert d.sha256((R/row['path']).read_bytes())==row['outputSha256']
gate_spec=importlib.util.spec_from_file_location('supplier_publication_gate',R/'lib/supplier_release.py');gate=importlib.util.module_from_spec(gate_spec);gate_spec.loader.exec_module(gate);approved={}
for group in ['altinis','alka-source-clean']:
 approved.update(gate.verify_review(json.loads((E/'media-review'/f'{group}.json').read_bytes()),R))
if (E/'media-review/alka-candidates-approved.json').exists():approved.update(gate.verify_review(json.loads((E/'media-review/alka-candidates-approved.json').read_bytes()),R))
for row in proof['assets'].values():assert approved[row['sourceSha256']]['outputSha256']==row['outputSha256']
# The legacy media gate remains mandatory and unmodified.
audit=json.loads((R/'artifacts/measurement-orders/full-media-audit.json').read_bytes());cleanup_path=R/'artifacts/media-cleanup.json';cleanup=json.loads(cleanup_path.read_bytes());approved=json.loads(new['all_bytes']['private/media-approved.json'])
assert audit['passed']is True and audit['sourceReportSha256']==d.sha256(cleanup_path.read_bytes())and audit['mediaVersion']==new['manifest']['mediaVersion']
assert cleanup['publicationReady']is True and cleanup['references']==approved['references']and set(cleanup['images'])==set(approved['images'])
for key,row in approved['images'].items():
 current=cleanup['images'][key]
 for field in ['state','sourceSha','outputSha','mime','bytes','width','height']:assert current[field]==row[field]
 for field,hashfield,folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
  candidate=R/current[field];assert not candidate.is_symlink()and candidate.resolve().is_relative_to((R/'artifacts'/folder).resolve());assert d.sha256(candidate.read_bytes())==row[hashfield]
for name in audit['files']:assert base['all_bytes'][name]==new['all_bytes'][name]
owner_spec=importlib.util.spec_from_file_location('supplier_owner_media_gate',R/'lib/owner_media_gate.py');owner=importlib.util.module_from_spec(owner_spec);owner_spec.loader.exec_module(owner);owner.verify_owner_catalogues(R,new)
subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(new['directory'])],check=True)
print(json.dumps({'legacyMediaIdentityVerified':True,'references':len(approved['references'])}),flush=True)
changed={name[7:]:body for name,body in new['all_bytes'].items()if name.startswith('public/')and base['all_bytes'].get(name)!=body};media={n:b for n,b in changed.items()if n.startswith('assets/suppliers/')};ui={n:b for n,b in changed.items()if n not in media};assert set(ui)<={'index.php','app.js','shop-core.js','supplier-products.js'}
b=d.CpanelBackend(allow_writes=args.apply);baseline_health=b.public_health();assert baseline_health['releaseHash']==proof['baseReleaseHash'];plan=d.make_plan(new,b)
if not args.apply:print(json.dumps({'planVerified':True,'productsAdded':len(added),'images':len(media),'releaseHash':proof['releaseHash']}));sys.exit(0)
old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';private=plan['privateRoot'];b.public_paths=frozenset((set(ui)|set(media))-{'index.php'})
def pointer(body):
 ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(b.post('/execute/Fileman/upload_files',payload,ct))
def verify_file(item):
 name,body=item;assert b.public_read(name)==body,name
with d.deployment_lease(b):
 assert b.public_health()['releaseHash']==proof['baseReleaseHash'];old_pointer=d.text_content(b,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1;new_pointer=old_pointer.replace(old_private.encode(),private.encode())
 backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-suppliers-'+secrets.token_hex(4);d.ensure_directory(b,backup,private=True,permissions='0700');d.ensure_directory(b,backup+'/public',private=True,permissions='0700')
 originals={n:(d.text_content(b,d.PUBLIC,n)if n=='index.php'else b.public_read(n))for n in ui if 'public/'+n in base['all_bytes']}
 for n,body in originals.items():assert body==base['all_bytes']['public/'+n]
 b.upload(backup,{'nodeno-runtime.php':old_pointer});b.upload(backup+'/public',originals);assert d.text_content(b,backup,'nodeno-runtime.php')==old_pointer
 d.ensure_directory(b,private,private=True,permissions='0700');d.ensure_directory(b,private+'/cache',private=True,permissions='0700')
 
 if not args.resume:b.upload(private,{name[8:]:body for name,body in new['all_bytes'].items()if name.startswith('private/')})
 assert d.text_content(b,private,'release.json')==new['all_bytes']['private/release.json']
 # Archives contain only immutable, hash-named approved raster files. No PHP, JSON or source archives.
 batch=[];size=0;archives=[]
 for name,body in media.items():
  d.public_asset_path(name);assert name.split('/')[:2]==['assets','suppliers'];assert name.rsplit('/',1)[1].split('.')[0]==d.sha256(body)
  if batch and size+len(body)>18000000:archives.append(batch);batch=[];size=0
  batch.append((name,body));size+=len(body)
 if batch:archives.append(batch)
 for i,items in enumerate([]if args.resume else archives):
  stream=io.BytesIO()
  with zipfile.ZipFile(stream,'w',zipfile.ZIP_STORED)as z:
   for name,body in items:
    info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=(0o100644<<16);z.writestr(info,body)
  filename=f'approved-supplier-media-{i}.zip';b.upload(private,{filename:stream.getvalue()});b.api2('fileop',op='extract',sourcefiles=private+'/'+filename,destfiles=d.PUBLIC,doubledecode='0');print(json.dumps({'mediaArchiveExtracted':i+1,'of':len(archives),'files':len(items)}),flush=True)
 # cPanel preserves archive UNIX modes. Apply a readable mode to exactly these approved raster paths.
 media_names=list(media)
 for start in range(0,len(media_names),100):
  paths=[d.PUBLIC+'/'+name for name in media_names[start:start+100]]
  for path in paths:assert path.startswith(d.PUBLIC+'/assets/suppliers/')and path[len(d.PUBLIC)+1:]in media
  b.api2('fileop',op='chmod',sourcefiles=','.join(paths),metadata='0644',doubledecode='0')
 print(json.dumps({'approvedMediaPermissionsVerified':len(media)}),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:
  for i,_ in enumerate(pool.map(verify_file,media.items()),1):
   if i%100==0:print(json.dumps({'mediaHashesVerified':i,'of':len(media)}),flush=True)
 # A newer release must never be rolled back by this job, even if another publisher ignored the lease.
 assert d.text_content(b,d.HOME,'nodeno-runtime.php')==old_pointer,'Live release changed during staging'
 assert b.public_health()['releaseHash']==proof['baseReleaseHash']
 try:
  # The new helper is installed before its importers. The catalogue switches last.
  b.public_paths=frozenset(set(ui)-{'index.php'})
  for n in ['supplier-products.js','shop-core.js','app.js']:
   if n in ui:b.upload(d.PUBLIC,{n:ui[n]});assert b.public_read(n)==ui[n]
  if 'index.php'in ui:b.upload(d.PUBLIC,{'index.php':ui['index.php']});assert d.text_content(b,d.PUBLIC,'index.php')==ui['index.php']
  pointer(new_pointer);assert d.text_content(b,d.HOME,'nodeno-runtime.php')==new_pointer
  # Allow PHP opcode revalidation to observe the newly installed entry point.
  for attempt in range(5):
   health=b.public_health()
   if health.get('releaseHash')==proof['releaseHash']and health.get('supplierProducts')==len(proof['publishedSupplierIds']):break
   if attempt<4:time.sleep(1)
  assert health['releaseHash']==proof['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']==baseline_health['checkoutEnabled']and health['products']==len(cat['products'])
  assert health['supplierProducts']==len(proof['publishedSupplierIds'])and health['supplierMediaApproved']==len(proof['assets'])
 except Exception:
  pointer(old_pointer);b.upload(d.PUBLIC,originals);assert b.public_health()['releaseHash']==proof['baseReleaseHash'];raise
 receipt={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'productsAdded':len(added),'productsTotal':len(cat['products']),'supplierProducts':health['supplierProducts'],'supplierMediaApproved':health['supplierMediaApproved'],'imagesUploadedAndHashVerified':len(media),'backupRoot':backup,'accountStoragePreserved':True,'checkoutEnabled':health['checkoutEnabled'],'existingPaymentSettingsPreserved':True}
 (E/(Path(args.release).name+'-deployment.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
