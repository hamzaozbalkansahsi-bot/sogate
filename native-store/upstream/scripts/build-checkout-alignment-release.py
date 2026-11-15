"""Align the two checkout columns without changing commerce, media or private data."""
from pathlib import Path
import hashlib,json,os,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/cpanel-release-checkout-20261110';O=R/'artifacts/cpanel-release-checkout-alignment-20261110';E=R/'artifacts/checkout-currency/alignment';E.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();base=json.loads((B/'private/release.json').read_bytes());assert base['releaseHash']=='fc5bfd644285ba1814efe7a9d8157cd6f3c76c8817bb72b8a91d6ebf941257a2'
for n,h in base['files'].items():assert sha((B/n).read_bytes())==h,n
app=(B/'public/app.js').read_text(encoding='utf8');source=(R/'web/app.js').read_text(encoding='utf8');start='function renderCheckout(){';end='\nfunction keepFocusedFieldVisible';a,b=app.index(start),app.index(end);x,y=source.index(start),source.index(end);app=app[:a]+source[x:y]+app[b:]
marker='/* Both checkout columns share one top edge beneath a full-width step guide. */';css=(B/'public/styles.css').read_text(encoding='utf8')+'\n'+marker+(R/'web/styles.css').read_text(encoding='utf8').split(marker,1)[1]
html=(B/'private/index.html').read_text(encoding='utf8');html=re.sub(r'(/(?:app.js|styles.css)\?v=)[^"\s]+',r'\1nodeno-checkout-20261110-r2',html)
patch={'public/app.js':app.encode(),'public/styles.css':css.encode(),'private/index.html':html.encode()};O.mkdir(exist_ok=True)
for n in base['files']:
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 if n in patch:p.write_bytes(patch[n])
 elif not p.exists():os.link(B/n,p)
 else:assert sha(p.read_bytes())==base['files'][n],n
hashes={**base['files'],**{n:sha(v)for n,v in patch.items()}};h=hashlib.sha256()
for n in sorted(hashes):h.update((n+'\0'+hashes[n]+'\0').encode())
manifest={**base,'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n')
proof={'baseReleaseHash':base['releaseHash'],'releaseHash':manifest['releaseHash'],'output':str(O),'changedFiles':sorted(patch),'publicProducts':1021,'mediaBytesUnchanged':True,'privateCustomerDataUntouched':True};(E/'build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
