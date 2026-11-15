"""Publish the reviewed social module, preserving all existing commerce storage."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,secrets,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/admin-mobile-social-20261112'
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def emit(stage,**safe):print(json.dumps({'stage':stage,**safe}),flush=True)
def require(value,code):
 if not value:raise RuntimeError(code)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args();d=module('social_engine_publish_backend','scripts/deploy-cpanel.py');proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release'])
 require(base['manifest']['releaseHash']==proof['baseReleaseHash'] and new['manifest']['releaseHash']==proof['releaseHash'],'local_release_changed')
 delta={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b};require(delta==set(proof['changedFiles'])|{'private/release.json'},'unexpected_release_delta')
 require(all(new['all_bytes'][n]==base['all_bytes'][n]for n in base['all_bytes']if n not in delta),'existing_commerce_bytes_changed')
 allowed={'private/social-campaigns.php','private/social-engine.php','private/social-media.php','private/social-worker.php','private/social-admin.php','public/admin.css','public/admin.js','public/admin.html','public/admin-social.js'}|{'public/assets/social-headlines/'+p.name for p in (R/'web/assets/social-headlines').glob('headline-*.png')}
 if proof.get('correction')=='coffee_colour':
  require(proof['baseReleaseHash']=='8727a68aef1301e322d908b87c4e70eac189d99bbc0a550f55efb7eb37530965' and set(proof['changedFiles'])=={'private/social-campaigns.php'},'topic_correction_scope_changed');scope={'private/social-campaigns.php'}
 else:
  require(proof['baseReleaseHash']=='3f8a299cb0e28aaa4c99c206a2d7ab31eaab7635d38fb343f3e1cae448dfc73f','unexpected_live_base')
  require(set(proof['changedFiles'])==allowed and len(allowed)==65,'mobile_campaign_scope_changed');scope=allowed
 for n in allowed:
  if n.startswith('public/assets/social-headlines/'):require(new['all_bytes'][n]==(R/'web'/n[7:]).read_bytes(),'creative_asset_changed')
  if n.startswith('private/social-'):require(new['all_bytes'][n]==(R/'hosting'/Path(n).name).read_bytes(),'source_module_changed')
  if n in {'public/admin-social.js','public/admin.css'}:require(new['all_bytes'][n]==(R/'web'/Path(n).name).read_bytes(),'source_ui_changed')
 media=module('social_engine_media_gate','scripts/publish-social-links-20261112.py');media.O=R/proof['release'];media.E=E;media.verify_unchanged_media(d,new,proof);emit('current_media_and_scope_verified',releaseHash=proof['releaseHash'])
 backend=d.CpanelBackend(allow_writes=args.apply);require(backend.public_health()['releaseHash']==proof['baseReleaseHash'],'live_base_changed');plan=d.make_plan(new,backend)
 public={n[7:]:new['all_bytes'][n]for n in scope if n.startswith('public/')};backend.public_paths=frozenset(public)
 originals={n:base['all_bytes']['public/'+n]for n in public if 'public/'+n in base['all_bytes']}
 def read_public(n):return d.text_content(backend,d.PUBLIC,n)if n in d.CRITICAL else backend.public_read(n)
 for n,b in originals.items():require(read_public(n)==b,'live_public_base_changed')
 if not args.apply:emit('read_only_plan_verified',releaseHash=proof['releaseHash'],publicFiles=sorted(public));return
 for name in ['browser-local.json','code-review.json']:
  record=json.loads((E/name).read_bytes());require(record.get('passed')is True and record.get('releaseHash')==proof['releaseHash'],'acceptance_missing_'+name)
 old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';private=plan['privateRoot']
 checked_directories=set()
 def remote_upload(directory,name,body):
  parts=name.split('/');folder=directory+('/'+'/'.join(parts[:-1])if len(parts)>1 else'')
  if folder not in checked_directories:d.ensure_directory(backend,folder,private=directory!=d.PUBLIC,permissions='0700'if directory!=d.PUBLIC else'0755');checked_directories.add(folder)
  backend.upload(folder,{parts[-1]:body})
 with d.deployment_lease(backend):
  require(backend.public_health()['releaseHash']==proof['baseReleaseHash'],'base_changed_before_lease');old_pointer=d.text_content(backend,d.HOME,'nodeno-runtime.php');require(old_pointer.count(old_private.encode())==1,'unexpected_private_pointer');new_pointer=old_pointer.replace(old_private.encode(),private.encode());require(new_pointer.replace(private.encode(),old_private.encode())==old_pointer,'runtime_storage_options_changed')
  backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-social-engine-'+secrets.token_hex(4);d.ensure_directory(backend,backup,private=True,permissions='0700');backend.upload(backup,{'nodeno-runtime.php':old_pointer});require(d.text_content(backend,backup,'nodeno-runtime.php')==old_pointer,'pointer_backup_failed')
  for n,b in originals.items():remote_upload(backup+'/public',n,b)
  d.ensure_directory(backend,private,private=True,permissions='0700');d.ensure_directory(backend,private+'/cache',private=True,permissions='0700');files={n[8:]:b for n,b in new['all_bytes'].items()if n.startswith('private/')}
  for i,(n,b)in enumerate(sorted(files.items()),1):backend.upload(private,{n:b});emit('private_staged_file',file=n,current=i,total=len(files))
  listing=d.listing(backend,private);require(all(listing.get(n,{}).get('type')=='file'and int(listing[n]['size'])==len(b)for n,b in files.items()),'private_staging_size_mismatch')
  for n in ['release.json','control-http.php','social-engine.php','social-providers.php','social-worker.php','social-admin.php','social-media.php']:require(d.text_content(backend,private,n)==files[n],'private_source_readback_failed')
  require(d.text_content(backend,d.HOME,'nodeno-runtime.php')==old_pointer,'pointer_changed_during_staging')
  deps=[n for n in public if n not in {'index.php','admin.js','admin.html'}]
  def switch(body):
   d.require_deployment_lease(backend);ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(backend.post('/execute/Fileman/upload_files',payload,ct));require(d.text_content(backend,d.HOME,'nodeno-runtime.php')==body,'runtime_pointer_readback_failed')
  try:
   for n in sorted(deps):remote_upload(d.PUBLIC,n,public[n]);require(backend.public_read(n)==public[n],'public_dependency_readback_failed')
   switch(new_pointer)
   for n in ['index.php','admin.js','admin.html']:
    if n in public:remote_upload(d.PUBLIC,n,public[n])
   health=backend.public_health();require(health['releaseHash']==proof['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']is True and health['products']==3602,'public_health_mismatch')
   for n,b in public.items():require(read_public(n)==b,'public_bytes_mismatch')
  except BaseException:
   switch(old_pointer)
   for n,b in originals.items():remote_upload(d.PUBLIC,n,b)
   require(backend.public_health()['releaseHash']==proof['baseReleaseHash'],'rollback_failed');raise
 record={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'publicFilesChanged':sorted(public),'backupRoot':backup,'accountPaymentAndMediaStoragePreserved':True,'cataloguePricesCheckoutUnchanged':True,'ordersCreated':0,'chargesCreated':0,'remoteDeletions':False};(E/'deployment.json').write_text(json.dumps(record,indent=2)+'\n');emit('deployment_verified',**record)
if __name__=='__main__':main()
