"""Install one permanent private Turhost cron, preserving every unrelated timer."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,time,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/blog-20261112'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def require(value,code):
 if not value:raise RuntimeError(code)
def cron_signature(rows,command):return sorted(hashlib.sha256(json.dumps({k:v for k,v in r.items()if k not in ['count','line']},sort_keys=True).encode()).hexdigest()for r in rows if r.get('command')and r['command']!=command)
def integrated_timer(rows,home):
 command='/usr/local/bin/php -d display_errors=0 -d log_errors=0 -d zend.exception_ignore_args=1 '+home+'/nodeno-search/search-notifications-runner.php > /dev/null 2>&1'
 matches=[r for r in rows if r.get('command')==command]
 require(len(matches)<=1,'duplicate_integrated_timers')
 if not matches:return None
 require(all(str(matches[0].get(k))=='*'for k in ['minute','hour','day','month','weekday']),'integrated_timer_schedule_changed')
 return matches[0]
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--check',action='store_true');args=p.parse_args();d=module('blog_timer_backend','scripts/deploy-cpanel.py');cron=module('blog_timer_cron','scripts/run-private-maintenance.py');b=d.CpanelBackend(allow_writes=True);proof=json.loads((E/'deployment.json').read_bytes());require(proof.get('passed')and b.public_health()['releaseHash']==proof['releaseHash'],'live_blog_release_changed')
 folder=d.HOME+'/nodeno-blog';command='/usr/local/bin/php -d display_errors=0 -d log_errors=0 -d zend.exception_ignore_args=1 '+folder+'/blog-runner.php > /dev/null 2>&1';script=(R/'scripts/blog-runner.php').read_bytes();before=cron.call_cron(b,'listcron');signature=cron_signature(before,command);matches=[r for r in before if r.get('command')==command];require(len(matches)<=1,'duplicate_blog_timers')
 integrated=integrated_timer(before,d.HOME)
 if integrated:
  require(not matches,'duplicate_blog_runners');runner=d.text_content(b,d.HOME+'/nodeno-search','search-notifications-runner.php');require(runner==(R/'scripts/search-notifications-runner.php').read_bytes()and b'nodenoBlogTick('in runner,'integrated_blog_runner_unverified')
  if args.check:
   heartbeat=json.loads(d.text_content(b,d.HOME+'/nodeno-search','heartbeat.json'));require(heartbeat.get('releaseHash')==proof['releaseHash']and heartbeat.get('checkedAt',0)>time.time()-180 and heartbeat.get('status')=='ok'and heartbeat.get('blog',{}).get('status')in['ok','paused'],'integrated_blog_heartbeat_not_fresh');(E/'heartbeat-live.json').write_text(json.dumps(heartbeat,indent=2)+'\n');print(json.dumps(heartbeat));return
  record={'installed':True,'reusedExistingIntegratedTimer':True,'server':'Turhost','everyMinutes':1,'timezone':'Europe/Istanbul','dailySlots':['09:30','18:30'],'dependsOnLocalComputer':False,'otherTimersPreserved':True,'privateRunnerVerified':True,'releaseHash':proof['releaseHash'],'paidRequests':0}
  if args.apply:(E/'timer.json').write_text(json.dumps(record,indent=2)+'\n')
  print(json.dumps(record));return
 if args.check:
  heartbeat=json.loads(d.text_content(b,folder,'heartbeat.json'));require(heartbeat.get('releaseHash')==proof['releaseHash']and int(heartbeat.get('checkedAt',0))>time.time()-660 and heartbeat.get('result',{}).get('status')in['ok','paused'],'blog_heartbeat_not_fresh');require(len(matches)==1 and str(matches[0].get('minute'))=='*/5','blog_timer_missing');(E/'heartbeat-live.json').write_text(json.dumps(heartbeat,indent=2)+'\n');print(json.dumps(heartbeat));return
 if not args.apply:print(json.dumps({'ready':True,'everyMinutes':5,'privateOnly':True,'dependsOnLocalComputer':False,'dailySlots':['09:30','18:30'],'timezone':'Europe/Istanbul','existingTimer':bool(matches)}));return
 with d.deployment_lease(b):
  require(b.public_health()['releaseHash']==proof['releaseHash'],'live_blog_release_changed');d.ensure_directory(b,folder,private=True,permissions='0700');b.upload(folder,{'blog-runner.php':script});require(d.text_content(b,folder,'blog-runner.php')==script,'private_runner_readback_failed')
  if not matches:cron.call_cron(b,'add_line',command=command,minute='*/5',hour='*',day='*',month='*',weekday='*')
  after=cron.call_cron(b,'listcron');require(cron_signature(after,command)==signature,'unrelated_timer_changed');matches=[r for r in after if r.get('command')==command];require(len(matches)==1 and str(matches[0].get('minute'))=='*/5','blog_timer_installation_failed')
 record={'installed':True,'server':'Turhost','everyMinutes':5,'timezone':'Europe/Istanbul','dailySlots':['09:30','18:30'],'dependsOnLocalComputer':False,'otherTimersPreserved':True,'privateRunnerVerified':True,'releaseHash':proof['releaseHash'],'installedAt':int(time.time()),'paidRequests':0};(E/'timer.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
