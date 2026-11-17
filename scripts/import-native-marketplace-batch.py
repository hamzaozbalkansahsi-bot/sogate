#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/import-native-marketplace-batch.py
# Açıklama   : İncelenmiş yeni kaynak dilimini gerçek MFA yönetim API’siyle yükler; eski ürünleri yeniden yayımlamaz.
import base64,hashlib,hmac,json,os,re,struct,time
from pathlib import Path
import requests
from native_marketplace_paths import marketplace_paths
from native_marketplace_import_guard import (
 canonical_data,fingerprint,frozen_baseline,project_initials,guarded_upgrade,normalize_generic_brand,
)
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');assert BASE=='https://127.0.0.1:3188/test'or re.fullmatch(r'https://sexogate\.com/test(?:/native-preview-[a-f0-9]{16})?',BASE)
remote=BASE.startswith('https://sexogate.com');access=json.loads((ROOT/'.local'/('php-stage-access.json'if remote else'php-access.json')).read_text('utf8'));selection=json.loads((ROOT/'.local/native-marketplace-selection.json').read_text('utf8'));paths=marketplace_paths(selection);package=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'));data=json.loads((paths.prepared/'catalog-data.json').read_text('utf8'));new=data['products'][2194:];expected={p['id']for p in new if p['images']and p['visualApprovedIndices']and not p['eligibilityHold']and p['salePriceMinor']}
private=Path(package['bundle'])/'private';packaged=json.loads((private/'catalog.json').read_text('utf8'))
assert package['dataset']==selection['dataset']and data['dataset']==selection['dataset']and packaged['products']==data['products'],'WRONG_DATASET_FOR_IMPORT'
baseline_products,held51,baseline_proof=frozen_baseline();old_ids={p['id']for p in baseline_products};public80=old_ids-held51
initial16=project_initials(ROOT/'.local/php-runtime/php.exe',private,baseline_products);initial17=project_initials(ROOT/'.local/php-runtime/php.exe',private,new)
approved_old=held51&expected;suffix='preview'if'/native-preview-'in BASE else'remote'if remote else'local'
upgrade_scope=BASE+'|'+package['release'];scope_key=hashlib.sha256(upgrade_scope.encode('utf8')).hexdigest()[:16]
intent_file=ROOT/('.local/native-marketplace-upgrade-intent-'+suffix+'-'+scope_key+'-'+selection['dataset']+'.json')
intents=json.loads(intent_file.read_text('utf8'))if intent_file.exists()else{}
assert isinstance(intents,dict),'UPGRADE_INTENT_INVALID'
def checkpoint():
 temporary=intent_file.with_suffix('.json.tmp');temporary.write_text(json.dumps(intents,ensure_ascii=False,sort_keys=True,indent=2),'utf8');temporary.replace(intent_file)
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
before_ids={p['id']for p in before['products']}
protected_ids=public80&before_ids;protected_before={row['id']:row for row in api('products')['data']if row['id']in protected_ids}if protected_ids else{}
assert set(protected_before)==protected_ids,'PROTECTED_PUBLIC_RECORD_MISSING'
totals={'created':0,'published':0,'preserved':0};offset=2194
while offset<len(data['products']):
 body={'dataset':selection['dataset'],'offset':offset};result=api('catalog-import',body);replay=api('catalog-import',body);assert replay==result,'IMPORT_REPLAY_CHANGED';offset=result['nextOffset']
 for name in totals:totals[name]+=result[name]
guarded=[]
for identity in sorted(approved_old):
 guarded.append(guarded_upgrade(api,identity,initial16[identity],initial17[identity],selection['dataset'],intents,checkpoint,eligible=True,scope=upgrade_scope))
normalized=0
for product in new:
 # The first 80 published records and any manually edited historical draft are preserved.
 if product['id']in public80:continue
 if product.get('brand','').strip().casefold()not in ['genel markalar','markasız','markasiz','diğer','diger']:continue
 editor=api('products/'+product['id']+'/editor');record=editor['record'];current=record['data']
 if current.get('brand','').strip().casefold()not in ['genel markalar','markasız','markasiz','diğer','diger']:continue
 # Only this importer's exact newly created initial record can receive the generic-brand cleanup.
 fresh_initial=(record['version']==1 and record['publishedVersion']==0 or record['version']==record['publishedVersion']==2 and product['id']not in before_ids)and fingerprint(canonical_data(current))==fingerprint(initial17[product['id']])
 if not fresh_initial:continue
 if product['id']in old_ids and not(product['id']in approved_old and product['id']not in before_ids and record['version']==record['publishedVersion']==2):continue
 updated=normalize_generic_brand(canonical_data(current))
 if fingerprint(updated)==fingerprint(canonical_data(current)):continue
 saved=api('products/'+product['id'],{'version':record['version'],'data':updated},'PUT')
 if record['publishedVersion']>0:
  fresh=api('products/'+product['id']+'/editor')['record'];assert fresh['version']==saved['data']['version']and fingerprint(canonical_data(fresh['data']))==fingerprint(updated),'CONCURRENT_PRODUCT_DRAFT_REQUIRES_REVIEW'
  api('products/'+product['id']+'/publish',{'version':fresh['version']})
 normalized+=1
final=session.get(BASE+'/api/catalog',timeout=(12,60)).json();actual={p['id']for p in final['products']};assert actual==expected,('VISIBLE_PRODUCT_SET_MISMATCH',len(actual),len(expected));assert all(p['stockKnown']is False and p['stockQuantity']is None for p in final['products'])
assert all(p.get('brand','').casefold()not in ['genel markalar','markasız','markasiz','diğer','diger']for p in final['products']),'UNKNOWN_BRAND_ADVERTISED'
protected_after={row['id']:row for row in api('products')['data']if row['id']in protected_ids}if protected_ids else{}
assert fingerprint(protected_before)==fingerprint(protected_after),'PROTECTED_PUBLIC_RECORD_CHANGED'
guard_counts={action:sum(row['action']==action for row in guarded)for action in ['upgraded','resumed','already_current','preserve']}
result={'genericBrandsNotInvented':True,'normalizedGenericBrands':normalized,'base':BASE,'release':package['release'],'dataset':selection['dataset'],'loadedNew':len(new),'sourceDetails':selection['sourceProducts'],'deferred':selection['sourceProducts']-len(new),'visibleNew':len(actual),'oldSupplierProductsVisible':False,'stockNotInvented':True,'idempotent':True,'realPayments':False,'counts':totals,'guardedOldHeldUpgrades':{'baseline':baseline_proof,'approvedCandidates':len(approved_old),'protectedPublished80':len(public80),'protectedExistingRecords':len(protected_ids),'protectedRecordsSha256':fingerprint(protected_after),'counts':guard_counts,'records':guarded,'targetInitialSha256':fingerprint({key:initial17[key]for key in sorted(approved_old)}),'projectionPhpSha256':hashlib.sha256((private/'sexogate-catalog.php').read_bytes()).hexdigest(),'localizationPhpSha256':hashlib.sha256((private/'localization.php').read_bytes()).hexdigest(),'helperSha256':hashlib.sha256((ROOT/'scripts/native_marketplace_import_guard.py').read_bytes()).hexdigest()}};(ROOT/('.local/native-marketplace-import-'+suffix+'.json')).write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result))
