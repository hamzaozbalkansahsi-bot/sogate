"""Stage one new ownership key without removing or replacing the active key."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util,json,secrets,requests
R=Path(__file__).resolve().parents[1]
O=R/'artifacts/indexnow-live-diagnosis-20261112'
P=O/'renewed-key.json'
if P.exists():
    raise SystemExit('A staged key already exists; inspect its receipt rather than rotating again')
spec=importlib.util.spec_from_file_location('deploy',R/'scripts/deploy-cpanel.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
b=d.CpanelBackend(allow_writes=True)
domains=b.read('DomainInfo','domains_data',format='hash')
main=domains.get('data',{}).get('main_domain',{})
assert main.get('domain')=='nodenohome.com.tr' and main.get('documentroot')=='/home/nodenoho/public_html'
key=secrets.token_hex(16);name=key+'.txt'
assert name not in d.listing(b,d.PUBLIC)
record={'createdAt':datetime.now(timezone.utc).isoformat(),'key':key,'host':'nodenohome.com','keyLocation':'https://nodenohome.com/'+name,'activeKeyReplaced':False}
P.write_text(json.dumps(record,indent=2)+'\n')
b.upload(d.PUBLIC,{name:key.encode('ascii')})
q=requests.get(record['keyLocation'],timeout=35,allow_redirects=False)
assert q.status_code==200 and q.content==key.encode('ascii')
q=requests.get('https://api.indexnow.org/indexnow',params={'url':'https://nodenohome.com/?lang=tr','key':key,'keyLocation':record['keyLocation']},timeout=45,allow_redirects=False)
record['initialSubmission']={'at':datetime.now(timezone.utc).isoformat(),'status':q.status_code,'response':q.text[:1500]}
P.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'staged':True,'activeKeyReplaced':False,'initialSubmission':record['initialSubmission']}))
