"""Bounded checkout/pricing publication with exact live-base, media and rollback gates."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,secrets,subprocess,sys
import base64
R=Path(__file__).resolve().parents[1];E=R/'artifacts/checkout-experience-20261112'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def require(ok,code):
 if not ok:raise RuntimeError(code)
def emit(stage,**data):print(json.dumps({'stage':stage,**data}),flush=True)
def read(path):return json.loads(path.read_bytes())
def remote_read(d,b,directory,name):
 parts=name.split('/');return d.text_content(b,directory+('/'+'/'.join(parts[:-1])if len(parts)>1 else''),parts[-1])
def upload(d,b,directory,name,body,private=False):
 parts=name.split('/');folder=directory+('/'+'/'.join(parts[:-1])if len(parts)>1 else'')
 if len(parts)>1:d.ensure_directory(b,folder,private=private,permissions='0700'if private else'0755')
 b.upload(folder,{parts[-1]:body})
def backup_public(d,b,directory,name,body):
 if len(body)<=1_000_000:
  upload(d,b,directory,name,body,private=True);require(remote_read(d,b,directory,name)==body,'public_backup_failed');return
 parts=[]
 for i,start in enumerate(range(0,len(body),450_000)):
  part=name+'.part-'+str(i).zfill(3);chunk=body[start:start+450_000];encoded=base64.b64encode(chunk);upload(d,b,directory,part,encoded,private=True);require(remote_read(d,b,directory,part)==encoded,'backup_chunk_failed');parts.append({'file':part,'bytes':len(chunk),'sha256':d.sha256(chunk)})
 manifest=json.dumps({'encoding':'base64','file':name,'bytes':len(body),'sha256':d.sha256(body),'parts':parts},indent=2).encode();upload(d,b,directory,name+'.parts.json',manifest,private=True);require(remote_read(d,b,directory,name+'.parts.json')==manifest,'backup_manifest_failed')
def media(d,base,new,proof):
 # Only the explicit shipping policy marker may differ in the raw catalogue.
 a=read(base['directory']/'private/catalog.json');z=read(new['directory']/'private/catalog.json');z['meta'].pop('shippingPolicyVersion',None);require(a==z,'raw_catalogue_changed_beyond_shipping_marker')
 for n,body in base['all_bytes'].items():
  if n.startswith('public/assets/') or n.startswith(('private/media','private/supplier-','private/door-catalog','private/cabinet-fronts')):require(new['all_bytes'][n]==body,'media_or_supplier_inputs_changed')
 cleanup=read(R/'artifacts/media-cleanup.json');audit=read(R/'artifacts/measurement-orders/full-media-audit.json')
 require(cleanup['publicationReady']is True and not cleanup.get('testOnly'),'media_not_ready')
 require(audit['passed']is True and audit['sourceReportSha256']==d.sha256((R/'artifacts/media-cleanup.json').read_bytes()) and audit['mediaVersion']==new['manifest']['mediaVersion'],'media_audit_stale')
 for n,digest in audit['files'].items():require(d.sha256(new['all_bytes'][n])==digest,'audited_media_changed')
 for i,row in enumerate(cleanup['images'].values(),1):
  for field,digest,folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
   p=R/row[field];require(not p.is_symlink() and p.resolve().is_relative_to((R/'artifacts'/folder).resolve()) and d.sha256(p.read_bytes())==row[digest],'media_source_output_hash_changed')
  if i%1000==0:emit('media_hash_progress',verified=i)
 # Validate exactly the live projection; do not accidentally ship a pending supplier addition.
 projection=read(R/'data/supplier-storefront.json');products=[p for p in a['products']if p.get('productType')=='supplier-item'];current={p['id']:p for p in projection['products']}
 require(all(current.get(p['id'])==p for p in products),'live_supplier_row_changed')
 shadow=E/'approved-live-inputs';(shadow/'data').mkdir(parents=True,exist_ok=True)
 approved=copy.deepcopy(projection);approved['products']=products
 for n,key in [('supplier-media-approved.json','mediaSha256'),('supplier-details.json','detailIndexSha256'),('supplier-details.bin','detailBlobSha256')]:approved[key]=d.sha256(base['all_bytes']['private/'+n])
 for row in approved['review']['files']:
  source=R/row['path'];require(d.sha256(source.read_bytes())==row['sha256'],'supplier_review_changed');target=shadow/row['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
 (shadow/'data/supplier-storefront.json').write_text(json.dumps(approved,ensure_ascii=False),encoding='utf8');d.validate_supplier_publication(shadow,new)
 module('checkout_owner_gate','lib/owner_media_gate.py').verify_owner_catalogues(R,new)
 subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(new['directory'])],check=True)
 record={'passed':True,'releaseHash':proof['releaseHash'],'mediaVersion':new['manifest']['mediaVersion'],'sourceReportSha256':d.sha256((R/'artifacts/media-cleanup.json').read_bytes()),'allOriginalAndOutputHashesVerified':True,'unchangedLiveMediaVerified':True};(E/'media.json').write_text(json.dumps(record,indent=2)+'\n');emit('all_media_gates_passed')
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--media-only',action='store_true');args=p.parse_args();d=module('checkout_deploy_backend','scripts/deploy-cpanel.py');proof=read(E/'build.json');base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release'])
 require(base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash'],'package_hash_changed')
 actual={n for n,b in new['all_bytes'].items()if b!=base['all_bytes'].get(n)};require(actual==set(proof['changedFiles'])|{'private/release.json'},'delta_changed')
 verified=read(E/'media.json')if(E/'media.json').exists()else{}
 if verified.get('passed')is True and verified.get('releaseHash')==proof['releaseHash']and verified.get('sourceReportSha256')==d.sha256((R/'artifacts/media-cleanup.json').read_bytes()):emit('exact_package_media_acceptance_reused')
 else:media(d,base,new,proof)
 if args.media_only:return
 browser=read(E/'browser.json');require(browser['passed']is True and browser['scenarios']==12 and not browser['live'],'browser_acceptance_missing')
 if browser['releaseHash']!=proof['releaseHash']:
  rebase=read(E/'rebase.json');tested=read(E/'tested-manifest.json');smoke=read(E/'browser-rebase.json');require(rebase['testedReleaseHash']==browser['releaseHash']==tested['releaseHash']and rebase['releaseHash']==proof['releaseHash'],'rebase_provenance_mismatch')
  delta={n for n in set(tested['files'])|set(new['manifest']['files'])if tested['files'].get(n)!=new['manifest']['files'].get(n)}
  allowed={'private/catalog.json','private/supplier-catalog.json','private/supplier-details.bin','private/supplier-details.json','private/supplier-media-approved.json'}|{n for n in new['manifest']['files']if n.startswith('public/assets/suppliers/')and n not in tested['files']}
  require(delta==set(rebase['onlyNewlyPublishedSupplierInputsDiffer'])and delta<=allowed,'tested_checkout_code_changed_in_rebase');require(smoke['passed']is True and smoke['scenarios']==2 and smoke['releaseHash']==proof['releaseHash'],'rebase_browser_acceptance_missing');emit('identical_checkout_code_rebase_verified',testedReleaseHash=browser['releaseHash'],finalSmokeScenarios=2)
 review=read(E/'code-review.json');require(review['passed']is True and review['releaseHash']==proof['releaseHash'],'review_missing')
 require('fail 0'in(E/'payment-tests.log').read_text(encoding='utf-8-sig'),'payment_tests_failed')
 b=d.CpanelBackend(allow_writes=args.apply);health=b.public_health();expected=read(E/'live-before-health.json');require(health['releaseHash']==proof['baseReleaseHash']and health['checkoutEnabled']==expected['checkoutEnabled'],'live_base_changed');plan=d.make_plan(new,b)
 public={n[7:]:new['all_bytes'][n]for n in proof['changedFiles']if n.startswith('public/')};b.public_paths=frozenset(public);originals={};created=[];listing=d.listing(b,d.PUBLIC)
 for n in public:
  old=base['all_bytes'].get('public/'+n)
  if old is None:require(n not in listing,'new_public_file_exists');created.append(n)
  else:require((b.public_read(n)if len(old)>1_000_000 else remote_read(d,b,d.PUBLIC,n))==old,'live_public_base_changed');originals[n]=old
 require(sum(map(len,originals.values()))<=d.PUBLIC_BACKUP_MAX_BYTES,'backup_limit')
 if not args.apply:emit('read_only_plan_verified',releaseHash=proof['releaseHash'],publicFiles=len(public));return
 private=plan['privateRoot'];old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private'
 def switch(body):
  d.require_deployment_lease(b);ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(b.post('/execute/Fileman/upload_files',payload,ct));require(d.text_content(b,d.HOME,'nodeno-runtime.php')==body,'pointer_readback_failed')
 with d.deployment_lease(b):
  require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'base_changed_before_lock');old=d.text_content(b,d.HOME,'nodeno-runtime.php');require(old.count(old_private.encode())==1,'runtime_pointer_unexpected');pointer=old.replace(old_private.encode(),private.encode());require(pointer.replace(private.encode(),old_private.encode())==old,'storage_configuration_changed')
  backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-checkout-experience-'+secrets.token_hex(4);d.ensure_directory(b,backup,private=True,permissions='0700');d.ensure_directory(b,backup+'/public',private=True,permissions='0700');b.upload(backup,{'nodeno-runtime.php':old,'delta.json':json.dumps({'base':proof['baseReleaseHash'],'target':proof['releaseHash'],'createdPublic':created}).encode()})
  for n,body in originals.items():backup_public(d,b,backup+'/public',n,body)
  require(d.text_content(b,backup,'nodeno-runtime.php')==old,'pointer_backup_failed')
  emit('backup_verified',publicFiles=len(originals));d.ensure_directory(b,private,private=True,permissions='0700');d.ensure_directory(b,private+'/cache',private=True,permissions='0700')
  files={n[8:]:body for n,body in new['all_bytes'].items()if n.startswith('private/')}
  for i,(n,body)in enumerate(sorted(files.items()),1):b.upload(private,{n:body});emit('private_staging',file=n,current=i,total=len(files))
  sizes=d.listing(b,private);require(all(sizes.get(n,{}).get('type')=='file'and int(sizes[n]['size'])==len(body)for n,body in files.items()),'private_size_mismatch')
  for n in ['release.json','index.html','payment-core.php','payments.php','payment-admin.php','door-commerce.php']:require(d.text_content(b,private,n)==files[n],'private_readback_failed')
  require(d.text_content(b,d.HOME,'nodeno-runtime.php')==old,'pointer_changed_during_staging')
  for n,body in originals.items():require((b.public_read(n)if len(body)>1_000_000 else remote_read(d,b,d.PUBLIC,n))==body,'public_changed_during_staging')
  try:
   for n in sorted(public,key=lambda n:(n in ['app.js','index.php'],n)):upload(d,b,d.PUBLIC,n,public[n]);require((b.public_read(n)if len(public[n])>1_000_000 else remote_read(d,b,d.PUBLIC,n))==public[n],'public_readback_failed')
   switch(pointer);h=b.public_health();require(h['releaseHash']==proof['releaseHash']and h['mediaReady']is True and h['checkoutEnabled']is expected['checkoutEnabled']and h['products']==expected['products'],'live_health_failed')
   for n,body in public.items():
    if n!='index.php':require(b.public_read(n)==body,'public_https_readback_failed')
  except BaseException:
   switch(old)
   for n,body in originals.items():upload(d,b,d.PUBLIC,n,body)
   require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'rollback_failed');emit('rollback_verified');raise
 record={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'backupRoot':backup,'publicFilesChanged':sorted(public),'customerStorageAndCredentialsPreserved':True,'checkoutEnabled':h['checkoutEnabled'],'products':h['products'],'ordersCreated':0,'chargesCreated':0};(E/'deployment.json').write_text(json.dumps(record,indent=2)+'\n');emit('deployment_verified',**record)
if __name__=='__main__':main()
