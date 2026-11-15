"""One private, read-only runtime inspection; remove only its own temporary timer."""
from pathlib import Path
import hashlib, importlib.util, json, secrets, time
R=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=load('social_runtime_deploy','scripts/deploy-cpanel.py');maintenance=load('social_runtime_timer','scripts/run-private-maintenance.py');b=d.CpanelBackend(allow_writes=True)
folder=d.HOME+'/nodeno-social';d.ensure_directory(b,folder,private=True,permissions='0700');nonce=secrets.token_hex(12);name='inspect-'+nonce+'.php';receipt='inspect-'+nonce+'.json'
php=('<?php if(PHP_SAPI!=="cli")exit(1);$body="";$ch=curl_init("https://trends.google.com/trending/rss?geo=TR");curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>20,CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_HTTPHEADER=>["User-Agent: NODENO-Trends/1.0","Accept: application/rss+xml, text/xml"]]);$body=curl_exec($ch);$result=["php"=>PHP_VERSION,"allowUrlFopen"=>ini_get("allow_url_fopen"),"httpCode"=>curl_getinfo($ch,CURLINFO_RESPONSE_CODE),"curlError"=>curl_errno($ch),"bodyBytes"=>is_string($body)?strlen($body):0,"rss"=>is_string($body)&&str_contains($body,"<rss")];file_put_contents(__DIR__."/'+receipt+'",json_encode($result));').encode()
b.upload(folder,{name:php});assert d.text_content(b,folder,name)==php
command='/usr/local/bin/php -d display_errors=0 -d log_errors=0 '+folder+'/'+name+' > /dev/null 2>&1'
before=[hashlib.sha256(r['command'].encode()).hexdigest()for r in maintenance.call_cron(b,'listcron')if 'command'in r]
try:
 maintenance.call_cron(b,'add_line',command=command,minute='*',hour='*',day='*',month='*',weekday='*');print(json.dumps({'privateRuntimeInspectionStarted':True}),flush=True)
 for attempt in range(35):
  if receipt in d.listing(b,folder):
   result=json.loads(d.text_content(b,folder,receipt));e=R/'artifacts/social-engine-20261112';e.mkdir(exist_ok=True);(e/'trend-transport-probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);break
  time.sleep(3)
 else:raise RuntimeError('runtime_inspection_timeout')
finally:
 maintenance.cleanup_job(b,command);after=[hashlib.sha256(r['command'].encode()).hexdigest()for r in maintenance.call_cron(b,'listcron')if 'command'in r];assert sorted(before)==sorted(after)
 print(json.dumps({'temporaryTimerRemoved':True,'otherTimersPreserved':True}),flush=True)
