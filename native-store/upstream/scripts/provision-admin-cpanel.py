"""Provision one hashed, expiring owner setup code outside the web root. Never prints secrets."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,secrets,time
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nodeno_deployment',ROOT/'scripts/deploy-cpanel.py');deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args();backend=deploy.CpanelBackend(allow_writes=args.apply)
 response=requests.get('https://nodenohome.com/api/admin/session',timeout=35);response.raise_for_status();status=response.json()
 if status.get('setupRequired') is not True:raise deploy.DeployError('owner_already_exists_or_management_not_ready')
 storage=deploy.remote_path(deploy.HOME+'/nodeno-data',private=True);entries=deploy.listing(backend,storage)
 target=ROOT/'artifacts/control-seo/NODENO_Yonetim_Ilk_Kurulum.txt'
 if 'admin-bootstrap.json' in entries:
  if status.get('bootstrapAvailable') is True and target.is_file():print(json.dumps({'status':'existing_private_setup_ready','file':str(target)},ensure_ascii=True));return
  raise deploy.DeployError('existing_setup_requires_manual_expiry_review')
 if not args.apply:print(json.dumps({'status':'ready_to_provision','email':'hamzaozbalkan@gmail.com','privateStorage':True,'remoteWrites':False}));return
 deploy.ensure_directory(backend,storage,private=True,permissions='0700');token=secrets.token_hex(32);expires=int(time.time())+7*86400;seed={'schema':1,'email':'hamzaozbalkan@gmail.com','tokenHash':hashlib.sha256(token.encode()).hexdigest(),'expiresAt':expires};body=json.dumps(seed).encode()
 # Save the only plaintext copy locally first; no token or password enters the remote seed.
 target.parent.mkdir(exist_ok=True);target.write_text('NODENO YÖNETİM İLK KURULUM\n\nAdres: https://nodenohome.com/yonetim\nE-posta: hamzaozbalkan@gmail.com\nKurulum kodu: '+token+'\n\nKod 7 gün geçerlidir. İlk kurulum bölümünden kendi parolanızı belirleyin ve doğrulama uygulamanızı bağlayın. Kurtarma kodlarınızı güvenli saklayın. Bu dosyayı kimseyle paylaşmayın.\n',encoding='utf-8')
 backend.upload(storage,{'admin-bootstrap.json':body});readback=deploy.text_content(backend,storage,'admin-bootstrap.json')
 if readback!=body:raise deploy.DeployError('setup_seed_readback_mismatch')
 result=requests.get('https://nodenohome.com/api/admin/session',timeout=35);result.raise_for_status()
 if result.json().get('bootstrapAvailable') is not True:raise deploy.DeployError('setup_not_available_after_provision')
 print(json.dumps({'status':'private_setup_ready','file':str(target),'expiresAt':expires,'plaintextUploaded':False},ensure_ascii=True))
if __name__=='__main__':
 try:main()
 except deploy.DeployError as e:print(json.dumps({'status':'stopped','code':str(e)}));raise SystemExit(1)
 except Exception:print(json.dumps({'status':'stopped','code':'provision_failed'}));raise SystemExit(1)
