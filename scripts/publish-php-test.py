#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/publish-php-test.py
# Açıklama   : Yalnız sexogate.com/test PHP yayını; kök koruması ve ayrı DB sahiplik denetimi.
import argparse,base64,hashlib,importlib.util,io,json,os,re,secrets,ssl,sys,tempfile,time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request,HTTPSHandler,build_opener,urlopen

ROOT=Path(__file__).resolve().parent.parent
sys.dont_write_bytecode=True
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
publisher=module('sexogate_ftps','scripts/publish-coming-soon.py')
panel=module('sexogate_panel','scripts/cpanel-test-preflight.py')
values=panel.configuration()
STATE=ROOT/'.local/php-stage-state.json';CONFIG=ROOT/'.local/php-stage-config.json';ACCESS=ROOT/'.local/php-stage-access.json'
DENY=b'Options -Indexes\nRequire all denied\n'

def persist(file,data):
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf8',dir=file.parent,prefix='.'+file.name+'.',delete=False) as stream:
            temporary=Path(stream.name);stream.write(json.dumps(data,ensure_ascii=False,indent=2));stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,file)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
def api(function,params=None,module='Mysql'):
    allowed={'Mysql':{'list_databases','list_users','create_database','create_user','set_privileges_on_database','get_privileges_on_database'},'DomainInfo':{'list_domains'}}
    if function not in allowed.get(module,set()):raise ValueError('CPANEL_OPERATION_NOT_ALLOWED')
    host=values['CPANEL_HOST'];user=values['CPANEL_USERNAME']
    if not re.fullmatch(r'[A-Za-z0-9.-]+',host) or not re.fullmatch(r'[A-Za-z0-9_]+',user):raise ValueError('PANEL_CONFIG_INVALID')
    token=values.get('CPANEL_API_TOKEN');authorization='cpanel '+user+':'+token if token else 'Basic '+base64.b64encode((user+':'+values['CPANEL_PASSWORD']).encode()).decode()
    request=Request('https://'+host+':2083/execute/'+module+'/'+function,data=urlencode(params or {}).encode(),headers={'Authorization':authorization,'Content-Type':'application/x-www-form-urlencoded'})
    with urlopen(request,context=ssl.create_default_context(),timeout=40) as response:raw=json.load(response)
    result=raw.get('result',raw)
    if result.get('status')!=1:raise ValueError('CPANEL_'+function.upper()+'_FAILED')
    return result.get('data')
def names(data,key):
    return {row[key] if isinstance(row,dict) else row for row in (data or [])}
def get(path,headers=None,data=None):
    if not path.startswith('/test/') and path!='/test':raise ValueError('HTTP_SCOPE_INVALID')
    opener=build_opener(HTTPSHandler(context=ssl.create_default_context()),publisher.SameOriginRedirect())
    try:
        with opener.open(Request('https://sexogate.com'+path,headers=headers or {},data=data),timeout=180) as r:return r.status,r.read(1000000),dict(r.headers)
    except HTTPError as e:return e.code,e.read(1000000),dict(e.headers)
def read(ftp,path):
    b=io.BytesIO();ftp.retrbinary('RETR '+path,b.write);return b.getvalue()
def store(ftp,path,data):
    if not path.startswith('/test/') or '..' in path.split('/'):raise ValueError('FTP_SCOPE_INVALID')
    ftp.storbinary('STOR '+path,io.BytesIO(data))

def store_atomic(ftp,path,data):
    if not path.startswith('/test/') or '..' in path.split('/'):raise ValueError('FTP_SCOPE_INVALID')
    temporary=path+'.upload-'+secrets.token_hex(12)
    try:
        store(ftp,temporary,data)
        if read(ftp,temporary)!=data:raise ValueError('FTP_UPLOAD_READBACK_FAILED')
        ftp.rename(temporary,path)
    finally:
        from ftplib import error_perm
        try:ftp.delete(temporary)
        except error_perm:pass
