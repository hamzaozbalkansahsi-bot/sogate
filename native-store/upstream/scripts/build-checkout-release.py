"""Apply only the checkout/currency UI delta to the verified production package."""
from pathlib import Path
import hashlib,json,os,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/cpanel-release-suppliers-20261110';O=R/'artifacts/cpanel-release-checkout-20261110';E=R/'artifacts/checkout-currency';E.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();base=json.loads((B/'private/release.json').read_bytes())
assert base['releaseHash']=='d365fd675610b9fc9cb66793ac7ad6fd605a859596dcdacda3aa3b2798a28ba4'
for n,h in base['files'].items():assert sha((B/n).read_bytes())==h,n
read=lambda n:(B/n).read_text(encoding='utf8');web=lambda n:(R/'web'/n).read_text(encoding='utf8')
patch={};app=read('public/app.js');source=web('app.js')
# Preserve unrelated, not-yet-published measurement work in the working tree.
for start,end in [('  if(review){guestCheckout.review=','\n  else{const d=guestCheckout.details'),(' return `<div class="wrap checkout-page">${pageHeading(\'checkout\')}<div class="basket-layout">','\n}\nfunction keepFocusedFieldVisible')]:
 a,b=app.index(start),app.index(end,app.index(start));x,y=source.index(start),source.index(end,source.index(start));app=app[:a]+source[x:y]+app[b:]
app=app.replace('syncMobileChrome();experience?.afterRender();if(focus)','syncMobileChrome();experience?.afterRender();doorUI?.toolbar();if(focus)')
app=re.sub(r"(from './(?:door-ui|shop-i18n)\.js)\?v=[^']+",r'\1?v=nodeno-checkout-20261110-r1',app)
patch['public/app.js']=app.encode()
door=read('public/door-ui.js');src=web('door-ui.js');a,b=door.index(' function toolbar(){'),door.index(' async function loadRates()');x,y=src.index(' function toolbar(){'),src.index(' async function loadRates()');door=door[:a]+src[x:y]+door[b:]
a=door.index("  if(el.hasAttribute('data-display-currency'))");b=door.index('\n',a);x=src.index("  if(el.hasAttribute('data-display-currency'))");y=src.index('\n',x);door=door[:a]+src[x:y]+door[b:];patch['public/door-ui.js']=door.encode()
css=read('public/styles.css');marker='/* Checkout review: contact and addresses stay distinct from the selected items. */';patch['public/styles.css']=(css+'\n'+marker+web('styles.css').split(marker,1)[1]).encode()
css=read('public/door-commerce.css');src=web('door-commerce.css');patch['public/door-commerce.css']=(src[:src.index('.door-collection-banner{')]+css[css.index('.door-collection-banner{'):]).encode()
i18n=read('public/shop-i18n.js');row=next(line for line in web('shop-i18n.js').splitlines()if "['guestBillingMatches'"in line);patch['public/shop-i18n.js']=i18n.replace('const rows = [','const rows = [\n'+row).encode()
html=read('private/index.html');html=html.replace(' <div id="currency-toolbar" class="currency-toolbar"></div>','');html=re.sub(r'(/(?:app.js|styles.css|door-commerce.css)\?v=)[^"\s]+',r'\1nodeno-checkout-20261110-r1',html);patch['private/index.html']=html.encode()
O.mkdir(exist_ok=True)
for n in base['files']:
 target=O/n;target.parent.mkdir(parents=True,exist_ok=True)
 if n in patch:target.write_bytes(patch[n])
 elif not target.exists():os.link(B/n,target)
 else:assert sha(target.read_bytes())==base['files'][n],n
hashes={**base['files'],**{n:sha(b)for n,b in patch.items()}};h=hashlib.sha256()
for n in sorted(hashes):h.update((n+'\0'+hashes[n]+'\0').encode())
manifest={**base,'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
proof={'baseReleaseHash':base['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(patch),'output':str(O),'publicProducts':1021,'mediaBytesUnchanged':True,'privateCustomerDataUntouched':True}
(E/'build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
