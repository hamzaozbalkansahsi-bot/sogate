"""Promote reviewed caption-rule corrections and seal a media-only live delta."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/front-image-integrity-20261115'
B=R/'artifacts/cpanel-release-social-keywords-20261113-r1';O=R/'artifacts/cpanel-release-front-rules-20261115-r1'
BASE='8eb5b0a704f94bc5227111b7f144ea7683bf11dc8b417332e6c1ee507b02ae78'
sha=lambda b:hashlib.sha256(b).hexdigest()

def load(n,path):
 s=importlib.util.spec_from_file_location(n,R/path);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def promote():
 proof=json.loads((E/'rule-removal.json').read_bytes());visual=json.loads((E/'visual-review.json').read_bytes())
 assert visual['passed']is True and visual['proofSha256']==sha((E/'rule-removal.json').read_bytes())
 assert visual['imagesInspected']==proof['imagesChanged']==len(proof['replacements'])
 for row in visual['sheets']:assert row['inspected']is True and sha((R/row['path']).read_bytes())==row['sha256']
 old=json.loads((E/'cabinet-fronts-before.json').read_bytes());data=json.loads((E/'cabinet-fronts-candidate.json').read_bytes())
 for a,b in zip(old['products'],data['products']):assert {k:v for k,v in a.items()if k!='assetHashes'}=={k:v for k,v in b.items()if k!='assetHashes'}
 assert old['sourceDocuments']==data['sourceDocuments'] and len(old['assets'])==len(data['assets'])
 archive=E/'original-published-assets';archive.mkdir(exist_ok=True)
 for before,after in proof['replacements'].items():
  source=(R/'web'/old['assets'][before]['path'].lstrip('/')).resolve();target=(archive/(before+'.png')).resolve()
  assert source.is_relative_to(R/'web/assets/fronts') and target.is_relative_to(archive.resolve())
  if source.exists():
   assert sha(source.read_bytes())==before
   if target.exists():assert target.read_bytes()==source.read_bytes();source.unlink()
   else:source.rename(target)
  assert sha(target.read_bytes())==before
  new=(E/'candidates'/(after+'.png')).read_bytes();assert sha(new)==after
  (R/'web'/data['assets'][after]['path'].lstrip('/')).write_bytes(new)
  data['assets'][after].update(reviewRequired=False,captionRasterInkExcluded=True)
 ocr=R/'artifacts/cabinet-fronts-2026/ocr-audit.json';original=E/'ocr-audit-before.json'
 if not original.exists():original.write_bytes(ocr.read_bytes())
 rows=json.loads(original.read_bytes())
 for row in rows:
  if row['sha256']in proof['replacements']:
   before=row['sha256'];row.update(sha256=proof['replacements'][before],sourceSha256=before,verificationMethod='inherited-ocr-no-new-dark-pixels',pixelEvidenceSha256=visual['proofSha256'])
 ocr.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 review=data['review'];review.update(contactSheetsInspected=True,ocrSha256=sha(ocr.read_bytes()),captionRuleCleanup={'proofSha256':visual['proofSha256'],'images':len(proof['replacements']),'nativePhotoAndAlphaStreamsUnchanged':True,'outsideRulePixelsExact':True,'noNewDarkPixels':True,'ocrRerun':False})
 for n in range(1,5):
  path=E/f'rules-review-{n}.png';review['contactSheets'].append({'path':path.relative_to(R).as_posix(),'sha256':sha(path.read_bytes())})
 data.update(publicationReady=True,reviewRequired=False)
 (R/'data/cabinet-fronts.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def changes_for(base,bank=None):
 body=(R/'data/cabinet-fronts.json').read_bytes();catalog=json.loads(base['all_bytes']['private/catalog.json']);catalog['meta']['frontCatalogVersion']=sha(body)
 result={'private/cabinet-fronts.json':body,'private/catalog.json':(json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+'\n').encode()}
 d=json.loads(body);proof=json.loads((E/'rule-removal.json').read_bytes())
 result.update({'public'+d['assets'][h]['path']:(E/'candidates'/(h+'.png')).read_bytes()for h in proof['replacements'].values()})
 return result

def main():
 d=load('front_rules_backend','scripts/deploy-cpanel.py');base=d.load_release(B);assert base['manifest']['releaseHash']==BASE
 health=d.CpanelBackend(allow_writes=False).public_health();assert health['releaseHash']==BASE and health['mediaReady']is True
 assert not O.exists(),'Immutable release exists'
 promote();expected=changes_for(base);mapping=json.loads((E/'rule-removal.json').read_bytes())['replacements'];removed={'public/assets/fronts/'+h+'.png'for h in mapping}
 names=(set(base['manifest']['files'])|set(expected))-removed
 for name in sorted(names):
  target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
  if name in expected:target.write_bytes(expected[name])
  else:os.link(B/name,target)
 hashes={n:sha((O/n).read_bytes())for n in sorted(names)};fp=hashlib.sha256()
 for n,h in hashes.items():fp.update((n+'\0'+h+'\0').encode())
 (O/'private/release.json').write_text(json.dumps({**base['manifest'],'releaseHash':fp.hexdigest(),'files':hashes},indent=2)+'\n')
 new=d.load_release(O)
 assert all(new['all_bytes'].get(n)==b for n,b in base['all_bytes'].items()if n not in expected and n not in removed and n!='private/release.json')
 oldcat=json.loads(base['all_bytes']['private/catalog.json']);newcat=json.loads(new['all_bytes']['private/catalog.json']);oldcat['meta']['frontCatalogVersion']=newcat['meta']['frontCatalogVersion'];assert oldcat==newcat
 record={'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':BASE,'releaseHash':new['manifest']['releaseHash'],'changedFiles':sorted(expected),'removedManifestFiles':sorted(removed),'imagesCorrected':len(mapping),'publicProducts':health['products'],'expectedCheckoutEnabled':health['checkoutEnabled'],'pricesProductsAndPersistentCustomerStoragePreserved':True}
 (E/'release.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))

if __name__=='__main__':main()
