#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/setup-php-cron.py
# Açıklama   : Yalnız sahipliği doğrulanan PHP test işçisinin tek cron kaydını ekler ve okur.
import base64,importlib.util,json,re,ssl,sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parent.parent
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('test_publish',ROOT/'scripts/publish-php-test.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def cron(function,parameters=None):
    if function not in ['listcron','add_line']:raise ValueError('CRON_OPERATION_DENIED')
    values=p.values;user=values['CPANEL_USERNAME'];token=values.get('CPANEL_API_TOKEN');auth='cpanel '+user+':'+token if token else 'Basic '+base64.b64encode((user+':'+values['CPANEL_PASSWORD']).encode()).decode()
    data={'cpanel_jsonapi_user':user,'cpanel_jsonapi_apiversion':'2','cpanel_jsonapi_module':'Cron','cpanel_jsonapi_func':function,**(parameters or {})}
    with urlopen(Request('https://'+values['CPANEL_HOST']+':2083/json-api/cpanel',data=urlencode(data).encode(),headers={'Authorization':auth}),context=ssl.create_default_context(),timeout=30) as response:result=json.load(response)['cpanelresult']
    if result.get('event',{}).get('result')!=1:raise ValueError('CRON_API_FAILED')
    return result.get('data',[])
def run():
    deployment=json.loads((ROOT/'.local/php-stage-deployment.json').read_text('utf8'))
    if not deployment.get('installed') or not deployment.get('mainUnchanged'):raise ValueError('VERIFIED_TEST_RELEASE_REQUIRED')
    info=deployment['installation'];php=info['phpCli'];path=info['cronPath'];account=p.values['CPANEL_USERNAME']
    if php not in ['/opt/alt/php83/usr/bin/php','/opt/cpanel/ea-php83/root/usr/bin/php','/usr/local/bin/php'] or path!='/home/'+account+'/public_html/test/app/cron.php':raise ValueError('CRON_PATH_NOT_VERIFIED')
    ftp=p.publisher.connect(p.publisher.env_values())
    try:
        owner=json.loads(p.read(ftp,'/test/app/owner.json'));state=json.loads(p.STATE.read_text('utf8'))
        if owner['owner']!=state['owner']:raise ValueError('TEST_OWNER_MISMATCH')
        if '--check' in sys.argv:
            health=json.loads(p.read(ftp,'/test/app/worker-health.json'));p.persist(ROOT/'.local/php-worker-remote.json',health)
            if not health.get('ok') or not health['runtime'].startswith('8.3.'):raise ValueError('REMOTE_CRON_HEALTH_FAILED')
            print(json.dumps(health));return
        command=php+' -d display_errors=0 '+path+' >/dev/null 2>&1'
        existing=cron('listcron');matches=[row for row in existing if row.get('command')==command]
        if len(matches)>1:raise ValueError('DUPLICATE_CRON_DETECTED')
        if not matches:
            result=cron('add_line',{'minute':'*','hour':'*','day':'*','month':'*','weekday':'*','command':command})
            if not result or result[0].get('status')!=1:raise ValueError('CRON_INSTALL_FAILED')
        after=cron('listcron');matches=[row for row in after if row.get('command')==command]
        if len(matches)!=1:raise ValueError('CRON_READBACK_FAILED')
        if sorted(row.get('command','') for row in existing if row.get('command')!=command)!=sorted(row.get('command','') for row in after if row.get('command')!=command):raise ValueError('OTHER_CRON_CHANGED')
        p.persist(ROOT/'.local/php-cron.json',{'installed':True,'frequency':'each minute','linekey':matches[0].get('linekey'),'command':command,'otherJobsUnchanged':True});print('PHP test cron installed; other scheduled jobs unchanged. Awaiting actual worker heartbeat.')
    finally:ftp.close()
if __name__=='__main__':
    try:run()
    except Exception as e:
        print(json.dumps({'success':False,'code':str(e) if isinstance(e,ValueError) else type(e).__name__}));raise SystemExit(1)
