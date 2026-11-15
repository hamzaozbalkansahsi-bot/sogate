"""Seal only current social content/wordmark changes on the exact audited live base."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-keywords-20261113'
B=R/'artifacts/cpanel-release-mobile-layout-20261113-r2'
O=R/'artifacts/cpanel-release-social-keywords-20261113-r1'
BASE='784eb7a7521e47352e3d5ee448cb5e13d406fff6c17969c0d90317f724a84130'
VERSION='social-keywords-20261113-v6'

def load(n,path):
 s=importlib.util.spec_from_file_location(n,R/path);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def changes_for(base,bank=None):
 cache=load('social_keyword_cache','scripts/prepare-social-role-release-20261112.py');cache.VERSION=VERSION
 assets=['assets/brand/logo-horizontal.svg','assets/brand/logo-horizontal-white.svg','assets/brand/logo-with-slogan.svg','wordmark.svg','assets/brand/social-logo.png','assets/brand/social-logo-white.png','assets/brand/share-cover.jpg']
 changes={'public/'+n:(R/'web'/n).read_bytes()for n in assets}
 changes.update({'private/'+n:(R/'hosting'/n).read_bytes()for n in ['social-campaigns.php','social-engine.php','social-media.php','social-worker.php']})
 for n in cache.CACHE_FILES:
  value=cache.cached(n,base['all_bytes'][n])
  if value!=base['all_bytes'][n]:changes[n]=value
 ui=base['all_bytes']['public/admin-social.js'].decode('utf-8')
 needle="${post?.format==='video'?"
 assert ui.count(needle)==1
 ui=ui.replace(needle,"${p.keywords?.length?`<p dir=\"auto\"><strong>Anahtar kelimeler:</strong> ${esc(p.keywords.join(' · '))}</p>`:''}"+needle)
 changes['public/admin-social.js']=ui.encode('utf-8')
 admin=changes.get('public/admin.js',base['all_bytes']['public/admin.js'])
 admin=re.sub(rb'admin-social\.js\?v=[A-Za-z0-9_-]+',b'admin-social.js?v='+VERSION.encode(),admin)
 changes['public/admin.js']=admin
 return {n:b for n,b in changes.items()if base['all_bytes'].get(n)!=b}

def main():
 E.mkdir(parents=True,exist_ok=True);d=load('social_keyword_backend','scripts/deploy-cpanel.py');base=d.load_release(B)
 assert base['manifest']['releaseHash']==BASE
 health=d.CpanelBackend(allow_writes=False).public_health();assert health['releaseHash']==BASE and health['mediaReady']is True
 expected=changes_for(base)
 assert not O.exists(),'Immutable candidate already exists; use a new version for changed bytes'
 for name in sorted(set(base['manifest']['files'])|set(expected)):
  target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
  if name in expected:target.write_bytes(expected[name])
  else:os.link(B/name,target)
 hashes={n:d.sha256((O/n).read_bytes())for n in sorted(set(base['manifest']['files'])|set(expected))};fp=hashlib.sha256()
 for n,digest in hashes.items():fp.update((n+'\0'+digest+'\0').encode())
 (O/'private/release.json').write_text(json.dumps({**base['manifest'],'releaseHash':fp.hexdigest(),'files':hashes},indent=2)+'\n')
 new=d.load_release(O)
 assert all(new['all_bytes'].get(n)==body for n,body in base['all_bytes'].items()if n not in expected and n!='private/release.json')
 prior=json.loads((R/'artifacts/mobile-layout-20261113/media.json').read_bytes());assert prior['passed']and prior['releaseHash']==BASE
 proof={'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':BASE,'releaseHash':new['manifest']['releaseHash'],'changedFiles':sorted(expected),'assetCacheVersion':VERSION,'publicProducts':health['products'],'expectedCheckoutEnabled':health['checkoutEnabled'],'catalogueCommerceCustomerStorageAndMediaByteExact':True}
 (E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

if __name__=='__main__':main()