def fingerprint(ftp):
    files=['index.html','.htaccess','robots.txt']+[e['name'] for e in publisher.entries(ftp) if e['type']=='file' and re.fullmatch(r'google[a-f0-9]+\.html',e['name'])]
    return {file:hashlib.sha256(read(ftp,'/'+file)).hexdigest() for file in files}
def ensure_dir(ftp,path):
    if not path.startswith('/test/'):raise ValueError('DIRECTORY_SCOPE_INVALID')
    parent,name=path.rsplit('/',1)
    found=next((e for e in publisher.entries(ftp,parent) if e['name']==name),None)
    if found and found['type']!='dir':raise ValueError('DIRECTORY_CONFLICT')
    if not found:ftp.mkd(path)

def validate_archive(package,package_root):
    release=package.get('release','');archive=Path(package['archive']).resolve()
    if not re.fullmatch('[a-f0-9]{24}',release) or archive!=(package_root.resolve()/(release+'.zip')) or not archive.is_file() or archive.stat().st_size>20000000 or hashlib.sha256(archive.read_bytes()).hexdigest()!=package['sha256']:
        raise ValueError('LOCAL_PACKAGE_INVALID')
    return archive

def run(package_root=None):
    if not panel.domain_owned(api('list_domains',module='DomainInfo')):raise ValueError('DOMAIN_ACCOUNT_MISMATCH')
    databases=names(api('list_databases'),'database');users=names(api('list_users'),'user')
    prefix=values['CPANEL_USERNAME'];db=prefix+'_sogate_test';user=prefix+'_sgtest'
    if '--inspect' in sys.argv:
        print(json.dumps({'domainVerified':True,'targetDatabaseExists':db in databases,'targetUserExists':user in users,'ownershipStateExists':STATE.exists()}));return
    if '--verify' in sys.argv:
        state=json.loads(STATE.read_text('utf8'));report=json.loads((ROOT/'.local/php-stage-deployment.json').read_text('utf8'));access=json.loads(ACCESS.read_text('utf8'));auth='Basic '+base64.b64encode((access['stageUser']+':'+access['stagePassword']).encode()).decode();ftp=publisher.connect(publisher.env_values())
        try:
            if json.loads(read(ftp,'/test/app/owner.json')).get('owner')!=state['owner']:raise ValueError('TEST_OWNER_MISMATCH')
            if read(ftp,'/test/app/active.php').decode()!="<?php return '"+report['release']+"';":raise ValueError('ACTIVE_RELEASE_MISMATCH')
            status,body,_=get('/test/api/health',{'Authorization':auth});health=json.loads(body)
            if status!=200 or health.get('runtime')!='php' or not health.get('database') or health.get('salesEnabled') is not False:raise ValueError('REMOTE_HEALTH_FAILED')
            for path,code in report['privatePaths'].items():
                actual=get(path,{'Authorization':auth})[0]
                if '/app/' in path and actual!=403:raise ValueError('PRIVATE_PATH_EXPOSED')
                if '__install_' in path and (actual!=404 or path.rsplit('/',1)[1] in {e['name'] for e in publisher.entries(ftp,'/test')}):raise ValueError('INSTALLER_NOT_REMOVED')
            report['mainAfter']=fingerprint(ftp);report['mainUnchanged']=report['mainBefore']==report['mainAfter']
            if not report['mainUnchanged']:raise ValueError('MAIN_SITE_CHANGED')
            report['installed']=True;report['installerRemovedVerified']=True;state['release']=report['release'];persist(STATE,state);persist(ROOT/'.local/php-stage-deployment.json',report);print('PHP test release verified; private files blocked, installer removed, main site unchanged.')
        finally:ftp.close()
        return
    if '--deploy' not in sys.argv:raise ValueError('EXPLICIT_TEST_DEPLOY_REQUIRED')
    for proof in ['php-browser-local.json','php-install-local.json']:
        if not (ROOT/'.local'/proof).is_file():raise ValueError('LOCAL_ACCEPTANCE_REQUIRED')
    package=json.loads((ROOT/'.local/php-package.json').read_text('utf8'));archive=validate_archive(package,package_root or ROOT/'.local/php-packages')
    if STATE.exists():
        state=json.loads(STATE.read_text('utf8'))
        if state['database']!=db or state['dbUser']!=user:raise ValueError('STATE_TARGET_MISMATCH')
    else:
        if db in databases or user in users:raise ValueError('UNOWNED_DATABASE_OR_USER')
        state={'owner':secrets.token_hex(32),'database':db,'dbUser':user,'dbCreated':False,'userCreated':False,'testCreated':False};persist(STATE,state)
    if not CONFIG.exists():
        access={'stageUser':'sexogate-test','stagePassword':secrets.token_urlsafe(24),'email':'info@sexogate.com','password':secrets.token_urlsafe(24)}
        config={'env':'test','secret':secrets.token_hex(32),'payment_provider':'test','live_sales':False,'base_path':'/test','app_url':'https://sexogate.com/test','db_dsn':'mysql:host=localhost;dbname='+db+';charset=utf8mb4','db_user':user,'db_password':secrets.token_urlsafe(36),'stage_access':True,'stage_user':access['stageUser'],'stage_password_sha256':hashlib.sha256(access['stagePassword'].encode()).hexdigest(),'bootstrap_admin':{'name':'Hamza ÖZBALKAN','email':access['email'],'password':access['password']}}
        persist(CONFIG,config);persist(ACCESS,access)
    config=json.loads(CONFIG.read_text('utf8'))
    if db not in databases:
        api('create_database',{'name':db});state['dbCreated']=True;persist(STATE,state)
    elif not state['dbCreated']:raise ValueError('DATABASE_OWNERSHIP_NOT_CONFIRMED')
    if user not in users:
        api('create_user',{'name':user,'password':config['db_password']});state['userCreated']=True;persist(STATE,state)
    elif not state['userCreated']:raise ValueError('USER_OWNERSHIP_NOT_CONFIRMED')
    api('set_privileges_on_database',{'user':user,'database':db,'privileges':'ALL PRIVILEGES'})
    ftp=publisher.connect(publisher.env_values());before=fingerprint(ftp);report={'scope':'https://sexogate.com/test','release':package['release'],'mainBefore':before,'installed':False}
    installer='/test/__install_'+secrets.token_hex(16)+'.php';token=secrets.token_hex(32)
    try:
        entry=next((e for e in publisher.entries(ftp) if e['name']=='test'),None)
        if entry and entry['type']!='dir':raise ValueError('TEST_PATH_CONFLICT')
        if not entry:ftp.mkd('/test');state['testCreated']=True;persist(STATE,state)
        existing=publisher.entries(ftp,'/test')
        if existing:
            if not state['testCreated']:raise ValueError('TEST_DIRECTORY_NOT_OWNED')
            app=next((e for e in existing if e['name']=='app'),None)
            if app:
                owner=json.loads(read(ftp,'/test/app/owner.json'))
                if owner.get('owner')!=state['owner']:raise ValueError('TEST_OWNER_MISMATCH')
        ensure_dir(ftp,'/test/app');store(ftp,'/test/app/.htaccess',DENY);store(ftp,'/test/app/owner.json',json.dumps({'owner':state['owner'],'application':'sexogate-php-test'}).encode())
        status,_,_=get('/test/app/owner.json');
        if status!=403:raise ValueError('PRIVATE_DIRECTORY_NOT_BLOCKED')
        # Only this application's private configuration is backed up, encrypted with the existing local key.
        appEntries={e['name'] for e in publisher.entries(ftp,'/test/app')}
        if 'config.local.json' in appEntries:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            key=bytes.fromhex(publisher.env_values()['BACKUP_ENCRYPTION_KEY']);nonce=secrets.token_bytes(12);raw=read(ftp,'/test/app/config.local.json');encrypted=nonce+AESGCM(key).encrypt(nonce,raw,b'sexogate-test-config-v1');backup=ROOT/'.local/php-stage-backups';backup.mkdir(exist_ok=True);(backup/(str(time.time_ns())+'.config.aesgcm')).write_bytes(encrypted)
            if AESGCM(key).decrypt(encrypted[:12],encrypted[12:],b'sexogate-test-config-v1')!=raw:raise ValueError('BACKUP_READBACK_FAILED')
            # Preserve the server's one-time bootstrap removal and runtime settings.
            serverConfig=json.loads(raw);serverConfig['asset_prefix']=config.get('asset_prefix','/test/assets');config=serverConfig
        if 'config.local.json' not in appEntries:
            store_atomic(ftp,'/test/app/config.local.json',json.dumps(config,ensure_ascii=False).encode())
        deploy={'release':package['release'],'sha256':package['sha256'],'token_hash':hashlib.sha256(token.encode()).hexdigest(),'expires':int(time.time())+900}
        store(ftp,'/test/app/deploy.json',json.dumps(deploy).encode());store(ftp,'/test/app/payload-'+package['release']+'.zip',archive.read_bytes());store(ftp,installer,(ROOT/'hosting/php/deploy/install.php').read_bytes())
        status,body,_=get(installer,{'X-Deploy-Token':token,'Content-Type':'application/json'},b'{}');result=json.loads(body)
        report['installerStatus']=status;report['installation']=result
        if status!=200 or not result.get('installed'):raise ValueError('REMOTE_INSTALL_FAILED_'+result.get('code','UNKNOWN'))
        store_atomic(ftp,'/test/app/cron.php',(ROOT/'hosting/php/deploy/cron.php').read_bytes());store_atomic(ftp,'/test/index.php',(ROOT/'hosting/php/deploy/index.php').read_bytes());store_atomic(ftp,'/test/.htaccess',(ROOT/'hosting/php/public/.htaccess').read_bytes());ftp.delete(installer)
        access=json.loads(ACCESS.read_text('utf8'));auth='Basic '+base64.b64encode((access['stageUser']+':'+access['stagePassword']).encode()).decode()
        status,body,headers=get('/test/api/health',{'Authorization':auth});health=json.loads(body)
        if status!=200 or health.get('runtime')!='php' or not health.get('database') or health.get('salesEnabled') is not False:raise ValueError('REMOTE_HEALTH_FAILED')
        report['health']=health;report['privatePaths']={path:get(path,{'Authorization':auth})[0] for path in ['/test/app/config.local.json','/test/app/releases/'+package['release']+'/vendor/autoload.php',installer]}
        if any(code not in [403,404] for code in report['privatePaths'].values()):raise ValueError('PRIVATE_PATH_EXPOSED')
        report['installed']=True;state['release']=package['release'];persist(STATE,state);print('Private PHP test application installed and health checked.')
    finally:
        try:
            if any(e['name']==installer.rsplit('/',1)[1] for e in publisher.entries(ftp,'/test')):ftp.delete(installer)
            report['mainAfter']=fingerprint(ftp);report['mainUnchanged']=report['mainAfter']==before
        finally:ftp.close();persist(ROOT/'.local/php-stage-deployment.json',report)
    if not report.get('mainUnchanged'):raise ValueError('MAIN_SITE_CHANGED')

if __name__=='__main__':
    try:
        parser=argparse.ArgumentParser(description='Yalnız özel PHP /test uygulamasını inceler veya yayımlar.')
        action=parser.add_mutually_exclusive_group(required=True)
        for name in ['inspect','deploy','verify']:action.add_argument('--'+name,action='store_true')
        parser.add_argument('--package-root',type=Path)
        args=parser.parse_args();run(args.package_root)
    except Exception as e:
        # Do not print provider responses, request headers, connection strings or passwords.
        code=str(e) if isinstance(e,ValueError) and re.fullmatch('[A-Z_0-9]+',str(e)) else type(e).__name__
        print(json.dumps({'deployed':False,'code':code}));raise SystemExit(1)
