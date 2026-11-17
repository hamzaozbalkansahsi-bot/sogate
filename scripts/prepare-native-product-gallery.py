#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-product-gallery.py
# Açıklama   : Gerçek görsel inceleme kararlarını kaynakla eşleştirerek ek galeri kaydını hazırlar.
import hashlib,json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
TARGET=Path('D:/sexogate-local-artifacts-20261114/private-installs/product-gallery-20261117')
REVIEW_FILES=['product-gallery-review-root.json','product-gallery-review-ui-agent.json','product-gallery-review-security-agent.json','product-gallery-review-catalog-agent.json']
DATASET='057fb50f7d5887fee341e3d5b4a3dd64'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
 manifest_path=TARGET/'manifest.json';manifest=json.loads(manifest_path.read_text('utf8'))
 assert manifest.get('sourceDataset')==DATASET and manifest.get('state')=='complete' and len(manifest['products'])==803,'GALLERY_DOWNLOAD_INCOMPLETE'
 sheets={s['file']:s for s in manifest['sheets']};viewed=set();decisions={};reports={}
 for name in REVIEW_FILES:
  path=ROOT/'.local'/name;review=json.loads(path.read_text('utf8'));reports[name]=sha(path)
  for sheet in review['sheets']:
   key=sheet['file'];assert key in sheets and key not in viewed,'GALLERY_REVIEW_SHEET_MISMATCH'
   image_file=TARGET/'review-sheets'/key;actual=sheets[key]
   assert sheet['sha256']==actual['sha256']==sha(image_file),'GALLERY_REVIEW_SHEET_CHANGED'
   sidecar=image_file.with_suffix('.jpg.json');detail=json.loads(sidecar.read_text('utf8'))
   assert detail==actual and (not sheet.get('sidecarSha256')or sheet['sidecarSha256']==sha(sidecar)),'GALLERY_REVIEW_SIDECAR_CHANGED'
   rows=sheet.get('decisions',sheet.get('images'));assert isinstance(rows,list)and len(rows)==len(actual['images']),'GALLERY_REVIEW_NOT_COMPLETE'
   positions=set()
   for row in rows:
    index=row['position'];assert type(index)is int and index not in positions and 0<=index<len(actual['images']),'GALLERY_REVIEW_POSITION_INVALID';positions.add(index)
    image_sha=row.get('imageSha256',row.get('sha256'));assert image_sha==actual['images'][index]['sha256']and image_sha not in decisions,'GALLERY_REVIEW_IMAGE_MISMATCH'
    assert row['decision']in['approve','approved','hold']and row.get('reason'),'GALLERY_REVIEW_DECISION_REQUIRED'
    decisions[image_sha]={'approved':row['decision']in['approve','approved'],'reason':row['reason'],'sheet':key,'position':index}
   viewed.add(key)
 assert viewed==set(sheets),'GALLERY_SHEETS_NOT_ALL_VIEWED'
 registry={'schema':1,'sourceDataset':DATASET,'products':{}};slots=Counter();assets=set();before=json.loads((ROOT/'.local/native-product-gallery-public-before.json').read_text('utf8'))
 for slot in manifest['slots']:
  if slot['review']!='pending_human_review':continue
  asset=manifest['assets'][slot['sourceUrl']];assert asset.get('state')=='ready','GALLERY_ASSET_UNAVAILABLE'
  original=manifest['products'][slot['productId']]
  if asset['sha256']in original['baseHashes'].values():slots['existing_base_excluded']+=1;continue
  decision=decisions.get(asset['sha256']);assert decision is not None,'GALLERY_PHOTO_NOT_VIEWED'
  if not decision['approved']:slots['held']+=1;continue
  file=TARGET/'media'/asset['file'];assert not file.is_symlink()and sha(file)==asset['sha256'],'GALLERY_APPROVED_ASSET_CHANGED'
  row=registry['products'].setdefault(slot['productId'],{**original,'images':[]})
  if any(i['sha256']==asset['sha256']for i in row['images']):slots['duplicate_slot_excluded']+=1;continue
  row['images'].append({**{key:asset[key]for key in['sha256','file','mime','width','height']},'sourceSha256':slot['sourceSha256'],'sourceIndex':slot['sourceIndex'],'sourceUrl':slot['sourceUrl'],'approved':True})
  slots['added']+=1;assets.add(asset['sha256'])
 for row in registry['products'].values():row['images'].sort(key=lambda item:item['sourceIndex'])
 output=ROOT/'native-store/storefront/product-gallery-data.json';dump(output,registry)
 after_counts=Counter(len(images)+len(registry['products'].get(pid,{}).get('images',[]))for pid,images in before['byProduct'].items())
 report={'schema':1,'sourceDataset':DATASET,'manifestSha256':sha(manifest_path),'registrySha256':sha(output),'humanVisualReview':True,'sheetsViewed':len(viewed),'photosViewed':len(decisions),'approvedHashes':sorted(assets),'reviewReports':reports,'productsExtended':len(registry['products']),'addedImageSlots':slots['added'],'uniqueApprovedAssets':len(assets),'heldImageSlots':slots['held'],'duplicateSlotsExcluded':slots['duplicate_slot_excluded'],'previousBasePhotosNeverReadded':True,'beforeDistribution':before['imageCounts'],'afterDistribution':dict(sorted(after_counts.items())),'sourceCatalogChanged':False,'mediaBytesChanged':False,'publishedOrUploaded':False}
 dump(ROOT/'.local/native-product-gallery-review.json',report)
 print(json.dumps({k:v for k,v in report.items()if k not in['approvedHashes','reviewReports']},ensure_ascii=False))

if __name__=='__main__':main()
