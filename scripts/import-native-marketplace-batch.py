#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/import-native-marketplace-batch.py
# Açıklama   : İncelenmiş yeni kaynak dilimini gerçek MFA yönetim API’siyle yükler; eski ürünleri yeniden yayımlamaz.
import base64,hashlib,hmac,json,os,re,struct,time
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');assert BASE=='https://127.0.0.1:3188/test'or re.fullmatch(r'https://sexogate\.com/test(?:/native-preview-[a-f0-9]{16})?',BASE)
remote=BASE.startswith('https://sexogate.com');access=json.loads((ROOT/'.local'/('php-stage-access.json'if remote else'php-access.json')).read_text('utf8'));selection=json.loads((ROOT/'.local/native-marketplace-selection.json').read_text('utf8'));package=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'));data=json.loads((Path(selection['path'])/'catalog-data.json').read_text('utf8'));new=data['products'][2194:];expected={p['id']for p in new if p['images']and p['visualApprovedIndices']and not p['eligibilityHold']and p['salePriceMinor']}
session=requests.Session();session.verify=True if remote else str(Path(json.loads((ROOT/'.local/native-stage-local.json').read_text('utf8'))['base'])/'tls.pem')
csrf=None
def api(path,body=None,method='POST'):
 headers={'Accept':'application/json'}
 if body is not None:headers.update({'Origin':BASE.split('/test')[0],'X-CSRF-Token':csrf})
 response=session.get(BASE+'/api/admin/'+path,timeout=(12,60))if body is None else session.request(method,BASE+'/api/admin/'+path,json=body,headers=headers,timeout=(12,60))
 if response.status_code!=200:raise RuntimeError('ADMIN_'+str(response.status_code)+'_'+str(response.json().get('error','unknown')))
 return response.json()
status=session.get(BASE+'/api/deployment-status',timeout=(12,60)).json();assert status['release']==package['release'],'WRONG_PACKAGE_FOR_IMPORT'
auth=api('session');csrf=auth['csrfToken'];auth=api('login',{'email':access['email'],'password':access['password']});csrf=auth['csrfToken'];time.sleep(30.1-time.time()%30)
secret=access['totpSecret'];key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));digest=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15;code=str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6);auth=api('login/verify',{'code':code});csrf=auth['csrfToken'];assert auth['user']['role']=='owner'
source=api('catalog-source');assert source['dataset']==selection['dataset']and source['products']==len(data['products'])
before=session.get(BASE+'/api/catalog',timeout=(12,60)).json();assert all(p['id'].startswith('sg_ty_')for p in before['products']),'OLD_ARCHIVED_PRODUCTS_VISIBLE'
totals={'created':0,'published':0,'preserved':0};offset=2194
while offset<len(data['products']):
 body={'dataset':selection['dataset'],'offset':offset};result=api('catalog-import',body);replay=api('catalog-import',body);assert replay==result,'IMPORT_REPLAY_CHANGED';offset=result['nextOffset']
 for name in totals:totals[name]+=result[name]
normalized=0
for product in new:
 if product.get('brand','').strip().casefold()not in ['genel markalar','markasız','markasiz','diğer','diger']:continue
 editor=api('products/'+product['id']+'/editor');record=editor['record'];current=record['data']
 if current.get('brand','').strip().casefold()not in ['genel markalar','markasız','markasiz','diğer','diger']:continue
 assert record['version']==record['publishedVersion']or record['publishedVersion']==0,'CONCURRENT_PRODUCT_DRAFT_REQUIRES_REVIEW'
 updated=dict(current);brand=current['brand'];updated['brand']=''
 for key,value in list(updated.items()):
  if isinstance(value,str)and key.startswith(('title_','seoTitle_','seoDescription_')):updated[key]=value.removeprefix(brand+' ')
 saved=api('products/'+product['id'],{'version':record['version'],'data':updated},'PUT')
 if record['publishedVersion']>0:api('products/'+product['id']+'/publish',{'version':saved['data']['version']})
 normalized+=1
final=session.get(BASE+'/api/catalog',timeout=(12,60)).json();actual={p['id']for p in final['products']};assert actual==expected,('VISIBLE_PRODUCT_SET_MISMATCH',len(actual),len(expected));assert all(p['stockKnown']is False and p['stockQuantity']is None for p in final['products'])
assert all(p.get('brand','').casefold()not in ['genel markalar','markasız','markasiz','diğer','diger']for p in final['products']),'UNKNOWN_BRAND_ADVERTISED'
result={'genericBrandsNotInvented':True,'normalizedGenericBrands':normalized,'base':BASE,'release':package['release'],'dataset':selection['dataset'],'loadedNew':len(new),'sourceDetails':selection['sourceProducts'],'deferred':selection['sourceProducts']-len(new),'visibleNew':len(actual),'oldSupplierProductsVisible':False,'stockNotInvented':True,'idempotent':True,'realPayments':False,'counts':totals};suffix='preview'if'/native-preview-'in BASE else'remote'if remote else'local';(ROOT/('.local/native-marketplace-import-'+suffix+'.json')).write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result))
