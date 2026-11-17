#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-http.py
# Açıklama   : Yeni katalog/iade yayınının alt yolunu, özel dosya ve erişim sınırlarını gerçek HTTPS üzerinden sınar.
import hashlib,json,os,re
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');SCOPE=os.environ.get('SEXOGATE_MARKETPLACE_SCOPE','local');assert SCOPE in ['local','preview','remote'];assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
remote=BASE.startswith('https://sexogate.com');session=requests.Session();session.verify=True if remote else str(Path(json.loads((ROOT/'.local/native-stage-local.json').read_text('utf8'))['base'])/'tls.pem');package=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'));selection=json.loads((ROOT/'.local/native-marketplace-selection.json').read_text('utf8'));data=json.loads((Path(selection['path'])/'catalog-data.json').read_text('utf8'));expected=sum(bool(p['visualApprovedIndices'])and not p['eligibilityHold']and bool(p['salePriceMinor'])for p in data['products'][2194:]);routes={}
for path,status in [('/',200),('/api/catalog',200),('/api/deployment-status',200),('/app/config.local.json',403 if remote else 404),('/.env',403 if remote else 404),('/private/accounts.sqlite',404),('/site.webmanifest',200),('/apple-touch-icon.png',200),('/api/admin/return-center',401),('/yonetim/iade-merkezi',200),('/?page=return-center&lang=tr',200)]:
 r=session.get(BASE+path,timeout=(12,60));assert r.status_code==status,(path,r.status_code);routes[path]=status
 if path=='/api/deployment-status':health=r.json();assert health['release']==package['release']and health['sourceProducts']==len(data['products'])and health['products']==expected and health['checkoutEnabled']is False;assert 'no-store'in r.headers.get('Cache-Control','')
 if path=='/':assert "script-src 'self'"in r.headers.get('Content-Security-Policy','')and "'unsafe-eval'"not in r.headers.get('Content-Security-Policy','')
 if path=='/site.webmanifest':manifest=r.json();mount=BASE.split('://',1)[1].split('/',1)[1];assert manifest['scope']=='/'+mount+'/'and manifest['start_url']=='/'+mount+'/'
 if path=='/?page=return-center&lang=tr':assert 'no-store'in r.headers.get('Cache-Control','')and re.search(r'<meta[^>]+name="robots"[^>]+content="noindex,(?:no)?follow"',r.text)
 if path=='/yonetim/iade-merkezi':assert 'no-store'in r.headers.get('Cache-Control','')and r.headers.get('X-Robots-Tag')=='noindex, nofollow'
r=session.get(BASE+'/api/returns',timeout=(12,60));assert r.status_code==200 and 'no-store'in r.headers.get('Cache-Control','');state=r.json();assert not state['orders']and state['signedIn']is False
headers={'Origin':BASE.split('/test')[0],'X-CSRF-Token':state['csrfToken']}
assert session.post(BASE+'/api/returns/order',json={'lookupToken':'0'*64},headers=headers,timeout=(12,60)).status_code==404
assert session.post(BASE+'/api/returns/order',json={'lookupToken':'0'*64},headers={**headers,'Origin':'https://invalid.example'},timeout=(12,60)).status_code==403
assert session.get(BASE+'/api/returns/cases/SGR-261116-000000000000',timeout=(12,60)).status_code==403
closed=session.post(BASE+'/api/payments/checkout',json={},headers=headers,timeout=(12,60));assert closed.status_code==409 and closed.json()['error']=='live_sales_not_approved'
gallery=json.loads((ROOT/'native-store/storefront/product-gallery-data.json').read_text('utf8'));assert gallery['sourceDataset']==selection['dataset']and gallery['products'],'GALLERY_APPROVED_REGISTRY_REQUIRED'
public=session.get(BASE+'/api/catalog',timeout=(12,60)).json()['products'];by_id={p['id']:p for p in public};before=json.loads((ROOT/'.local/product-experience-commercial-baseline.json').read_text('utf8'));assert set(by_id)=={p['id']for p in before['products']},'GALLERY_PUBLIC_SET_CHANGED'
def media_suffix(value):
 assert isinstance(value,str)and'/media/'in value,'GALLERY_MOUNT_INVALID'
 return '/media/'+value.split('/media/',1)[1]
for original in before['products']:
 current=by_id[original['id']]
 for key,value in original.items():
  if key!='images':assert current.get(key)==value,('GALLERY_COMMERCIAL_FIELD_CHANGED',original['id'],key)
 expected_images=[media_suffix(v)for v in original['images']]+['/media/'+original['id']+'/gallery/'+v['sha256']for v in gallery['products'].get(original['id'],{}).get('images',[])]
 assert [media_suffix(v)for v in current['images']]==expected_images,('GALLERY_IMAGE_ASSOCIATION_CHANGED',original['id'])
assets={}
for identifier,row in sorted(gallery['products'].items()):
 for image in row['images']:assets.setdefault(image['sha256'],(identifier,image))
assert assets,'GALLERY_NO_APPROVED_ASSETS';samples=list(assets.values())[:24]
for identifier,image in samples:
 route=BASE+'/media/'+identifier+'/gallery/'+image['sha256'];head=session.head(route,timeout=(12,60));assert head.status_code==200 and head.headers.get('Content-Type')==image['mime']and'no-store'in head.headers.get('Cache-Control',''),'GALLERY_HEAD_NOT_PRIVATE'
 photo=session.get(route,timeout=(12,60));assert photo.status_code==200 and hashlib.sha256(photo.content).hexdigest()==image['sha256']and'no-store'in photo.headers.get('Cache-Control',''),'GALLERY_ORIGINAL_BYTES_NOT_SERVED'
identifier,image=samples[0];route=BASE+'/media/'+identifier+'/gallery/'+image['sha256']
assert session.post(route,json={},timeout=(12,60)).status_code==405,'GALLERY_METHOD_NOT_BLOCKED'
assert session.get(BASE+'/media/'+identifier+'/gallery/'+'0'*64,timeout=(12,60)).status_code==404,'GALLERY_UNKNOWN_HASH_PUBLIC'
hidden_id=next(p['id']for p in data['products'][2194:]if p['id']not in by_id)
assert session.get(BASE+'/media/'+hidden_id+'/gallery/'+image['sha256'],timeout=(12,60)).status_code==404,'GALLERY_HIDDEN_PRODUCT_PUBLIC'
base_hash=next(iter(gallery['products'][identifier]['baseHashes'].values()))
assert session.get(BASE+'/media/'+identifier+'/gallery/'+base_hash,timeout=(12,60)).status_code==404,'GALLERY_BASE_OR_REJECTED_IMAGE_REINTRODUCED'
result={'base':BASE,'release':package['release'],'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'visibleNew':expected,'routes':routes,'privatePathsBlocked':True,'guestOrderOwnership':True,'returnCsrfAndOrigin':True,'returnsNoStoreNoindex':True,'adminProtected':True,'checkoutClosed':True,'realPayments':False}
result.update(reviewedGallery=True,galleryCommercialFieldsUnchanged=True,galleryAllAssociationsChecked=True,galleryPrivateNoStore=True,galleryOwnershipChecked=True,galleryOriginalSamples=len(samples),galleryProductsExtended=len(gallery['products']),galleryApprovedAssets=len(assets),galleryRegistrySha256=hashlib.sha256((ROOT/'native-store/storefront/product-gallery-data.json').read_bytes()).hexdigest())
(ROOT/('.local/native-marketplace-http-'+SCOPE+'.json')).write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result))
