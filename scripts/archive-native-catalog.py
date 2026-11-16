#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/archive-native-catalog.py
# Açıklama   : Yetkili yönetim API’siyle mevcut vitrini sürümlü ve geri alınabilir biçimde yayından kaldırır.
import argparse,base64,hashlib,hmac,json,os,struct,sys,time,sqlite3
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_test_errors import safe_error
sys.excepthook=safe_error
ROOT=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--remote',action='store_true');a=p.parse_args();base='https://sexogate.com/test'if a.remote else'https://127.0.0.1:3188/test';phase='remote'if a.remote else'local'
access=json.loads((ROOT/'.local'/('php-stage-access.json'if a.remote else'php-access.json')).read_text('utf-8'))
def otp():
 key=base64.b32decode(access['totpSecret']+'='*((8-len(access['totpSecret'])%8)%8));d=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=d[-1]&15;return str((struct.unpack('>I',d[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
if not a.remote:
 state=Path(json.loads((ROOT/'.local/native-stage-local.json').read_text('utf-8'))['home'])/'state';target=Path('D:/sexogate-local-artifacts-20261114/private-installs/catalog-before-replacement-20261116');target.mkdir(exist_ok=True)
 for f in state.glob('*.sqlite'):
  if not(target/f.name).exists():
   with sqlite3.connect(f)as src,sqlite3.connect(target/f.name)as dest:src.backup(dest);assert dest.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
else:
 backup=json.loads((ROOT/'.local/native-backup-restore.json').read_text('utf-8'));assert backup['restored']and backup['encrypted']and backup['foreignKeysValid'],'VERIFIED_BACKUP_REQUIRED';assert (ROOT/'.local/native-backup-restore.json').stat().st_mtime>time.time()-900,'FRESH_BACKUP_REQUIRED'
with sync_playwright()as driver:
 browser=driver.chromium.launch();context=browser.new_context(ignore_https_errors=not a.remote);page=context.new_page();page.set_default_timeout(60000);page.goto(base+'/yonetim',wait_until='domcontentloaded');page.locator('[name=email]').fill(access['email']);page.locator('[name=password]').fill(access['password']);page.get_by_role('button',name='Devam et',exact=True).click();page.locator('#verify').wait_for();time.sleep(max(0,30.5-time.time()%30));page.locator('[name=proof]').fill(otp());page.locator('#verify button[type=submit]').click();page.locator('.sidebar').wait_for()
 api=context.request;session=api.get(base+'/api/admin/session').json();headers={'Content-Type':'application/json','Origin':base.split('/test')[0],'X-CSRF-Token':session['csrfToken']}
 assert session['user']['role']=='owner','OWNER_REQUIRED';public=api.get(base+'/api/catalog',timeout=60000).json();public=public.get('catalog',public);rows=api.get(base+'/api/admin/products',timeout=60000).json()['data'];pending=[r for r in rows if r.get('publishedVersion',0)>0];assert all(r['id'].startswith(('sg_xsh_','sg_lio_','sg_sis_'))for r in pending),'UNEXPECTED_PRODUCTS_REVIEW_REQUIRED'
 checkpoint=ROOT/'.local'/('catalog-archive-'+phase+'-20261116.json');report=json.loads(checkpoint.read_text('utf-8'))if checkpoint.exists()else{'base':base,'startedAt':int(time.time()),'beforeVisible':len(public['products']),'archived':[],'retainedRecords':True,'ordersDeleted':False,'completed':False};checkpoint.write_text(json.dumps(report,indent=2),'utf-8')
 for row in pending:
  response=api.post(base+'/api/admin/products/'+row['id']+'/unpublish',headers=headers,data=json.dumps({'version':row['version']}),timeout=60000);assert response.status==200,'ARCHIVE_FAILED_STATUS_'+str(response.status)
  report['archived'].append(row['id']);checkpoint.write_text(json.dumps(report,indent=2),'utf-8')
  if len(report['archived'])%50==0:print(json.dumps({'phase':phase,'archived':len(report['archived'])}),flush=True)
 health=api.get(base+'/api/deployment-status',timeout=60000).json();after=api.get(base+'/api/catalog',timeout=60000).json();after=after.get('catalog',after);assert health['products']==len(after['products'])==0,'PUBLIC_CATALOG_NOT_EMPTY'
 after_rows=api.get(base+'/api/admin/products',timeout=60000).json()['data'];assert len(after_rows)==len(rows)and not any(r.get('publishedVersion',0)>0 for r in after_rows),'ARCHIVE_NOT_RETAINED'
 report.update(completed=True,completedAt=int(time.time()),visibleAfter=0,retainedCount=len(after_rows),release=health['release']);checkpoint.write_text(json.dumps(report,indent=2),'utf-8');print(json.dumps({k:v for k,v in report.items()if k!='archived'}));context.close();browser.close()
