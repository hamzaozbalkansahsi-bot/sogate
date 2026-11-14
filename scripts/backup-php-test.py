#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/backup-php-test.py
# Açıklama   : Özel test DB yedeğini şifreli indirir ve yeni yerel DB'de geri yükleyerek doğrular.
import hashlib,importlib.util,json,os,secrets,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('php_publish',ROOT/'scripts/publish-php-test.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
def run():
    deployment=json.loads((ROOT/'.local/php-stage-deployment.json').read_text('utf8'));state=json.loads(p.STATE.read_text('utf8'))
    if not deployment.get('installed'):raise ValueError('VERIFIED_TEST_REQUIRED')
    ftp=p.publisher.connect(p.publisher.env_values());before=p.fingerprint(ftp);token=secrets.token_hex(32);identifier=secrets.token_hex(12);helper='/test/__backup_'+identifier+'.php';key=p.publisher.env_values()['BACKUP_ENCRYPTION_KEY'];report={'scope':'only private PHP test database','restored':False}
    try:
        if json.loads(p.read(ftp,'/test/app/owner.json'))['owner']!=state['owner']:raise ValueError('OWNER_MISMATCH')
        p.store(ftp,'/test/app/backup-request.json',json.dumps({'id':identifier,'key':key,'token_hash':hashlib.sha256(token.encode()).hexdigest(),'expires':int(time.time())+600}).encode());p.store(ftp,helper,(ROOT/'hosting/php/deploy/backup.php').read_bytes())
        status,body,_=p.get(helper,{'X-Backup-Token':token},b'{}');response=json.loads(body)
        if status!=200 or not response.get('created'):raise ValueError('ENCRYPTED_BACKUP_FAILED')
        encrypted=p.read(ftp,'/test/app/backups/'+identifier+'.aesgcm')
        if hashlib.sha256(encrypted).hexdigest()!=response['sha256'] or not encrypted.startswith(b'SGPHPB1'):raise ValueError('BACKUP_DOWNLOAD_HASH_INVALID')
        directory=ROOT/'.local/php-stage-backups';directory.mkdir(exist_ok=True);archive=directory/(identifier+'.db.aesgcm');archive.write_bytes(encrypted)
        env=os.environ.copy();env['SEXOGATE_BACKUP_KEY']=key;env['SEXOGATE_BACKUP_FILE']=str(archive)
        for line in (ROOT/'.local/mysql/mysql.env').read_text('utf8').splitlines():
            if line.startswith('MYSQL_TEST_ADMIN_URL='):
                value=line.split('=',1)[1];env['MYSQL_TEST_ADMIN_URL']=json.loads(value) if value.startswith('"') else value
        result=subprocess.run([str(ROOT/'.local/php-runtime/php.exe'),'bin/verify-restore.php'],cwd=ROOT/'hosting/php',env=env,capture_output=True)
        if result.returncode:raise ValueError('LOCAL_RESTORE_FAILED')
        verified=json.loads(result.stdout);report.update({'download':response,'restore':verified,'restored':True});print(json.dumps({'encryptedBackup':True,'localRestore':verified}))
    finally:
        try:
            rootfiles={e['name'] for e in p.publisher.entries(ftp,'/test')}
            if helper.rsplit('/',1)[1] in rootfiles:ftp.delete(helper)
            if any(e['name']=='backup-request.json' for e in p.publisher.entries(ftp,'/test/app')):ftp.delete('/test/app/backup-request.json')
            report['mainUnchanged']=p.fingerprint(ftp)==before;report['helperRemoved']=helper.rsplit('/',1)[1] not in {e['name'] for e in p.publisher.entries(ftp,'/test')}
        finally:ftp.close();p.persist(ROOT/'.local/php-backup-restore.json',report)
if __name__=='__main__':
    try:run()
    except Exception as e:
        print(json.dumps({'backupVerified':False,'error':str(e) if isinstance(e,ValueError) else type(e).__name__}));raise SystemExit(1)
