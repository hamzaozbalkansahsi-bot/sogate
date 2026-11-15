"""Publish only the provider-tested payment delta; preserve live credentials and store data."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,base64,ctypes,hashlib,importlib.util,json,re,secrets,subprocess,sys,urllib.parse,urllib.request
R=Path(__file__).resolve().parents[1];E=R/'artifacts/stripe-sandbox-20261110'

def load_dpapi_credentials():
 class Blob(ctypes.Structure):_fields_=[('length',ctypes.c_ulong),('data',ctypes.POINTER(ctypes.c_ubyte))]
 raw=base64.b64decode((Path.home()/'.codex/private/nodeno-stripe/stripe-live.dpapi').read_text(encoding='utf-8-sig').strip());buffer=(ctypes.c_ubyte*len(raw)).from_buffer_copy(raw);source=Blob(len(raw),buffer);output=Blob()
 if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(output)):raise RuntimeError('private_credential_decryption_failed')
 try:value=json.loads(ctypes.string_at(output.data,output.length).decode('utf8'))
 finally:ctypes.windll.kernel32.LocalFree(output.data)
 assert re.fullmatch(r'(?:sk|rk)_live_[A-Za-z0-9]+',value.get('secretKey',''))
 return value

def connect_refund_events():
 credentials=load_dpapi_credentials();key=credentials['secretKey'];hook_id='we_1UaI6fLFNjlPPKTy0EaEAdCm'
 def api(method,path,form=None):
  headers={'Authorization':'Bearer '+key,'Stripe-Version':'2026-10-28.endive','Accept':'application/json'}
  if form is not None:headers['Content-Type']='application/x-www-form-urlencoded'
  request=urllib.request.Request('https://api.stripe.com'+path,data=None if form is None else urllib.parse.urlencode(form).encode(),headers=headers,method=method)
  with urllib.request.urlopen(request,timeout=30)as response:return json.load(response)
 account=api('GET','/v1/account');assert account['id']=='acct_1UaASFLFNjlPPKTy'and account['charges_enabled']is True
 old=api('GET','/v1/webhook_endpoints/'+hook_id);assert old['livemode']is True and old['url']=='https://nodenohome.com/api/payments/stripe/webhook'
 required=['refund.created','refund.updated','refund.failed'];events=sorted(set(old['enabled_events']+required))
 before={k:old[k]for k in ['id','url','livemode','enabled_events','api_version','status']};(E/'webhook-before.json').write_text(json.dumps(before,indent=2)+'\n')
 updated=old if '*'in old['enabled_events']or all(x in old['enabled_events']for x in required)else api('POST','/v1/webhook_endpoints/'+hook_id,{f'enabled_events[{i}]':event for i,event in enumerate(events)})
 assert updated['status']=='enabled'and all(x in updated['enabled_events']or'*'in updated['enabled_events']for x in required)
 record={k:updated[k]for k in ['id','url','livemode','enabled_events','api_version','status']};(E/'webhook-live.json').write_text(json.dumps(record,indent=2)+'\n');return record

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 spec=importlib.util.spec_from_file_location('nodeno_sandbox_fix_publish',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
 proof=json.loads((E/'release-preparation.json').read_bytes());base=d.load_release(R/proof['base']);release=d.load_release(R/proof['release']);assert release['manifest']['releaseHash']==proof['releaseHash']
 for scenario in ['success','decline','3ds','3ds-fail','refund']:
  check=json.loads((E/(scenario+'.json')).read_bytes());assert check['passed']is True and check['testMode']is True
  for filename in ['payment-store.php','payment-admin.php','payment-stripe.php','payments.php']:assert hashlib.sha256(release['all_bytes']['private/'+filename]).hexdigest()==check['sourceHashes']['hosting/'+filename],scenario
  assert hashlib.sha256(release['all_bytes']['public/payments.js']).hexdigest()==check['sourceHashes']['web/payments.js']
 assert 'fail 0'in(E/'payment-regressions.log').read_text(encoding='utf8')
 assert json.loads((R/'artifacts/media-cleanup.json').read_bytes())['publicationReady']is True
 subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(R/proof['release'])],check=True)
 changed={name[7:]:body for name,body in release['all_bytes'].items()if name.startswith('public/')and base['all_bytes'].get(name)!=body}
 assert set(changed)=={'payments.js','admin-payments.js','app.js','admin.js','admin.html'}
 backend=d.CpanelBackend(allow_writes=args.apply);plan=d.make_plan(release,backend);assert backend.public_health()['releaseHash']==proof['baseReleaseHash']
 if not args.apply:print(json.dumps({'planVerified':True,'releaseHash':proof['releaseHash'],'publicDelta':sorted(changed),'liveCheckoutPreserved':True}));return
 backend.public_paths=frozenset(changed);old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';private=plan['privateRoot']
 def pointer(body):
  content_type,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(backend.post('/execute/Fileman/upload_files',payload,content_type))
 with d.deployment_lease(backend):
  assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];originals={name:backend.public_read(name)for name in changed}
  for name,body in originals.items():assert body==base['all_bytes']['public/'+name]
  old_pointer=d.text_content(backend,d.HOME,'nodeno-runtime.php');assert old_pointer.count(old_private.encode())==1;new_pointer=old_pointer.replace(old_private.encode(),private.encode())
  backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-stripe-refunds-'+secrets.token_hex(4);d.ensure_directory(backend,backup,private=True,permissions='0700');d.ensure_directory(backend,backup+'/public',private=True,permissions='0700');backend.upload(backup,{'nodeno-runtime.php':old_pointer});backend.upload(backup+'/public',originals)
  assert d.text_content(backend,backup,'nodeno-runtime.php')==old_pointer
  for name,body in originals.items():assert d.text_content(backend,backup+'/public',name)==body
  d.ensure_directory(backend,private,private=True,permissions='0700');d.ensure_directory(backend,private+'/cache',private=True,permissions='0700');backend.upload(private,{name[8:]:body for name,body in release['all_bytes'].items()if name.startswith('private/')});assert d.text_content(backend,private,'release.json')==release['all_bytes']['private/release.json']
  try:
   for name in sorted(changed,key=lambda n:(n in ['app.js','admin.js','admin.html'],n)):backend.upload(d.PUBLIC,{name:changed[name]})
   for name,body in changed.items():assert backend.public_read(name)==body
   pointer(new_pointer);assert d.text_content(backend,d.HOME,'nodeno-runtime.php')==new_pointer;health=backend.public_health();assert health['releaseHash']==proof['releaseHash']and health['mediaReady']is True and health['checkoutEnabled']is True
  except Exception:
   pointer(old_pointer);backend.upload(d.PUBLIC,originals);assert backend.public_health()['releaseHash']==proof['baseReleaseHash'];raise
 result={'passed':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'backupRoot':backup,'publicFilesChanged':sorted(changed),'catalogueAndMediaUnchanged':True,'customerDataAndCredentialsPreserved':True,'checkoutEnabled':True,'providerSandboxScenarios':5,'realCharges':0};(E/'deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 hook=connect_refund_events();print(json.dumps({'liveRefundWebhookConnected':True,'events':hook['enabled_events']}))

if __name__=='__main__':main()
