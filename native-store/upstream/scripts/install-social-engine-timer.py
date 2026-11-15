"""Install the user's server-side one-minute social worker without changing other timers."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,time
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-engine-20261112'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();d=load('social_timer_backend','scripts/deploy-cpanel.py');maintenance=load('social_timer_helpers','scripts/run-private-maintenance.py');b=d.CpanelBackend(allow_writes=args.apply);proof=json.loads((E/'deployment.json').read_bytes());assert proof['passed']and b.public_health()['releaseHash']==proof['releaseHash']
 folder=d.HOME+'/nodeno-social';command='/usr/local/bin/php -d display_errors=0 -d log_errors=0 -d zend.exception_ignore_args=1 '+folder+'/social-engine-runner.php > /dev/null 2>&1';script=(R/'scripts/social-engine-runner.php').read_bytes()
 if not args.apply:print(json.dumps({'ready':True,'everyMinutes':1,'privateOnly':True,'dependsOnLocalComputer':False}));return
 d.ensure_directory(b,folder,private=True,permissions='0700');b.upload(folder,{'social-engine-runner.php':script});assert d.text_content(b,folder,'social-engine-runner.php')==script
 before=maintenance.call_cron(b,'listcron');others=sorted(hashlib.sha256(r['command'].encode()).hexdigest()for r in before if 'command'in r and r['command']!=command)
 matching=[r for r in before if r.get('command')==command]
 if not matching:maintenance.call_cron(b,'add_line',command=command,minute='*',hour='*',day='*',month='*',weekday='*')
 elif len(matching)!=1:raise RuntimeError('duplicate_social_worker_timers')
 after=maintenance.call_cron(b,'listcron');assert sorted(hashlib.sha256(r['command'].encode()).hexdigest()for r in after if 'command'in r and r['command']!=command)==others
 rows=[r for r in after if r.get('command')==command];assert len(rows)==1 and str(rows[0].get('minute'))=='*'
 record={'installed':True,'server':'Turhost','everyMinutes':1,'privateRunnerVerified':True,'otherTimersPreserved':True,'dependsOnLocalComputer':False,'paidProductionEnabled':False,'releaseHash':proof['releaseHash'],'installedAt':int(time.time())};(E/'timer.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
