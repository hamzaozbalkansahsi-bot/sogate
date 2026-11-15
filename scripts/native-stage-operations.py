#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native-stage-operations.py
# Açıklama   : Yalnız kendi özel test işçisini zamanlar ve SQLite yedeğini şifreli indirip geri yükler.
import importlib.util,io,json,re,secrets,sqlite3,sys,time,zipfile,hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT=Path(__file__).resolve().parent.parent;sys.dont_write_bytecode=True
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('publisher','scripts/publish-php-test.py');cron_api=module('cron_api','scripts/setup-php-cron.py');deployment=json.loads((ROOT/'.local/native-stage-deployment.json').read_text('utf8'))
def setup_cron():
 info=deployment['installation'];php=info['phpCli'];path=info['privateRoot']+'/worker.php'
 if php not in ['/opt/alt/php83/usr/bin/php','/opt/cpanel/ea-php83/root/usr/bin/php','/usr/local/bin/php'] or path!='/home/'+p.values['CPANEL_USERNAME']+'/.sexogate-native-test/worker.php':raise ValueError('NATIVE_CRON_SCOPE_INVALID')
 command=php+' -d display_errors=0 '+path+' >/dev/null 2>&1';before=cron_api.cron('listcron');matching=[r for r in before if r.get('command')==command]
 if len(matching)>1:raise ValueError('NATIVE_CRON_DUPLICATE')
 if not matching:cron_api.cron('add_line',{'minute':'*','hour':'*','day':'*','month':'*','weekday':'*','command':command})
 after=cron_api.cron('listcron');matching=[r for r in after if r.get('command')==command]
 if len(matching)!=1 or sorted(r.get('command','') for r in before if r.get('command')!=command)!=sorted(r.get('command','') for r in after if r.get('command')!=command):raise ValueError('NATIVE_CRON_READBACK_FAILED')
 p.persist(ROOT/'.local/native-stage-cron.json',{'installed':True,'command':command,'linekey':matching[0].get('linekey'),'otherJobsUnchanged':True,'at':int(time.time())});print(json.dumps({'nativeCronInstalled':True,'otherJobsUnchanged':True}))
def maintenance(action):
 ftp=p.publisher.connect(p.publisher.env_values());before=p.fingerprint(ftp);token=secrets.token_hex(32);state=json.loads(p.STATE.read_text('utf8'));helper='/test/__native_maintenance_'+secrets.token_hex(12)+'.php';record='/test/app/native-maintenance-request.json'
 route_before=route_during=None
 try:
  if deployment.get('activated'):
   route_before=p.read(ftp,'/test/.htaccess')
   if route_before!=(ROOT/'native-store/deploy/.htaccess').read_bytes():raise ValueError('UNKNOWN_NATIVE_ROUTE_CONFIGURATION')
   rule=('RewriteRule ^'+re.escape(helper.rsplit('/',1)[1])+'$ - [END]\n').encode();needle=b'RewriteRule ^ index.php [END]'
   if route_before.count(needle)!=1:raise ValueError('NATIVE_ROUTE_MARKER_MISSING')
   route_during=route_before.replace(needle,rule+needle)
   # Aynı saniyedeki iki FTP değişikliği, hostingin htaccess mtime önbelleğinde kaybolabilir.
   time.sleep(1.1);p.store_atomic(ftp,'/test/.htaccess',route_during)
  p.store_atomic(ftp,record,json.dumps({'owner':state['owner'],'expires':int(time.time())+300,'tokenHash':hashlib.sha256(token.encode()).hexdigest()}).encode());p.store(ftp,helper,(ROOT/'native-store/deploy/maintenance.php').read_bytes())
  body={'action':'status'}
  if action=='backup':body={'action':'backup','id':secrets.token_hex(12),'key':p.publisher.env_values()['BACKUP_ENCRYPTION_KEY']}
  for attempt in range(12):
   status,raw,_=p.get(helper,{'X-Native-Maintenance':token,'Content-Type':'application/json'},json.dumps(body).encode())
   if status not in [404,405]:break
   time.sleep(1)
  response=json.loads(raw)
  if status!=200:raise ValueError('NATIVE_MAINTENANCE_'+response.get('code',response.get('error','FAILED')).upper())
  if action=='status':
   p.persist(ROOT/'.local/native-stage-worker.json',response);print(json.dumps(response));return
  if not response.get('created'):raise ValueError('NATIVE_BACKUP_FAILED')
  encrypted=p.read(ftp,'/test/app/native-backups/'+body['id']+'.aesgcm')
  if not encrypted.startswith(b'SGNATIVE1') or hashlib.sha256(encrypted).hexdigest()!=response['sha256']:raise ValueError('NATIVE_BACKUP_HASH_INVALID')
  plain=AESGCM(bytes.fromhex(body['key'])).decrypt(encrypted[9:21],encrypted[37:]+encrypted[21:37],b'sexogate-native-backup-v1');folder=Path('D:/sexogate-local-artifacts-20261114/private-installs')/('native-restored-'+secrets.token_hex(8));folder.mkdir();(folder/'archive.aesgcm').write_bytes(encrypted)
  with zipfile.ZipFile(io.BytesIO(plain))as archive:
   manifest=json.loads(archive.read('manifest.json'));tables=rows=0
   for name,sha in manifest['files'].items():
    if not re.fullmatch(r'[a-z0-9_-]+\.(sqlite|bin)',name):raise ValueError('NATIVE_BACKUP_PATH_INVALID')
    data=archive.read(name)
    if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('NATIVE_BACKUP_CONTENT_CHANGED')
    if name.endswith('.sqlite'):
     target=folder/name;target.write_bytes(data)
     with sqlite3.connect(target)as db:
      if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('NATIVE_RESTORE_INTEGRITY_FAILED')
      for table,count in manifest['databases'][name].items():
       actual=db.execute('SELECT COUNT(*) FROM "'+table.replace('"','""')+'"').fetchone()[0]
       if actual!=count:raise ValueError('NATIVE_RESTORE_ROW_COUNT_CHANGED')
       tables+=1;rows+=actual
  result={'restored':True,'encrypted':True,'databases':response['databases'],'tables':tables,'rows':rows,'foreignKeysValid':True,'sourceRelease':manifest['release'],'privateArchive':str(folder/'archive.aesgcm'),'sha256':response['sha256']};p.persist(ROOT/'.local/native-backup-restore.json',result);print(json.dumps({k:v for k,v in result.items()if k!='privateArchive'}))
 finally:
  try:
   if helper.rsplit('/',1)[1]in {e['name']for e in p.publisher.entries(ftp,'/test')}:ftp.delete(helper)
   if record.rsplit('/',1)[1]in {e['name']for e in p.publisher.entries(ftp,'/test/app')}:ftp.delete(record)
   if route_during is not None:
    if p.read(ftp,'/test/.htaccess')!=route_during:raise ValueError('OTHER_NATIVE_ROUTE_CHANGED')
    p.store_atomic(ftp,'/test/.htaccess',route_before)
   if p.fingerprint(ftp)!=before:raise ValueError('MAIN_CHANGED_DURING_OPERATIONS')
  finally:ftp.close()
if __name__=='__main__':
 try:setup_cron()if sys.argv[1]=='cron'else maintenance(sys.argv[1])
 except Exception as error:
  code=str(error)if isinstance(error,ValueError)and re.fullmatch('[A-Z_0-9]+',str(error))else type(error).__name__;print(json.dumps({'ok':False,'code':code}));raise SystemExit(1)
