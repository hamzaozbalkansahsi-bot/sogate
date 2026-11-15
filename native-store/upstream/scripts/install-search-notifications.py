"""Install and verify one persistent private search/blog cron; preserve all unrelated jobs."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,time
R=Path(__file__).resolve().parents[1];E=R/'artifacts/search-automation-20261112'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def signature(rows,command):return sorted(hashlib.sha256(json.dumps({k:v for k,v in row.items()if k not in ['count','line']},sort_keys=True).encode()).hexdigest()for row in rows if row.get('command')and row['command']!=command)
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--check',action='store_true');args=p.parse_args();d=load('search_cron_backend','scripts/deploy-cpanel.py');cron=load('search_cron_api','scripts/run-private-maintenance.py');readback=load('search_cron_readback','scripts/publish-paint-release.py');proof=json.loads((E/'deployment.json').read_bytes());b=d.CpanelBackend(allow_writes=args.apply or args.check);assert proof['passed']and b.public_health()['releaseHash']==proof['releaseHash'],'current_release_changed'
 folder=d.HOME+'/nodeno-search';command='/usr/local/bin/php -d display_errors=0 -d log_errors=0 -d zend.exception_ignore_args=1 '+folder+'/search-notifications-runner.php > /dev/null 2>&1';before=cron.call_cron(b,'listcron');oldSignature=signature(before,command);matches=[x for x in before if x.get('command')==command];assert len(matches)<=1
 if args.check:
  heartbeat=json.loads(d.text_content(b,folder,'heartbeat.json'));assert matches and str(matches[0]['minute'])=='*';assert heartbeat.get('status')=='ok'and heartbeat.get('releaseHash')==proof['releaseHash']and heartbeat['checkedAt']>time.time()-180,heartbeat;assert heartbeat.get('blog',{}).get('status')in ['ok','paused'];(E/'heartbeat-live.json').write_text(json.dumps(heartbeat,indent=2)+'\n');print(json.dumps(heartbeat));return
 if not args.apply:print(json.dumps({'ready':True,'everyMinutes':1,'scanEveryMinutes':5,'blogDailySlots':['09:30','18:30'],'timezone':'Europe/Istanbul','existingTimer':bool(matches)}));return
 key=json.loads((R/'data/seo-indexnow.json').read_bytes());configuration={'key':key['key'],'endpoint':'https://yandex.com/indexnow','baselineUrls':(R/'artifacts/indexnow-live-diagnosis-20261112/preflight/canonical-urls.txt').read_text().splitlines()};body=(json.dumps(configuration,separators=(',',':'))+'\n').encode();runner=(R/'scripts/search-notifications-runner.php').read_bytes()
 with d.deployment_lease(b):
  assert b.public_health()['releaseHash']==proof['releaseHash'];d.ensure_directory(b,folder,private=True,permissions='0700');b.upload(folder,{'configuration.json':body,'search-notifications-runner.php':runner});assert readback.verified_private_read(d,b,folder,'configuration.json',body)==body;assert d.text_content(b,folder,'search-notifications-runner.php')==runner
  if not matches:cron.call_cron(b,'add_line',command=command,minute='*',hour='*',day='*',month='*',weekday='*')
  after=cron.call_cron(b,'listcron');assert signature(after,command)==oldSignature;matches=[x for x in after if x.get('command')==command];assert len(matches)==1 and str(matches[0]['minute'])=='*'
 record={'installed':True,'releaseHash':proof['releaseHash'],'everyMinutes':1,'changeScanMinutes':5,'privateRunnerVerified':True,'originalKeyPreserved':True,'otherTimersPreserved':True,'dependsOnLocalComputer':False,'blogDailySlots':['09:30','18:30'],'timezone':'Europe/Istanbul','installedAt':int(time.time())};(E/'timer.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
