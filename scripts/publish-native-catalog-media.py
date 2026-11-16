#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/publish-native-catalog-media.py
# Açıklama   : Hash denetimli kaynak fotoğraflarını yalnız test uygulamasının web dışı alanına aktarır.
import hashlib,importlib.util,io,json,re,secrets,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('publisher',ROOT/'scripts/publish-php-test.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
selection_path=ROOT/('.local/native-marketplace-selection.json'if(ROOT/'.local/native-marketplace-selection.json').is_file()else'.local/native-catalog-selection.json')
selection=json.loads(selection_path.read_text('utf8'));prepared=Path(selection['path']);allowed_base=Path('D:/sexogate-local-artifacts-20261114/private-installs').resolve()
media_roots=[Path(selection['mediaRoot']).resolve()]+([Path(selection['legacyMediaRoot']).resolve()]if selection.get('legacyMediaRoot')else[])
assert all(p in [allowed_base/'native-catalog-20261115/media',allowed_base/'marketplace-catalog-20261116/media']for p in media_roots)
def media_file(name):
 assert re.fullmatch(r'[a-f0-9]{64}\.(jpg|png|webp)',name)
 matches=[folder/name for folder in media_roots if(folder/name).is_file()and not(folder/name).is_symlink()]
 assert matches,'MEDIA_FILE_MISSING'
 return matches[0]
rows=json.loads((prepared/'media-manifest.json').read_text('utf8'));checkpoint=ROOT/'.local/native-catalog-media-upload.json';done=set(json.loads(checkpoint.read_text('utf8')).get('verified',[]))if checkpoint.is_file()else set();pending=[r for r in rows if r['file']not in done]
ftp=p.publisher.connect(p.publisher.env_values());before=p.fingerprint(ftp);token=secrets.token_hex(32);state=json.loads(p.STATE.read_text('utf8'));helper='/test/__native_maintenance_'+secrets.token_hex(12)+'.php';record='/test/app/native-maintenance-request.json';route_before=route_during=None;payload=None
try:
 route_before=p.read(ftp,'/test/.htaccess');expected=(ROOT/'native-store/deploy/.htaccess').read_bytes();assert route_before==expected,'UNKNOWN_NATIVE_ROUTE_CONFIGURATION';needle=b'RewriteRule ^ index.php [END]';assert route_before.count(needle)==1
 route_during=route_before.replace(needle,('RewriteRule ^'+re.escape(helper.rsplit('/',1)[1])+'$ - [END]\n').encode()+needle);time.sleep(1.1);p.store_atomic(ftp,'/test/.htaccess',route_during)
 p.store_atomic(ftp,record,json.dumps({'owner':state['owner'],'expires':int(time.time())+3600,'tokenHash':hashlib.sha256(token.encode()).hexdigest()}).encode());p.store(ftp,helper,(ROOT/'native-store/deploy/maintenance.php').read_bytes())
 while pending:
  batch=[];size=0
  while pending and len(batch)<100 and (not batch or size+pending[0]['bytes']<7500000):
   row=pending.pop(0);path=media_file(row['file']);assert re.fullmatch(r'[a-f0-9]{64}\.(jpg|png|webp)',path.name)and not path.is_symlink()and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];batch.append(row);size+=row['bytes']
  output=io.BytesIO()
  with zipfile.ZipFile(output,'w',zipfile.ZIP_STORED)as archive:
   for row in batch:archive.write(media_file(row['file']),row['file'])
  body=output.getvalue();assert len(body)<9000000;identifier=secrets.token_hex(12);payload='/test/app/native-media-'+identifier+'.zip';p.store(ftp,payload,body)
  for attempt in range(12):
   status,raw,_=p.get(helper,{'X-Native-Maintenance':token,'Content-Type':'application/json'},json.dumps({'action':'media','id':identifier,'sha256':hashlib.sha256(body).hexdigest()}).encode())
   if status not in [404,405]:break
   time.sleep(1)
  result=json.loads(raw);assert status==200 and result.get('stored')and set(result['files'])=={r['file']for r in batch},'REMOTE_MEDIA_VERIFICATION_FAILED'
  done.update(result['files']);p.persist(checkpoint,{'dataset':selection['dataset'],'verified':sorted(done),'originalBytesPreserved':True});payload=None;print(json.dumps({'verifiedMedia':len(done),'remaining':len(pending)}),flush=True)
finally:
 try:
  for path in [helper,record,payload]:
   if path and path.rsplit('/',1)[1]in{e['name']for e in p.publisher.entries(ftp,path.rsplit('/',1)[0])}:ftp.delete(path)
  if route_during is not None:
   if p.read(ftp,'/test/.htaccess')!=route_during:raise ValueError('OTHER_NATIVE_ROUTE_CHANGED')
   p.store_atomic(ftp,'/test/.htaccess',route_before)
  assert p.fingerprint(ftp)==before,'MAIN_CHANGED_DURING_MEDIA_UPLOAD'
 finally:ftp.close()
