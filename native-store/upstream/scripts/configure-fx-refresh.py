"""Install the private, TLS-verified TCMB cache refresh job on the owned host."""
from pathlib import Path
import importlib.util,sys,json,hashlib,time,urllib.parse,requests
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('configure_private_fx',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d)
b=d.CpanelBackend(allow_writes=True);directory=d.HOME+'/nodeno-jobs';filename='fx-refresh.py';storage=d.HOME+'/nodeno-data';body=(R/'hosting'/filename).read_bytes()
def cron(function,**params):
 payload=urllib.parse.urlencode({'cpanel_jsonapi_apiversion':'2','cpanel_jsonapi_module':'Cron','cpanel_jsonapi_func':function,**params}).encode();result=b.post('/json-api/cpanel',payload,'application/x-www-form-urlencoded').get('cpanelresult',{});assert result.get('event',{}).get('result')==1;return result.get('data',[])
command='/usr/bin/python3 '+directory+'/'+filename+' --storage '+storage+' --refresh-seconds 300 >/dev/null 2>&1'
before={r['command']for r in cron('listcron')if isinstance(r,dict)and r.get('command')}
d.ensure_directory(b,directory,private=True,permissions='0700')
if filename in d.listing(b,directory):assert d.text_content(b,directory,filename)==body,'Existing refresh job differs; review before replacing'
else:b.upload(directory,{filename:body})
assert d.text_content(b,directory,filename)==body
if command not in before:cron('add_line',command=command,minute='*',hour='*',day='*',month='*',weekday='*')
after={r['command']for r in cron('listcron')if isinstance(r,dict)and r.get('command')};assert before<=after and command in after
print(json.dumps({'stage':'verified_private_refresh_installed','jobSha256':hashlib.sha256(body).hexdigest(),'existingJobsPreserved':True}),flush=True)
result=None
for _ in range(25):
 time.sleep(4)
 response=requests.get('https://nodenohome.com/api/exchange-rates',timeout=15)
 if response.status_code!=200:continue
 result=response.json()
 if result.get('policy')=='week_to_date_highest_forex_selling'and result.get('validUntil',0)>time.time()and result.get('rates',{}).get('USD'):break
assert result and result.get('validUntil',0)>time.time(),'Refresh installed, but first verified cache is not ready'
receipt={'installed':True,'privateDirectory':directory,'jobSha256':hashlib.sha256(body).hexdigest(),'schedule':'every minute; refresh every 300 seconds or on pending publication','existingJobsPreserved':True,'policy':result['policy'],'revision':result['revision'],'sources':result['sources'],'usd':result['rates']['USD'],'eur':result['rates']['EUR'],'paymentEnabled':False}
(R/'artifacts/project-commerce/fx-service.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
