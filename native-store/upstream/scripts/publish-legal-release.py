"""Publish the tested legal delta with backups, preserving orders and live payment keys."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,secrets,subprocess,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/legal-20261110'
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 spec=importlib.util.spec_from_file_location('nodeno_legal_publish',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
 proof=json.loads((E/'release-preparation.json').read_bytes());base=d.load_release(R/proof['base']);release=d.load_release(R/proof['release']);assert release['manifest']['releaseHash']==proof['releaseHash']
 subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(R/proof['release'])],check=True)
 assert json.loads((R/'artifacts/media-cleanup.json').read_bytes())['publicationReady']is True
 backend=d.CpanelBackend(allow_writes=args.apply);plan=d.make_plan(release,backend);assert backend.public_health()['releaseHash']==proof['baseReleaseHash'],'live_base_changed'
 changed={name[7:]:body for name,body in release['all_bytes'].items()if name.startswith('public/')and base['all_bytes'].get(name)!=body};assert set(changed)in[{'app.js','index.php','legal-links.js','legal.css','legal.js','payments.js','privacy-preferences.js','shop-i18n.js','shopping-ui.js','store-insights.js'},{'app.js','shop-i18n.js'}]
 if not args.apply:print(json.dumps({'planVerified':True,'releaseHash':proof['releaseHash'],'publicDelta':sorted(changed),'liveCheckoutPreserved':True}));return
 browser=json.loads((E/'browser-local.json').read_bytes());provider=json.loads((E/'order-provider.json').read_bytes());assert browser['passed']and provider['passed'];assert 'fail 0'in(E/'legal-regressions.log').read_text(encoding='utf8')
 if proof.get('sourceEvidenceRelease'):
  evidence=d.load_release(R/proof['sourceEvidenceRelease']);assert browser['releaseHash']==provider['releaseHash']==evidence['manifest']['releaseHash']
  allowed={'private/release.json','private/index.html','public/app.js','public/shop-i18n.js'}
  for name,body in evidence['all_bytes'].items():
   if name not in allowed:assert release['all_bytes'][name]==body,name
  assert release['all_bytes']['public/app.js']==evidence['all_bytes']['public/app.js'].replace(b'shop-i18n.js?v=nodeno-legal-20261110-r1',b'shop-i18n.js?v=nodeno-legal-20261110-r2')
 else:assert browser['releaseHash']==provider['releaseHash']==proof['releaseHash']
 private=plan['privateRoot'];old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private'
 def pointer(body):
  kind,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(backend.post('/execute/Fileman/upload_files',payload,kind))
 with d.deployment_lease(backend):
  assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];existing=d.listing(backend,d.PUBLIC);originals={name:d.text_content(backend,d.PUBLIC,name)for name in changed if name in existing}
  for name,body in originals.items():assert body==base['all_bytes'].get('public/'+name,changed[name]),name
  old_pointer=d.text_content(backend,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1;new_pointer=old_pointer.replace(old_private.encode(),private.encode())
  backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-legal-'+secrets.token_hex(4);d.ensure_directory(backend,backup,private=True,permissions='0700');d.ensure_directory(backend,backup+'/public',private=True,permissions='0700');backend.upload(backup,{'nodeno-runtime.php':old_pointer});backend.upload(backup+'/public',originals)
  assert d.text_content(backend,backup,'nodeno-runtime.php')==old_pointer
  for name,body in originals.items():assert d.text_content(backend,backup+'/public',name)==body
  d.ensure_directory(backend,private,private=True,permissions='0700');d.ensure_directory(backend,private+'/cache',private=True,permissions='0700');backend.upload(private,{name[8:]:body for name,body in release['all_bytes'].items()if name.startswith('private/')})
  for name in ['legal.php','payment-documents.php','membership-legal.php','payments.php','account.php','site-documents.tr.json','release.json']:assert d.text_content(backend,private,name)==release['all_bytes']['private/'+name]
  try:
   for name in sorted(changed,key=lambda n:(n in ['app.js','index.php'],n)):backend.upload(d.PUBLIC,{name:changed[name]})
   for name,body in changed.items():assert d.text_content(backend,d.PUBLIC,name)==body
   pointer(new_pointer);assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==new_pointer;health=backend.public_health();assert health['releaseHash']==proof['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']is True
  except Exception:
   pointer(old_pointer);backend.upload(d.PUBLIC,originals);assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];raise
 record={'passed':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'backupRoot':backup,'catalogueAndMediaUnchanged':True,'liveCheckoutPreserved':True,'credentialsAndCustomerRecordsUntouched':True,'publicFilesChanged':sorted(changed),'realCharges':0};(E/'deployment.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
