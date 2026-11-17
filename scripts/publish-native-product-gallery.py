#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/publish-native-product-gallery.py
# Açıklama   : Görsel inceleme kaydına bağlı ek fotoğrafları yalnız test uygulamasının özel medya alanına aktarır.
import hashlib,importlib.util,io,json,re,secrets,time,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
MEDIA=Path('D:/sexogate-local-artifacts-20261114/private-installs/product-gallery-20261117/media').resolve()
REGISTRY=ROOT/'native-store/storefront/product-gallery-data.json'
REVIEW=ROOT/'.local/native-product-gallery-review.json'
CHECKPOINT=ROOT/'.local/native-product-gallery-media-upload.json'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def approved_assets():
 data=json.loads(REGISTRY.read_text('utf8'));review=json.loads(REVIEW.read_text('utf8'))
 assert data.get('schema')==1 and data.get('sourceDataset')=='057fb50f7d5887fee341e3d5b4a3dd64','GALLERY_DATASET_INVALID'
 assert review.get('registrySha256')==digest(REGISTRY) and review.get('sourceDataset')==data['sourceDataset'] and review.get('humanVisualReview')is True,'GALLERY_VISUAL_REVIEW_REQUIRED'
 approved=set(review['approvedHashes']);assets={}
 for product,row in data['products'].items():
  assert re.fullmatch(r'sg_ty_[a-f0-9]{16}',product)
  for image in row['images']:
   name=image['file'];sha=image['sha256'];assert image.get('approved')is True and sha in approved and re.fullmatch(sha+r'\.(jpg|png|webp)',name),'GALLERY_NOT_APPROVED'
   path=MEDIA/name;assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(MEDIA) and digest(path)==sha,'GALLERY_MEDIA_HASH_MISMATCH'
   size=path.stat().st_size;assert 0<size<7500000,'GALLERY_MEDIA_BATCH_SIZE'
   assets[name]={'file':name,'sha256':sha,'bytes':size}
 return data,list(assets.values())

def main():
 data,rows=approved_assets()
 spec=importlib.util.spec_from_file_location('gallery_publisher',ROOT/'scripts/publish-php-test.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
 # Önceki checkpoint varlık kanıtı değildir; geri yükleme dosyayı kaldırmış olabilir.
 done=set();pending=list(rows)
 ftp=p.publisher.connect(p.publisher.env_values());before=p.fingerprint(ftp);token=secrets.token_hex(32);state=json.loads(p.STATE.read_text('utf8'));helper='/test/__native_maintenance_'+secrets.token_hex(12)+'.php';record='/test/app/native-maintenance-request.json';route_before=route_during=payload=None
 try:
  route_before=p.read(ftp,'/test/.htaccess');assert route_before==(ROOT/'native-store/deploy/.htaccess').read_bytes(),'GALLERY_UNKNOWN_TEST_ROUTE'
  needle=b'RewriteRule ^ index.php [END]';assert route_before.count(needle)==1
  route_during=route_before.replace(needle,('RewriteRule ^'+re.escape(helper.rsplit('/',1)[1])+'$ - [END]\n').encode()+needle);time.sleep(1.1);p.store_atomic(ftp,'/test/.htaccess',route_during)
  p.store_atomic(ftp,record,json.dumps({'owner':state['owner'],'expires':int(time.time())+3600,'tokenHash':hashlib.sha256(token.encode()).hexdigest()}).encode());p.store(ftp,helper,(ROOT/'native-store/deploy/maintenance.php').read_bytes())
  while pending:
   batch=[];size=0
   while pending and len(batch)<100 and (not batch or size+pending[0]['bytes']<7500000):
    row=pending.pop(0);assert digest(MEDIA/row['file'])==row['sha256'],'GALLERY_CHANGED_AFTER_APPROVAL';batch.append(row);size+=row['bytes']
   output=io.BytesIO()
   with zipfile.ZipFile(output,'w',zipfile.ZIP_STORED)as archive:
    for row in batch:archive.write(MEDIA/row['file'],row['file'])
   body=output.getvalue();assert len(body)<9000000;identifier=secrets.token_hex(12);payload='/test/app/native-media-'+identifier+'.zip';p.store(ftp,payload,body)
   for attempt in range(12):
    status,raw,_=p.get(helper,{'X-Native-Maintenance':token,'Content-Type':'application/json'},json.dumps({'action':'media','id':identifier,'sha256':hashlib.sha256(body).hexdigest()}).encode())
    if status not in [404,405]:break
    time.sleep(1)
   result=json.loads(raw);assert status==200 and result.get('stored')and set(result['files'])=={r['file']for r in batch},'GALLERY_REMOTE_MEDIA_NOT_VERIFIED'
   done.update(result['files']);p.persist(CHECKPOINT,{'dataset':data['sourceDataset'],'registrySha256':digest(REGISTRY),'verified':sorted(done),'originalBytesPreserved':True});payload=None;print(json.dumps({'galleryVerified':sum(r['file']in done for r in rows),'remaining':len(pending)}),flush=True)
  assert digest(REGISTRY)==json.loads(REVIEW.read_text('utf8'))['registrySha256'],'GALLERY_REVIEW_CHANGED_DURING_UPLOAD'
 finally:
  try:
   for path in [helper,record,payload]:
    if path and path.rsplit('/',1)[1]in{e['name']for e in p.publisher.entries(ftp,path.rsplit('/',1)[0])}:ftp.delete(path)
   if route_during is not None:
    assert p.read(ftp,'/test/.htaccess')==route_during,'OTHER_TEST_ROUTE_CHANGED';p.store_atomic(ftp,'/test/.htaccess',route_before)
   assert p.fingerprint(ftp)==before,'MAIN_CHANGED_DURING_GALLERY_UPLOAD'
  finally:ftp.close()
 print(json.dumps({'approvedAssets':len(rows),'verified':True,'registrySha256':digest(REGISTRY),'mainUnchanged':True,'publicMainModified':False}))

if __name__=='__main__':main()
