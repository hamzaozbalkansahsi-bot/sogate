#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/publish-native-test.py
# Açıklama   : Doğrulanmış PHP kopyasını önce özel önizlemeye, sonra yalnız test alt yoluna atomik geçirir.
import argparse,hashlib,importlib.util,io,json,re,secrets,subprocess,sys,time,zipfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT=Path(__file__).resolve().parent.parent;sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('legacy_publish',ROOT/'scripts/publish-php-test.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
REPORT=ROOT/'.local/native-stage-deployment.json';DENY=b'Options -Indexes\nRequire all denied\n'

def adult_proof(scope,release,base):
 path=ROOT/('.local/native-adult-'+scope+'.json')
 if not path.is_file():raise ValueError('ADULT_STORE_ACCEPTANCE_REQUIRED')
 rows=json.loads(path.read_text('utf8'))
 if len(rows)!=2 or {row['engine']for row in rows}!={'chromium','webkit'} or any(row.get('base')!=base or row.get('release')!=release or row.get('worldMap')is not False or row.get('furnitureCopy')is not False or not row.get('guestBrowsing')or not row.get('ageGate')or row.get('pageErrors')for row in rows):raise ValueError('ADULT_STORE_ACCEPTANCE_FAILED')

def storefront_proof(scope,release,base):
 path=ROOT/('.local/native-'+scope+'.json')
 if not path.is_file():raise ValueError('STOREFRONT_VISUAL_ACCEPTANCE_REQUIRED')
 rows=json.loads(path.read_text('utf8'))
 required=['realImagesLoaded','alignedCards','footerPrivacyEntry','readableFeatures','horizontalRelatedRail','horizontalRecentRail','consentRevocation','accountHelperMountedOnce','productImageBounds']
 if len(rows)!=2 or {row.get('engine')for row in rows}!={'chromium','webkit'} or any(row.get('base')!=base or row.get('release')!=release or row.get('furnitureCopy')is not False or row.get('stickyOverlap')is not False or row.get('underlinedLinks')is not False or row.get('compactImageCampaignCards')!=4 or row.get('curtainDurationSeconds',0)<4.8 or row.get('pageErrors')or not all(row.get(key)is True for key in required)for row in rows):raise ValueError('STOREFRONT_VISUAL_ACCEPTANCE_FAILED')
def entry(home,release,mount):
 if not re.fullmatch(r'/home/[A-Za-z0-9_]+/\.sexogate-native-test',home) or not re.fullmatch('[a-f0-9]{24}',release) or not re.fullmatch('/test(?:/native-preview-[a-f0-9]{16})?',mount):raise ValueError('NATIVE_ENTRY_SCOPE_INVALID')
 quote=lambda value:"'"+value.replace("'","\\'")+"'"
 return ("<?php\n/** SEXOGATE — özel PHP test uygulaması; kaynak: native-store/deploy. */\ndefine('SEXOGATE_NATIVE_MOUNT',"+quote(mount)+");define('SEXOGATE_NATIVE_RELEASE',"+quote(release)+");require "+quote(home+'/releases/'+release+'/deploy/dispatcher.php')+';\n').encode('utf8')
def own_local_proof(package):
 path=ROOT/'.local/native-browser-mount-local.json'
 if not path.is_file():raise ValueError('LOCAL_MOUNT_ACCEPTANCE_REQUIRED')
 results=json.loads(path.read_text('utf8'))
 if len(results)!=2 or {r['engine'] for r in results}!={'chromium','webkit'} or any(r.get('release')!=package['release']or r['adminRoutes']<33 or r['publicRoutes']<9 or r['pageErrors'] or r['externalRequests'] for r in results):raise ValueError('LOCAL_MOUNT_ACCEPTANCE_FAILED')
 local=json.loads((ROOT/'.local/native-stage-local.json').read_text('utf8'))
 if local['release']!=package['release']:raise ValueError('LOCAL_PROOF_RELEASE_MISMATCH')
 if path.stat().st_mtime<(ROOT/'.local/native-stage-package.json').stat().st_mtime:raise ValueError('STALE_LOCAL_ACCEPTANCE')
 language_path=ROOT/'.local/native-languages-mount-local.json'
 if language_path.stat().st_mtime<(ROOT/'.local/native-stage-package.json').stat().st_mtime:raise ValueError('STALE_LOCAL_LANGUAGE_ACCEPTANCE')
 languages=json.loads(language_path.read_text('utf8'))
 if len(languages['locales'])!=11 or languages['pageErrors'] or any(row['status']!=200 or not row['selected']or not row.get('adultMetadata')or not row.get('clientAdultMetadata')for row in languages['locales']):raise ValueError('LOCAL_LANGUAGE_ACCEPTANCE_FAILED')
 adult_proof('adult-local',package['release'],'https://127.0.0.1:3188/test')
 storefront_proof('polish-local',package['release'],'https://127.0.0.1:3188/test')
 if package.get('products'):
  proof=json.loads((ROOT/'.local/native-catalog-local.json').read_text('utf8'))
  if proof.get('release')!=package['release']or proof.get('products')!=package['products']or not proof.get('idempotent')or not proof.get('privateDrafts')or proof.get('pageErrors'):raise ValueError('LOCAL_CATALOG_ACCEPTANCE_REQUIRED')
def web_backup(ftp,values):
 names=['/test/index.php','/test/.htaccess','/test/app/active.php','/test/app/config.local.json','/test/app/owner.json'];files={name:p.read(ftp,name) for name in names};out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED)as archive:
  for name,raw in files.items():archive.writestr(name.lstrip('/'),raw)
 plain=out.getvalue();key=bytes.fromhex(values['BACKUP_ENCRYPTION_KEY']);nonce=secrets.token_bytes(12);encrypted=nonce+AESGCM(key).encrypt(nonce,plain,b'sexogate-native-rollback-v1')
 decoded=AESGCM(key).decrypt(encrypted[:12],encrypted[12:],b'sexogate-native-rollback-v1');assert decoded==plain
 with zipfile.ZipFile(io.BytesIO(decoded))as archive:
  for name,raw in files.items():assert archive.read(name.lstrip('/'))==raw
 folder=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-rollback');folder.mkdir(exist_ok=True);destination=folder/(str(time.time_ns())+'.aesgcm');destination.write_bytes(encrypted)
 return {'path':str(destination),'sha256':hashlib.sha256(encrypted).hexdigest(),'verified':True,'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
def restore_web(ftp,report):
 backup=Path(report['rollback']['path']);allowed=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-rollback').resolve()
 if not backup.resolve().is_relative_to(allowed) or hashlib.sha256(backup.read_bytes()).hexdigest()!=report['rollback']['sha256']:raise ValueError('ROLLBACK_BACKUP_INVALID')
 encrypted=backup.read_bytes();key=bytes.fromhex(p.publisher.env_values()['BACKUP_ENCRYPTION_KEY']);plain=AESGCM(key).decrypt(encrypted[:12],encrypted[12:],b'sexogate-native-rollback-v1')
 with zipfile.ZipFile(io.BytesIO(plain))as archive:
  originals={name:archive.read(name.lstrip('/'))for name in ['/test/index.php','/test/.htaccess']}
 for name,raw in originals.items():
  current=p.read(ftp,name);expected=entry(report['installation']['privateRoot'],report['release'],'/test')if name.endswith('index.php')else(ROOT/'native-store/deploy/.htaccess').read_bytes()
  if current not in [raw,expected]:raise ValueError('OTHER_DEPLOYMENT_PREVENTS_ROLLBACK')
 for name,raw in originals.items():p.store_atomic(ftp,name,raw)
 report.update(activated=False,phase='rolled_back',mainUnchanged=p.fingerprint(ftp)==report['mainBefore']);p.persist(REPORT,report)
 if not report['mainUnchanged']:raise ValueError('MAIN_SITE_CHANGED')
def prepare():
 package=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'));own_local_proof(package)
 archive=Path(package['archive']);base=Path('D:/sexogate-local-artifacts-20261114/private-installs').resolve()
 if not archive.resolve().is_relative_to(base) or archive.stat().st_size>15000000 or hashlib.sha256(archive.read_bytes()).hexdigest()!=package['sha256']:raise ValueError('PACKAGE_INVALID')
 if not p.panel.domain_owned(p.api('list_domains',module='DomainInfo')):raise ValueError('DOMAIN_OWNER_MISMATCH')
 state=json.loads(p.STATE.read_text('utf8'));values=p.publisher.env_values();ftp=p.publisher.connect(values);main=p.fingerprint(ftp);token=secrets.token_hex(32);helper='/test/__native_install_'+secrets.token_hex(12)+'.php';payload='/test/app/native-payload-'+package['release']+'.zip';preview='/test/native-preview-'+secrets.token_hex(8);report={'release':package['release'],'mainBefore':main,'activated':False,'preview':preview,'phase':'preparing'}
 route_before=route_preview=route_during=None
 try:
  if json.loads(p.read(ftp,'/test/app/owner.json'))['owner']!=state['owner']:raise ValueError('TEST_OWNER_MISMATCH')
  report['rollback']=web_backup(ftp,values);p.persist(REPORT,report)
  route_before=p.read(ftp,'/test/.htaccess');needle=b'RewriteRule ^ index.php [END]'
  if route_before==(ROOT/'native-store/deploy/.htaccess').read_bytes():
   preview_name=preview.rsplit('/',1)[1];preview_rule=('RewriteRule ^'+preview_name+'(?:/.*)?$ '+preview_name+'/index.php [END]\n').encode()
   route_preview=route_before.replace(needle,preview_rule+needle);helper_rule=('RewriteRule ^'+re.escape(helper.rsplit('/',1)[1])+'$ - [END]\n').encode();route_during=route_preview.replace(needle,helper_rule+needle)
   p.store_atomic(ftp,'/test/.htaccess',route_during);report['previewRoutingSha256']=hashlib.sha256(route_preview).hexdigest()
  request={'release':package['release'],'sha256':package['sha256'],'owner':state['owner'],'expires':int(time.time())+900,'tokenHash':hashlib.sha256(token.encode()).hexdigest()}
  p.store_atomic(ftp,'/test/app/native-request.json',json.dumps(request).encode());p.store(ftp,payload,archive.read_bytes())
  if hashlib.sha256(p.read(ftp,payload)).hexdigest()!=package['sha256']:raise ValueError('REMOTE_ARCHIVE_HASH_MISMATCH')
  p.store(ftp,helper,(ROOT/'native-store/deploy/install.php').read_bytes())
  access=json.loads((ROOT/'.local/php-stage-access.json').read_text('utf8'))
  code="$s=json_decode(stream_get_contents(STDIN),true);echo password_hash($s['password'],PASSWORD_BCRYPT);"
  hashed=subprocess.run([str(ROOT/'.local/php-runtime/php.exe'),'-r',code],input=json.dumps({'password':access['password']}).encode(),capture_output=True,check=True).stdout.decode()
  body={'email':access['email'],'passwordHash':hashed,'totpSecret':access['totpSecret']}
  for attempt in range(8):
   status,raw,_=p.get(helper,{'X-Native-Deploy':token,'Content-Type':'application/json'},json.dumps(body).encode())
   if status!=404:break
   time.sleep(.5)
  installed=json.loads(raw)
  if status!=200 or not installed.get('installed'):raise ValueError('NATIVE_INSTALL_'+installed.get('code','FAILED').upper())
  report['installation']=installed;p.ensure_dir(ftp,preview);p.store_atomic(ftp,preview+'/index.php',entry(installed['privateRoot'],package['release'],preview));p.store_atomic(ftp,preview+'/.htaccess',(ROOT/'native-store/deploy/.htaccess').read_bytes())
  report['phase']='preview';p.persist(REPORT,report);status,raw,_=p.get(preview+'/api/deployment-status');health=json.loads(raw)
  if status!=200 or health.get('release')!=package['release'] or health.get('basePath')!=preview or health.get('sourceProducts')!=package['products'] or health.get('checkoutEnabled')is not False or not health.get('database'):raise ValueError('PREVIEW_HEALTH_FAILED')
  report['previewHealth']=health;print(json.dumps({'prepared':True,'release':package['release'],'preview':'https://sexogate.com'+preview,'database':True,'products':health['products'],'sourceProducts':health['sourceProducts'],'checkoutEnabled':False,'rollbackVerified':True}))
 finally:
  try:
   existing={e['name'] for e in p.publisher.entries(ftp,'/test')}
   if helper.rsplit('/',1)[1]in existing:ftp.delete(helper)
   existing={e['name'] for e in p.publisher.entries(ftp,'/test/app')}
   for name in ['native-request.json',payload.rsplit('/',1)[1]]:
    if name in existing:ftp.delete('/test/app/'+name)
   if route_during is not None:
    if p.read(ftp,'/test/.htaccess')!=route_during:raise ValueError('OTHER_PREVIEW_ROUTE_CHANGED')
    p.store_atomic(ftp,'/test/.htaccess',route_preview if report.get('previewHealth')else route_before)
   report['mainUnchanged']=p.fingerprint(ftp)==main;report['installerRemoved']=helper.rsplit('/',1)[1]not in {e['name'] for e in p.publisher.entries(ftp,'/test')};p.persist(REPORT,report)
  finally:ftp.close()
def activate():
 report=json.loads(REPORT.read_text('utf8'));proof=json.loads((ROOT/'.local/native-browser-mount-preview.json').read_text('utf8'));expected='https://sexogate.com'+report['preview']
 if len(proof)!=2 or any(r['base']!=expected or r.get('release')!=report['release']or r['adminRoutes']<33 or r['publicRoutes']<9 or r['pageErrors'] or r['externalRequests'] for r in proof):raise ValueError('PREVIEW_BROWSER_ACCEPTANCE_REQUIRED')
 adult_proof('adult-preview',report['release'],expected)
 storefront_proof('polish-preview',report['release'],expected)
 if report['installation'].get('products'):
  catalog=json.loads((ROOT/'.local/native-catalog-preview.json').read_text('utf8'))
  if catalog.get('release')!=report['release']or catalog.get('base')!=expected or catalog.get('products')!=report['installation']['products']or not catalog.get('idempotent')or not catalog.get('privateDrafts'):raise ValueError('PREVIEW_CATALOG_ACCEPTANCE_REQUIRED')
 language_path=ROOT/'.local/native-languages-mount-preview.json';languages=json.loads(language_path.read_text('utf8'))
 if language_path.stat().st_mtime<REPORT.stat().st_mtime or len(languages['locales'])!=11 or languages['pageErrors'] or any(row['status']!=200 or not row['selected']or not row.get('adultMetadata')or not row.get('clientAdultMetadata')for row in languages['locales']):raise ValueError('PREVIEW_LANGUAGE_ACCEPTANCE_REQUIRED')
 ftp=p.publisher.connect(p.publisher.env_values());changed=False
 try:
  if p.fingerprint(ftp)!=report['mainBefore']:raise ValueError('MAIN_CHANGED_SINCE_PREPARE')
  for path in ['/test/index.php','/test/.htaccess']:
   expected_sha=report.get('previewRoutingSha256',report['rollback']['files'][path])if path.endswith('.htaccess')else report['rollback']['files'][path]
   if hashlib.sha256(p.read(ftp,path)).hexdigest()!=expected_sha:raise ValueError('OTHER_TEST_DEPLOYMENT_DETECTED')
  # Geçişten önce son kez çalışan özel önizleme ve SQLite kontrolü.
  status,raw,_=p.get(report['preview']+'/api/deployment-status');health=json.loads(raw)
  if status!=200 or health.get('release')!=report['release'] or health.get('basePath')!=report['preview'] or not health.get('database') or health.get('checkoutEnabled')is not False:raise ValueError('PRE_ACTIVATION_CHECK_FAILED')
  new=entry(report['installation']['privateRoot'],report['release'],'/test');p.store_atomic(ftp,'/test/index.php',new);changed=True;p.store_atomic(ftp,'/test/.htaccess',(ROOT/'native-store/deploy/.htaccess').read_bytes())
  health={}
  for attempt in range(8):
   status,raw,_=p.get('/test/api/deployment-status')
   try:health=json.loads(raw)
   except json.JSONDecodeError:health={}
   if status==200 and health.get('release')==report['release'] and health.get('database') and health.get('checkoutEnabled')is False:break
   time.sleep(.5)
  else:raise ValueError('ACTIVATION_HEALTH_FAILED')
  report.update(activated=True,phase='active',health=health,mainUnchanged=p.fingerprint(ftp)==report['mainBefore']);p.persist(REPORT,report)
  if not report['mainUnchanged']:raise ValueError('MAIN_SITE_CHANGED')
  print(json.dumps({'activated':True,'url':'https://sexogate.com/test','release':report['release'],'mainUnchanged':True,'checkoutEnabled':False,'products':health['products'],'sourceProducts':health['sourceProducts']}))
 except Exception:
  if changed:restore_web(ftp,report)
  raise
 finally:ftp.close()
def rollback():
 report=json.loads(REPORT.read_text('utf8'));ftp=p.publisher.connect(p.publisher.env_values())
 try:restore_web(ftp,report);print(json.dumps({'rolledBack':True,'mainUnchanged':report['mainUnchanged']}))
 finally:ftp.close()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','activate','rollback']);args=parser.parse_args()
 try:{'prepare':prepare,'activate':activate,'rollback':rollback}[args.action]()
 except Exception as error:
  code=str(error)if isinstance(error,ValueError)and re.fullmatch('[A-Z_0-9]+',str(error))else type(error).__name__;print(json.dumps({'deployed':False,'code':code}));raise SystemExit(1)
