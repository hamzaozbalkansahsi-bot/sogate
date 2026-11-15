#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-installer.py
# Açıklama   : Gerçek PHP HTTP kurucusunda doğru paket ve zararlı ZIP reddini izole alanda sınar.
import hashlib,io,json,os,secrets,shutil,stat,subprocess,time,urllib.error,urllib.request,zipfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT=Path(__file__).resolve().parent.parent;p=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'));base=Path('D:/sexogate-local-artifacts-20261114/private-installs')/('native-install-test-'+secrets.token_hex(8));web=base/'web';app=web/'test/app';app.mkdir(parents=True);shutil.copy2(ROOT/'native-store/deploy/install.php',web/'test/install.php');token=secrets.token_hex(32);owner=secrets.token_hex(32)
php=ROOT/'.local/php-runtime/php.exe';r=subprocess.run([str(php),'-r',"echo password_hash('isolated-native-install-password',PASSWORD_BCRYPT);"],capture_output=True,check=True);body=json.dumps({'email':'native-install@example.invalid','passwordHash':r.stdout.decode(),'totpSecret':'J'*103}).encode()
log=(base/'php.log').open('wb');server=subprocess.Popen([str(php),'-d','extension=pdo_sqlite','-d','extension=sqlite3','-S','127.0.0.1:3189','-t',str(web)],stdout=log,stderr=log)
def request(archive,identifier,*,wrong_hash=False,proof=token,expired=False):
 raw=archive if isinstance(archive,bytes)else Path(archive).read_bytes();(app/('native-payload-'+identifier+'.zip')).write_bytes(raw);record={'release':identifier,'sha256':'0'*64 if wrong_hash else hashlib.sha256(raw).hexdigest(),'owner':owner,'expires':int(time.time())+300 if not expired else int(time.time())-1,'tokenHash':hashlib.sha256(token.encode()).hexdigest()};(app/'native-request.json').write_text(json.dumps(record),encoding='utf8')
 req=urllib.request.Request('http://127.0.0.1:3189/test/install.php',data=body,headers={'X-Native-Deploy':proof,'Content-Type':'application/json'})
 for attempt in range(20):
  try:
   with urllib.request.urlopen(req,timeout=20)as response:return response.status,json.load(response)
  except urllib.error.HTTPError as error:return error.code,json.load(error)
  except urllib.error.URLError:
   if attempt==19:raise
   time.sleep(.1)
def attack(name,*,symlink=False,duplicate=False):
 identifier=secrets.token_hex(12);content=b'isolated-path-probe';manifest={'release':identifier,'checkoutEnabled':False,'products':0,'previewOnly':True,'files':{name:hashlib.sha256(content).hexdigest()}};out=io.BytesIO()
 with zipfile.ZipFile(out,'w')as z:
  z.writestr('deployment-manifest.json',json.dumps(manifest));info=zipfile.ZipInfo(name)
  if symlink:info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
  z.writestr(info,content)
  if duplicate:z.writestr(name,content)
 return out.getvalue(),identifier
results=[]
def changed_catalog(change):
 identifier=secrets.token_hex(12)
 with zipfile.ZipFile(p['archive'])as archive:files={name:archive.read(name)for name in archive.namelist()}
 catalog=json.loads(files['private/catalog.json'])
 if len(catalog['categories'])==6:catalog['categories'].append({'id':'sg_toys_fixture','parentId':'sg_toys','name':catalog['categories'][0]['name']})
 change(catalog);files['private/catalog.json']=json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode()
 manifest=json.loads(files['deployment-manifest.json']);manifest['release']=identifier;manifest['files']['private/catalog.json']=hashlib.sha256(files['private/catalog.json']).hexdigest();files['deployment-manifest.json']=json.dumps(manifest).encode();output=io.BytesIO()
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED)as archive:
  for name,content in files.items():archive.writestr(name,content)
 return output.getvalue(),identifier
