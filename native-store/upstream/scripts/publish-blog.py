"""Current-base, shared-lease publication of the reviewed blog delta with rollback."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,secrets,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/blog-20261112'
sys.path.insert(0,str(R))
from lib.blog_bundle import unpack_bundle
from lib.blog_publication import validate_blog_publication
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def require(value,code):
 if not value:raise RuntimeError(code)
def emit(stage,**safe):print(json.dumps({'stage':stage,**safe}),flush=True)
def verify_scope(base,new,proof,expected):
 require(not proof.get('preview')and not new['manifest'].get('testOnly'),'preview_not_deployable')
 require(base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash'],'release_changed')
 changed={name for name,body in new['all_bytes'].items()if body!=base['all_bytes'].get(name)}
 require(changed==set(proof['changedFiles'])|{'private/release.json'},'blog_delta_changed')
 require(set(expected)==set(proof['changedFiles'])and all(new['all_bytes'].get(name)==body for name,body in expected.items()),'unreviewed_blog_sources')
 require(all(new['all_bytes'].get(name)==body for name,body in base['all_bytes'].items()if name not in changed),'unrelated_release_bytes_changed')
 for name in ['catalog.json','config.json','media.json','media-approved.json','supplier-catalog.json','supplier-details.json','supplier-details.bin','supplier-media-approved.json']:
  key='private/'+name
  if key in base['all_bytes']:require(base['all_bytes'][key]==new['all_bytes'].get(key),'catalogue_commerce_or_media_changed')
 bank=json.loads(new['all_bytes']['private/blog-bank.json']);require(bank.get('publicationReady')is True and len(bank['articles'])>=250,'editorial_bank_incomplete')
 validate_blog_publication(new['all_bytes'])
 index=json.loads(new['all_bytes'].get('private/blog-images.json',b'{}'));blob=new['all_bytes'].get('private/blog-images.bin',b'');unpack_bundle(index,blob)
 require(not any(name.startswith('public/assets/blog/')for name in new['all_bytes']),'static_editorial_images_rejected')
 for a in bank['articles']:
  require(set(a.get('locales',{}))>={'en','ru','ar'},'editorial_translations_incomplete')
  for image in [a['image'],*[x['image']for x in a['locales'].values()]]:
   require(image.get('storage')=='private-bundle'and 'public'+image['url']not in new['all_bytes'],'public_editorial_image_rejected');entry=index.get('files',{}).get(image['url']);require(isinstance(entry,dict)and type(entry.get('offset'))is int and type(entry.get('length'))is int and entry['offset']>=0 and 0<entry['length']<=2000000 and entry['offset']+entry['length']<=len(blob),'blog_media_index_invalid');require(hashlib.sha256(blob[entry['offset']:entry['offset']+entry['length']]).hexdigest()==image['sha256']==entry.get('sha256'),'blog_media_integrity_failed')
def assert_current(backend,proof):
 health=backend.public_health();require(health.get('releaseHash')==proof['baseReleaseHash'],'live_base_changed');require(health.get('mediaReady')is True,'live_media_not_ready');return health
def verify_date_scope(base,new,proof,expected):
 require(base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash'],'release_changed');delta={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b}
 require(delta==set(expected)|{'private/release.json'}and set(proof['changedFiles'])==set(expected),'date_policy_scope_changed');require(all(new['all_bytes'].get(n)==b for n,b in expected.items()),'date_policy_sources_changed')
 allowed={'public/date-time.js','private/date-time.php','private/date-time-regions.json','public/app.js','public/admin.js','public/admin-social.js','public/admin-suppliers.js','public/admin-analytics.js','private/index.html','public/admin.html','private/payment-documents.php'};require(set(expected)<=allowed,'non_date_change_rejected');require(all(new['all_bytes'].get(n)==b for n,b in base['all_bytes'].items()if n not in delta),'unrelated_release_bytes_changed')
def main():
 global E
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--date-only',action='store_true');args=p.parse_args();d=module('blog_deploy','scripts/deploy-cpanel.py');prepare=module('blog_prepare','scripts/prepare-date-time-release.py'if args.date_only else'scripts/prepare-blog-release.py');readback=module('blog_private_readback','scripts/publish-paint-release.py')
 if args.date_only:E=R/'artifacts/date-time-20261112'
 proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release']);bank={'articles':[]}
 if args.date_only:verify_date_scope(base,new,proof,prepare.changes_for(base))
 else:bank=json.loads(new['all_bytes']['private/blog-bank.json']);verify_scope(base,new,proof,prepare.changes_for(base,bank))
 require(json.loads((R/'artifacts/media-cleanup.json').read_bytes()).get('publicationReady')is True,'media_publication_gate_not_ready')
 if not args.date_only:
  quality=json.loads((E/'content-quality.json').read_bytes());require(quality['bankSha256']==hashlib.sha256(new['all_bytes']['private/blog-bank.json']).hexdigest()and not quality['heldTranslations'],'editorial_quality_stale')
 for name in ['browser-local.json','code-review.json']:
  record=json.loads((E/name).read_bytes());require(record.get('passed')is True and record.get('releaseHash')==proof['releaseHash'],'acceptance_missing_'+name)
 b=d.CpanelBackend(allow_writes=args.apply);health=assert_current(b,proof);plan=d.make_plan(new,b);public={name[7:]:new['all_bytes'][name]for name in proof['changedFiles']if name.startswith('public/')};b.public_paths=frozenset(public);originals={name:base['all_bytes']['public/'+name]for name in public if'public/'+name in base['all_bytes']}
 def public_bytes(name):return d.text_content(b,d.PUBLIC,name)if name in ['index.php','.htaccess','admin.html']else b.public_read(name)
 for name,body in originals.items():require(public_bytes(name)==body,'live_public_base_changed')
 emit('blog_read_only_plan_verified',releaseHash=proof['releaseHash'],baseReleaseHash=proof['baseReleaseHash'],articles=len(bank['articles']),publicFiles=len(public),catalogueProducts=health['products'])
 if not args.apply:return
 checked=set()
 def upload(directory,name,body):
  rel=Path(name);folder=directory+(''if rel.parent.as_posix()=='.'else'/'+rel.parent.as_posix())
  if folder not in checked:d.ensure_directory(b,folder,private=directory!=d.PUBLIC,permissions='0755'if directory==d.PUBLIC else'0700');checked.add(folder)
  b.upload(folder,{rel.name:body})
 with d.deployment_lease(b):
  assert_current(b,proof);old=d.text_content(b,d.HOME,'nodeno-runtime.php');old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';private=plan['privateRoot'];require(old.count(old_private.encode())==1,'runtime_pointer_unexpected');pointer=old.replace(old_private.encode(),private.encode());require(pointer.replace(private.encode(),old_private.encode())==old,'persistent_storage_configuration_changed')
  backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-blog-'+secrets.token_hex(4);d.ensure_directory(b,backup,private=True,permissions='0700');b.upload(backup,{'nodeno-runtime.php':old});require(d.text_content(b,backup,'nodeno-runtime.php')==old,'pointer_backup_failed')
  for name,body in originals.items():upload(backup+'/public',name,body);require(readback.verified_private_read(d,b,backup+'/public'+(''if Path(name).parent.as_posix()=='.'else'/'+Path(name).parent.as_posix()),Path(name).name,body)==body,'public_backup_readback_failed')
  d.ensure_directory(b,private,private=True,permissions='0700');d.ensure_directory(b,private+'/cache',private=True,permissions='0700');files={name[8:]:body for name,body in new['all_bytes'].items()if name.startswith('private/')}
  for i,(name,body)in enumerate(sorted(files.items()),1):b.upload(private,{name:body});emit('staged_private',file=name,current=i,total=len(files))
  listed=d.listing(b,private);require(all(listed.get(name,{}).get('type')=='file'and int(listed[name]['size'])==len(body)for name,body in files.items()),'private_size_mismatch')
  for name in ['release.json',*{x[8:]for x in proof['changedFiles']if x.startswith('private/')}]:require(readback.verified_private_read(d,b,private,name,files[name])==files[name],'private_readback_failed')
  require(d.text_content(b,d.HOME,'nodeno-runtime.php')==old,'pointer_changed_during_staging')
  def switch(body):
   d.require_deployment_lease(b);kind,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(b.post('/execute/Fileman/upload_files',payload,kind));require(d.text_content(b,d.HOME,'nodeno-runtime.php')==body,'runtime_pointer_readback_failed')
  try:
   # Additive dependencies first; the entry point and pointer change only after readback.
   for i,name in enumerate(sorted(n for n in public if n not in ['index.php','.htaccess']),1):
    upload(d.PUBLIC,name,public[name]);require(public_bytes(name)==public[name],'public_blog_asset_mismatch')
    if i%50==0:emit('public_blog_assets_verified',current=i,total=len(public)-1)
   if 'index.php'in public:upload(d.PUBLIC,'index.php',public['index.php']);require(public_bytes('index.php')==public['index.php'],'entrypoint_readback_failed')
   if '.htaccess'in public:upload(d.PUBLIC,'.htaccess',public['.htaccess']);require(public_bytes('.htaccess')==public['.htaccess'],'routing_readback_failed')
   switch(pointer)
   after=b.public_health();require(after['releaseHash']==proof['releaseHash']and after['products']==health['products']and after['mediaReady']is True and after['checkoutEnabled']==health['checkoutEnabled'],'live_blog_health_mismatch')
  except BaseException:
   # Attempt every restoration even when one file fails; never claim a partial rollback worked.
   failures=[]
   try:switch(old)
   except BaseException:failures.append('pointer')
   for name,body in originals.items():
    try:upload(d.PUBLIC,name,body);require(public_bytes(name)==body,'rollback_byte_mismatch')
    except BaseException:failures.append(name)
   try:require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'rollback_health_mismatch')
   except BaseException:failures.append('health')
   if failures:raise RuntimeError('manual_restore_required')from None
   raise
 record={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'articles':len(bank['articles']),'publicProducts':health['products'],'backupRoot':backup,'otherChatChangesPreserved':True,'cataloguePricesCustomerPaymentStoragePreserved':True,'ordersCreated':0,'chargesCreated':0};(E/'deployment.json').write_text(json.dumps(record,indent=2)+'\n');emit('blog_deployment_verified',**record)
if __name__=='__main__':main()
