"""Run one bounded private CLI maintenance job through hosting administration, then remove its timer."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,re,time,urllib.parse
R=Path(__file__).resolve().parents[1];PRIVATE=Path('C:/Users/Hamza ÖZBALKAN/.codex/private/nodeno-stripe')
def deployment_module():
 spec=importlib.util.spec_from_file_location('nodeno_private_deploy',R/'scripts/deploy-cpanel.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def build_command(nonce):
 if not isinstance(nonce,str)or not re.fullmatch('[a-f0-9]{64}',nonce):raise ValueError('invalid_nonce')
 return '/usr/local/bin/php -d display_errors=0 -d log_errors=0 -d zend.exception_ignore_args=1 /home/nodenoho/nodeno-maintenance/private-maintenance.php '+nonce+' > /home/nodenoho/nodeno-maintenance/job-'+nonce+'.log 2>&1'
def call_cron(backend,action,**params):
 if action not in ['listcron','add_line','remove_line']:raise ValueError('unsupported_cron_action')
 body=urllib.parse.urlencode({'cpanel_jsonapi_apiversion':'2','cpanel_jsonapi_module':'Cron','cpanel_jsonapi_func':action,**params}).encode()
 result=backend.post('/json-api/cpanel',body,'application/x-www-form-urlencoded').get('cpanelresult',{})
 if result.get('event',{}).get('result')!=1:raise RuntimeError('maintenance_timer_failed')
 rows=result.get('data')or[]
 if any(row.get('status')in [0,'0']for row in rows):raise RuntimeError('maintenance_timer_failed')
 return rows
def cleanup_job(backend,command):
 for row in call_cron(backend,'listcron'):
  if row.get('command')==command:call_cron(backend,'remove_line',line=int(row['count']))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--job',required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();file=Path(args.job)
 if file.is_symlink()or file.resolve().parent!=PRIVATE.resolve():raise RuntimeError('private_job_path_required')
 payload=file.read_bytes();job=json.loads(payload);nonce=job.get('nonce');command=build_command(nonce)
 if len(payload)>(100000 if job.get('action')in ['install-sale-documents','activate-payments','update-sale-documents']else 10000)or job.get('action')not in ['recover-password','configure-stripe','inspect-stripe','install-sale-documents','activate-payments','update-sale-documents']or not int(time.time())<job.get('expiresAt',0)<=int(time.time())+1800:raise RuntimeError('private_job_invalid')
 if not args.apply:print(json.dumps({'prepared':True,'action':job['action'],'privateOnly':True}));return
 d=deployment_module();backend=d.CpanelBackend(allow_writes=True);remote=d.HOME+'/nodeno-maintenance';d.ensure_directory(backend,remote,private=True,permissions='0700')
 script=(R/'scripts/private-maintenance.php').read_bytes();seed='job-'+nonce+'.json';receipt='receipt-'+nonce+'.json'
 entries=d.listing(backend,remote)
 if receipt in entries:raise RuntimeError('job_already_used')
 backend.upload(remote,{'private-maintenance.php':script,seed:payload})
 if d.text_content(backend,remote,'private-maintenance.php')!=script or d.text_content(backend,remote,seed)!=payload:raise RuntimeError('maintenance_upload_mismatch')
 before=[hashlib.sha256(row['command'].encode()).hexdigest()for row in call_cron(backend,'listcron')if 'command'in row]
 try:
  call_cron(backend,'add_line',command=command,minute='*',hour='*',day='*',month='*',weekday='*');print(json.dumps({'started':True,'action':job['action'],'privateOnly':True}),flush=True)
  end=time.time()+150
  while time.time()<end:
   if receipt in d.listing(backend,remote):
    result=json.loads(d.text_content(backend,remote,receipt));out=R/'artifacts/stripe-checkout-20261110'/('maintenance-'+job['action']+'.json');out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result),flush=True)
    if result.get('status')=='failed':raise RuntimeError('private_job_failed')
    return
   time.sleep(3)
  raise RuntimeError('private_job_timeout')
 finally:
  cleanup_job(backend,command)
  after=[hashlib.sha256(row['command'].encode()).hexdigest()for row in call_cron(backend,'listcron')if 'command'in row]
  if sorted(before)!=sorted(after):raise RuntimeError('unrelated_timer_changed')
  # Remove only this operation's remaining seed, after the timer has been removed.
  if seed in d.listing(backend,remote):backend.api2('fileop',op='trash',sourcefiles=remote+'/'+seed,doubledecode='0')
  print(json.dumps({'maintenanceTimerRemoved':True,'otherJobsPreserved':True}),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as error:print(json.dumps({'status':'stopped','code':str(error)if re.fullmatch('[a-z_]+',str(error))else'maintenance_failed'}));raise SystemExit(1)
