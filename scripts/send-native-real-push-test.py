#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/send-native-real-push-test.py
# Açıklama   : Hazır izole Chrome cihazına tek bildirim yollar; bakım yollarını geri kaldırır.
import hashlib,importlib.util,json,re,secrets,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('native_publish',ROOT/'scripts/publish-native-test.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);p=module.p
ready=json.loads((ROOT/'.local/native-real-push-ready.json').read_text('utf8'));deployment=json.loads((ROOT/'.local/native-stage-deployment.json').read_text('utf8'));state=json.loads(p.STATE.read_text('utf8'))
assert deployment['phase']=='active'and deployment['release']==ready['release']and ready['base']=='https://sexogate.com/test'and 0<=time.time()-ready['createdAt']<180
for key,length in [('release',24),('tag',64),('endpointHash',64)]:assert re.fullmatch('[a-f0-9]{'+str(length)+'}',ready[key])
assert re.fullmatch('sg_[a-z0-9_]+',ready['productId'])
ftp=p.publisher.connect(p.publisher.env_values());route_path='/test/.htaccess';record='/test/app/native-push-request.json';name='__native_push_'+secrets.token_hex(12)+'.php';helper='/test/'+name;token=secrets.token_hex(32);before=p.read(ftp,route_path);baseline=(ROOT/'native-store/deploy/.htaccess').read_bytes();assert before==baseline
needle=b'RewriteRule ^index\\.php$ - [END]\n';assert before.count(needle)==1;during=before.replace(needle,('RewriteRule ^'+re.escape(name)+'$ - [END]\n').encode()+needle);main=p.fingerprint(ftp);receipt={'release':ready['release'],'realStockEvent':False}
try:
 payload={**ready,'expires':int(time.time())+180,'owner':state['owner'],'tokenHash':hashlib.sha256(token.encode()).hexdigest(),'consumed':False}
 p.store_atomic(ftp,record,json.dumps(payload).encode());p.store(ftp,helper,(ROOT/'scripts/native-real-push-test.php').read_bytes());p.store_atomic(ftp,route_path,during)
 status,raw,_=p.post(helper,{}, {'X-Native-Push':token});receipt.update(httpStatus=status,response=json.loads(raw))
finally:
 try:
  names={row['name']for row in p.publisher.entries(ftp,'/test')}
  if name in names:ftp.delete(helper)
  names={row['name']for row in p.publisher.entries(ftp,'/test/app')}
  if 'native-push-request.json'in names:ftp.delete(record)
  assert p.read(ftp,route_path)==during,'OTHER_ROUTING_CHANGED';p.store_atomic(ftp,route_path,before);receipt.update(helperRemoved=True,routingRestored=p.read(ftp,route_path)==before,mainUnchanged=p.fingerprint(ftp)==main)
 finally:ftp.close();(ROOT/'.local/native-real-push-send.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps(receipt),flush=True)
