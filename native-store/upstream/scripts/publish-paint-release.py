"""Lease-protected paint catalogue publication on the user's existing Turhost host."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,secrets,sys,base64,http.client,ssl,urllib.parse
R=Path(__file__).resolve().parents[1];E=R/'artifacts/bianca-20261112'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def require(v,code):
 if not v:raise RuntimeError(code)
def emit(stage,**data):print(json.dumps({'stage':stage,**data}),flush=True)
def verified_private_read(d,b,directory,name,expected):
 if len(expected)<900000:return d.text_content(b,directory,name)
 d.remote_path(directory,private=True);d.component(name);user,password=b.probe.credentials();authorization=base64.b64encode((user+':'+password).encode()).decode('ascii');connection=http.client.HTTPSConnection(d.HOST,d.PORT,timeout=90,context=ssl.create_default_context())
 try:
  connection.request('GET','/download?'+urllib.parse.urlencode({'file':directory+'/'+name}),headers={'Authorization':'Basic '+authorization,'Accept-Encoding':'identity'});response=connection.getresponse()
  require(response.status==200 and(response.getheader('Content-Encoding')or'identity')=='identity','private_download_rejected');body=response.read(len(expected)+1);require(len(body)==len(expected),'private_download_size_mismatch');return body
 finally:connection.close()
def main():
 global E
 a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');a.add_argument('--evidence-dir',default='artifacts/bianca-20261112',choices=['artifacts/bianca-20261112','artifacts/paint-completion-20261112','artifacts/paint-resolution-20261112','artifacts/paint-alternatives-20261112']);args=a.parse_args();E=R/args.evidence_dir;d=module('paint_deploy','scripts/deploy-cpanel.py');proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release']);require(base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash'],'release_changed')
 delta={n for n,b in new['all_bytes'].items()if base['all_bytes'].get(n)!=b};require(delta==set(proof['changedFiles'])|{'private/release.json'},'delta_changed')
 allowed={'private/catalog.json','private/supplier-catalog.json','private/supplier-details.json','private/supplier-details.bin','private/supplier-media-approved.json','private/suppliers.php','private/supplier-watch.php','private/supplier-products.php','private/index.html','public/app.js','public/admin-suppliers.js','public/admin.js','public/admin.html','public/paint-recommendations.js','public/date-time.js'}|{'public'+path for path in json.loads((E/'catalogue-prepared.json').read_bytes())['assets']}
 require(set(proof['changedFiles'])<=allowed,'unexpected_scope');require(all(new['all_bytes'][n]==b for n,b in base['all_bytes'].items()if n not in delta),'unrelated_bytes_changed')
 before=json.loads(base['all_bytes']['private/catalog.json']);after=json.loads(new['all_bytes']['private/catalog.json']);old={p['id']:p for p in before['products']}
 for p in after['products']:
  if p['id']in old:require(p==old[p['id']]or(not any(k in old[p['id']]for k in ['finishState','paintSurface'])and{k:v for k,v in p.items()if k not in ['finishState','paintSurface']}==old[p['id']]),'existing_product_changed')
 require(len(after['products'])==proof['publicProducts']and len(after['products'])-len(before['products'])==proof['newProducts'],'product_count_changed')
 media=module('paint_media_gate','scripts/publish-social-links-20261112.py');media.O=R/proof['release'];media.E=E;media.verify_unchanged_media(d,new,proof);emit('media_and_scope_verified',releaseHash=proof['releaseHash'])
 b=d.CpanelBackend(allow_writes=args.apply);require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'live_base_changed');plan=d.make_plan(new,b)
 public={n[7:]:new['all_bytes'][n]for n in proof['changedFiles']if n.startswith('public/')};b.public_paths=frozenset(public);originals={n:base['all_bytes']['public/'+n]for n in public if'public/'+n in base['all_bytes']}
 for n,body in originals.items():require(b.public_read(n)==body,'public_base_changed')
 if not args.apply:emit('read_only_plan_verified',newProducts=proof['newProducts'],publicFiles=len(public));return
 for name in ['browser-local.json','code-review.json']:
  r=json.loads((E/name).read_bytes());require(r.get('passed')and r.get('releaseHash')==proof['releaseHash'],'acceptance_missing_'+name)
 checked=set()
 def upload(directory,name,body):
  path=Path(name);folder=directory+(''if path.parent.as_posix()=='.'else'/'+path.parent.as_posix())
  if folder not in checked:d.ensure_directory(b,folder,private=directory!=d.PUBLIC,permissions='0755'if directory==d.PUBLIC else'0700');checked.add(folder)
  b.upload(folder,{path.name:body})
 with d.deployment_lease(b):
  require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'base_changed_before_lease');old_pointer=d.text_content(b,d.HOME,'nodeno-runtime.php');old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';require(old_pointer.count(old_private.encode())==1,'pointer_unexpected');private=plan['privateRoot'];new_pointer=old_pointer.replace(old_private.encode(),private.encode());require(new_pointer.replace(private.encode(),old_private.encode())==old_pointer,'storage_changed')
  backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-paints-'+secrets.token_hex(4);d.ensure_directory(b,backup,private=True,permissions='0700');b.upload(backup,{'nodeno-runtime.php':old_pointer});require(d.text_content(b,backup,'nodeno-runtime.php')==old_pointer,'backup_failed')
  for n,body in originals.items():upload(backup+'/public',n,body)
  d.ensure_directory(b,private,private=True,permissions='0700');d.ensure_directory(b,private+'/cache',private=True,permissions='0700');files={n[8:]:body for n,body in new['all_bytes'].items()if n.startswith('private/')}
  for i,(name,body)in enumerate(sorted(files.items()),1):b.upload(private,{name:body});emit('staged_private_file',file=name,current=i,total=len(files))
  listed=d.listing(b,private);require(all(listed.get(n,{}).get('type')=='file'and int(listed[n]['size'])==len(body)for n,body in files.items()),'private_size_mismatch')
  for n in ['release.json','catalog.json','supplier-catalog.json','suppliers.php','supplier-watch.php','supplier-products.php']:require(verified_private_read(d,b,private,n,files[n])==files[n],'private_readback_failed')
  require(d.text_content(b,d.HOME,'nodeno-runtime.php')==old_pointer,'pointer_changed_during_staging')
  def switch(body):
   d.require_deployment_lease(b);ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(b.post('/execute/Fileman/upload_files',payload,ct));require(d.text_content(b,d.HOME,'nodeno-runtime.php')==body,'pointer_readback_failed')
  try:
   # Additive media/modules first; retain old app entrypoints until private catalogue is active.
   for n in sorted(public):
    if n not in ['app.js','admin.js','admin.html','admin-suppliers.js']:upload(d.PUBLIC,n,public[n]);require(b.public_read(n)==public[n],'dependency_readback_failed')
   for n in ['app.js','admin-suppliers.js','admin.js','admin.html']:
    if n in public:upload(d.PUBLIC,n,public[n])
   switch(new_pointer);health=b.public_health();require(health['releaseHash']==proof['releaseHash']and health['products']==proof['publicProducts']and health['mediaReady']and health['checkoutEnabled'],'health_mismatch')
   for n,body in public.items():require(b.public_read(n)==body,'public_readback_failed')
  except BaseException:
   switch(old_pointer)
   for n,body in originals.items():upload(d.PUBLIC,n,body)
   require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'rollback_failed');raise
 record={'passed':True,'releaseHash':proof['releaseHash'],'newProducts':proof['newProducts'],'publicProducts':health['products'],'mediaReady':health['mediaReady'],'backupRoot':backup,'accountPaymentStoragePreserved':True,'ordersCreated':0,'chargesCreated':0};(E/'deployment.json').write_text(json.dumps(record,indent=2));emit('deployment_verified',**record)
if __name__=='__main__':main()
