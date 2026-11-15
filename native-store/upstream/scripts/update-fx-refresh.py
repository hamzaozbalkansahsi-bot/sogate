"""Apply the reviewed transport retry fix to the already installed private job."""
from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/project-commerce'
s=importlib.util.spec_from_file_location('update_private_fx',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d)
b=d.CpanelBackend(allow_writes=True);directory=d.HOME+'/nodeno-jobs';name='fx-refresh.py';body=(R/'hosting'/name).read_bytes();digest=lambda value:hashlib.sha256(value).hexdigest()
previous=json.loads((E/'fx-service.json').read_bytes())['jobSha256']
with d.deployment_lease(b):
 old=d.text_content(b,directory,name)
 assert digest(old)in[previous,digest(body)],'Unexpected installed job; review required'
 backup=None
 if old!=body:
  backup='fx-refresh-previous-'+digest(old)+'.py'
  b.upload(directory,{backup:old});assert d.text_content(b,directory,backup)==old
  b.upload(directory,{name:body})
 assert d.text_content(b,directory,name)==body
 receipt={'updated':True,'previousSha256':previous,'jobSha256':digest(body),'backup':directory+'/'+backup if backup else None,'tlsVerified':True,'transportTimeoutSeconds':20,'maximumAttempts':3,'cacheLifetimeUnchanged':True,'cronUnchanged':True}
 (E/'fx-service-update.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
