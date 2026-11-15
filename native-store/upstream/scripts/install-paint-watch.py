"""Install the authorized price watcher without changing existing Turhost jobs."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,time
R=Path(__file__).resolve().parents[1];E=R/'artifacts/bianca-20261112'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args();d=load('paint_timer_backend','scripts/deploy-cpanel.py');maintenance=load('paint_timer_helper','scripts/run-private-maintenance.py');b=d.CpanelBackend(allow_writes=args.apply);proof=json.loads((E/'deployment.json').read_bytes());assert proof['passed']and b.public_health()['releaseHash']==proof['releaseHash']
 folder=d.HOME+'/nodeno-price-watch';name='paint-price-watch-runner.php';body=(R/'scripts'/name).read_bytes();command='/usr/local/bin/php -d display_errors=0 -d log_errors=0 -d zend.exception_ignore_args=1 '+folder+'/'+name+' > /dev/null 2>&1'
 if not args.apply:print(json.dumps({'ready':True,'everyMinutes':5,'productCheckHours':24,'requiresLocalComputer':False}));return
 d.ensure_directory(b,folder,private=True,permissions='0700');b.upload(folder,{name:body});assert d.text_content(b,folder,name)==body
 before=maintenance.call_cron(b,'listcron');other=sorted(hashlib.sha256(r['command'].encode()).hexdigest()for r in before if r.get('command')and r['command']!=command);rows=[r for r in before if r.get('command')==command]
 if not rows:maintenance.call_cron(b,'add_line',command=command,minute='*/5',hour='*',day='*',month='*',weekday='*')
 else:assert len(rows)==1
 after=maintenance.call_cron(b,'listcron');assert sorted(hashlib.sha256(r['command'].encode()).hexdigest()for r in after if r.get('command')and r['command']!=command)==other;rows=[r for r in after if r.get('command')==command];assert len(rows)==1 and rows[0]['minute']=='*/5'
 record={'installed':True,'releaseHash':proof['releaseHash'],'server':'Turhost','everyMinutes':5,'productCheckHours':24,'otherJobsPreserved':True,'requiresLocalComputer':False,'at':int(time.time())};(E/'timer.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
if __name__=='__main__':main()