try:
 for kind,kwargs in [('unauthenticated',{'proof':'wrong'}),('expired',{'expired':True}),('wrong-hash',{'wrong_hash':True})]:
  status,value=request(p['archive'],p['release'],**kwargs);assert status==400 and value['installed']is False,(kind,status,value);results.append(kind)
 status,value=request(p['archive'],p['release']);assert status==200 and value['installed'] and value['ownerCount']==1 and value['products']==p['products'],(status,value);results.append('valid-provenance-catalog-and-mfa-owner')
 for kind,change in ([
  ('category-orphan-parent',lambda c:c['categories'][6].update(parentId='missing-root')),
  ('category-cycle',lambda c:c['categories'][6].update(parentId=c['categories'][6]['id'])),
  ('category-duplicate-id',lambda c:c['categories'][6].update(id=c['categories'][0]['id'],parentId=None)),
  ('category-foreign-namespace',lambda c:c['categories'][6].update(id='donor-furniture',parentId=None)),
  ('product-unknown-category',lambda c:c['products'][0].update(categoryIds=['missing-category']))]if p['products']else []):
  archive,identifier=changed_catalog(change);status,value=request(archive,identifier);assert status==400 and value['code']=='catalog_provenance_invalid',(kind,status,value);results.append(kind)
 entry=base/'.sexogate-native-test/releases'/p['release']/'public/index.php';php_entry="<?php define('NODENO_RUNTIME_LIBRARY',true);require '"+entry.as_posix()+"';$_SERVER['REQUEST_URI']='/api/catalog';nodenoRun();";(web/'test/fresh-catalog.php').write_text(php_entry,encoding='utf8')
 with urllib.request.urlopen('http://127.0.0.1:3189/test/fresh-catalog.php',timeout=20)as response:fresh=json.load(response)
 assert fresh['products']==[],'UNPUBLISHED_SOURCE_CATALOG_EXPOSED';results.append('unpublished_catalog_private_at_revision_zero')
 for kind,name,options in [('traversal','../escape.php',{}),('absolute','/escape.php',{}),('dot-alias','public/./escape.js',{}),('symlink','public/escape.js',{'symlink':True}),('duplicate','public/duplicate.js',{'duplicate':True})]:
  archive,identifier=attack(name,**options);status,value=request(archive,identifier);assert status==400 and value['installed']is False and value['code']=='archive_path_invalid',(kind,status,value);results.append(kind)
 assert not (base/'escape.php').exists() and not (base/'.sexogate-native-test/escape.php').exists()
 result=subprocess.run([str(php),'-d','extension=pdo_sqlite','-d','extension=sqlite3',str(base/'.sexogate-native-test/worker.php')],capture_output=True);assert result.returncode==0,'ORIGINAL_CONTENT_WORKER_FAILED';results.append('cli-content-worker')
 shutil.copy2(ROOT/'native-store/deploy/maintenance.php',web/'test/maintenance.php');(app/'native-maintenance-request.json').write_text(json.dumps({'owner':owner,'expires':int(time.time())+300,'tokenHash':hashlib.sha256(token.encode()).hexdigest()}),encoding='utf8')
 image=next((base/'.sexogate-native-test/releases'/p['release']/'public').rglob('apple-touch-icon.png')).read_bytes();image_name=hashlib.sha256(image).hexdigest()+'.png'
 def media_request(name,content):
  identifier=secrets.token_hex(12);output=io.BytesIO()
  with zipfile.ZipFile(output,'w')as archive:archive.writestr(name,content)
  raw=output.getvalue();(app/('native-media-'+identifier+'.zip')).write_bytes(raw);req=urllib.request.Request('http://127.0.0.1:3189/test/maintenance.php',data=json.dumps({'action':'media','id':identifier,'sha256':hashlib.sha256(raw).hexdigest()}).encode(),headers={'X-Native-Maintenance':token,'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=20)as response:return response.status,json.load(response)
  except urllib.error.HTTPError as error:return error.code,json.load(error)
 status,receipt=media_request(image_name,image);assert status==200 and receipt['created']==1;assert (base/'.sexogate-native-test/media'/image_name).read_bytes()==image;results.append('private-original-media')
 status,receipt=media_request(image_name,image);assert status==200 and receipt['existing']==1;results.append('media-idempotency')
 for label,name,content in [('media-traversal','../escape.png',image),('media-hash',image_name,b'wrong'),('media-mime',hashlib.sha256(b'not-an-image').hexdigest()+'.png',b'not-an-image')]:
  status,receipt=media_request(name,content);assert status==400 and not receipt.get('stored');results.append(label)
 identifier=secrets.token_hex(12);key=secrets.token_bytes(32)
 req=urllib.request.Request('http://127.0.0.1:3189/test/maintenance.php',data=json.dumps({'action':'backup','id':identifier,'key':key.hex()}).encode(),headers={'X-Native-Maintenance':token,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30)as response:receipt=json.load(response)
 assert receipt['created'] and receipt['databases']>=2;encrypted=(app/'native-backups'/(identifier+'.aesgcm')).read_bytes();assert hashlib.sha256(encrypted).hexdigest()==receipt['sha256'];plain=AESGCM(key).decrypt(encrypted[9:21],encrypted[37:]+encrypted[21:37],b'sexogate-native-backup-v1')
 with zipfile.ZipFile(io.BytesIO(plain))as archive:
  manifest=json.loads(archive.read('manifest.json'))
  for name,digest in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==digest
 results.append('encrypted-consistent-sqlite-backup')
 print(json.dumps({'passed':len(results),'checks':results,'isolated':True,'liveDataOrCharging':False}))
finally:server.terminate();server.wait(timeout=10);log.close()
