"""One private, read-only runtime inspection; remove only its own temporary timer."""
from pathlib import Path
import hashlib, importlib.util, json, secrets, time
R=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=load('social_runtime_deploy','scripts/deploy-cpanel.py');maintenance=load('social_runtime_timer','scripts/run-private-maintenance.py');b=d.CpanelBackend(allow_writes=True)
folder=d.HOME+'/nodeno-social';d.ensure_directory(b,folder,private=True,permissions='0700');nonce=secrets.token_hex(12);name='inspect-'+nonce+'.php';receipt='inspect-'+nonce+'.json'
php=('<?php if(PHP_SAPI!=="cli")exit(1); $bins=array_values(array_filter(["/usr/bin/ffmpeg","/usr/local/bin/ffmpeg"],static fn($p)=>is_file($p)&&is_executable($p)));file_put_contents(__DIR__+"/'+receipt+'",json_encode(["php"=>PHP_VERSION,"gd"=>extension_loaded("gd"),"imagick"=>extension_loaded("imagick"),"curl"=>extension_loaded("curl"),"procOpen"=>function_exists("proc_open"),"ffmpeg"=>$bins,"sqlite"=>extension_loaded("pdo_sqlite")]));').replace('__DIR__+','__DIR__.').encode()
b.upload(folder,{name:php});assert d.text_content(b,folder,name)==php
command='/usr/local/bin/php -d display_errors=0 -d log_errors=0 '+folder+'/'+name+' > /dev/null 2>&1'
before=[hashlib.sha256(r['command'].encode()).hexdigest()for r in maintenance.call_cron(b,'listcron')if 'command'in r]
try:
 maintenance.call_cron(b,'add_line',command=command,minute='*',hour='*',day='*',month='*',weekday='*');print(json.dumps({'privateRuntimeInspectionStarted':True}),flush=True)
 for attempt in range(35):
  if receipt in d.listing(b,folder):
   result=json.loads(d.text_content(b,folder,receipt));e=R/'artifacts/social-engine-20261112';e.mkdir(exist_ok=True);(e/'runtime.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);break
  time.sleep(3)
 else:raise RuntimeError('runtime_inspection_timeout')
finally:
 maintenance.cleanup_job(b,command);after=[hashlib.sha256(r['command'].encode()).hexdigest()for r in maintenance.call_cron(b,'listcron')if 'command'in r];assert sorted(before)==sorted(after)
 print(json.dumps({'temporaryTimerRemoved':True,'otherTimersPreserved':True}),flush=True)
