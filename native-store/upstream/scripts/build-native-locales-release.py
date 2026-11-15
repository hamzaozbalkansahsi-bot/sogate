"""Bind the reviewed locale delta to the current live catalogue and commerce."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,urllib.request
R=Path(__file__).resolve().parents[1];E=R/os.environ.get('NODENO_RELEASE_EVIDENCE','artifacts/target-locales-20261111')
spec=importlib.util.spec_from_file_location('native_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
SOURCE=R/os.environ.get('NODENO_RELEASE_SOURCE','artifacts/cpanel-release-target-locales-source-20261111');source=d.load_release(SOURCE)
B=R/os.environ.get('NODENO_RELEASE_BASE','artifacts/cpanel-release-vitrine-20261111');base=d.load_release(B)
health=json.load(urllib.request.urlopen('https://nodenohome.com/api/health',timeout=45))
assert health['releaseHash']==base['manifest']['releaseHash']and health['checkoutEnabled']is True and health['mediaReady']is True
coverage=json.loads((E/'coverage.json').read_bytes());assert coverage['complete']is True and coverage['missingCount']==0
O=R/os.environ.get('NODENO_RELEASE_OUTPUT','artifacts/cpanel-release-target-locales-20261111');assert not O.exists()
assert all(p.resolve().is_relative_to((R/'artifacts').resolve())for p in [E,SOURCE,B,O])
PRICING=R/'artifacts/target-locales-20261111'
pricing_review=json.loads((PRICING/'pricing-refresh-review.json').read_bytes())
fresh_prices=json.loads((R/'data/catalog-prices.json').read_bytes())
previous_prices=json.loads((PRICING/'pricing-before-refresh/catalog-prices.json').read_bytes())
assert hashlib.sha256((R/'data/catalog-prices.json').read_bytes()).hexdigest()==pricing_review['sourceSha256']
assert hashlib.sha256((PRICING/'pricing-before-refresh/catalog-prices.json').read_bytes()).hexdigest()==pricing_review['previousSha256']
financial_ids={r['productId']for r in previous_prices['products']}
for release,pricing in [(base,previous_prices),(source,fresh_prices)]:
 products={p['id']:p for p in json.loads(release['all_bytes']['private/catalog.json'])['products']}
 for row in pricing['products']:
  expected=row.get('salePriceMinor')if row['status']=='verified'else None
  assert products[row['productId']].get('salePriceMinor')==expected,'source/live price evidence mismatch'
def catalog_facts(body):
 value=json.loads(body);value['meta'].pop('releaseHash',None)
 # Source builds re-read supplier offers and derive historical price badges.
 # None of those financial fields or build provenance enter this UI delta:
 # the entire approved live catalogue is retained byte for byte below.
 for product in value['products']:
  if product['id']in financial_ids:
   for key in ['salePrice','salePriceMinor','currency','priceUpdatedAt','previousPriceMinor','discountPercent']:product.pop(key,None)
 for key in ['pricedProducts','unpricedProducts','discountedProducts']:value['meta']['pricing'].pop(key,None)
 for key in ['furnitureSetsVersion','supplierCatalogVersion','supplierPublication']:value['meta'].pop(key,None)
 if isinstance(value['meta'].get('priceRefresh'),dict):value['meta']['priceRefresh'].pop('effectiveAt',None)
 return value
assert catalog_facts(source['all_bytes']['private/catalog.json'])==catalog_facts(base['all_bytes']['private/catalog.json']),'nonfinancial catalogue facts changed'
retained=['private/catalog.json','private/config.json','private/media.json','private/media-approved.json','private/door-catalog.json','private/cabinet-fronts.json','private/supplier-details.json','private/supplier-details.bin','private/supplier-media-approved.json']
for name in retained[1:]:
 if name.endswith('.json'):assert json.loads(source['all_bytes'][name])==json.loads(base['all_bytes'][name]),name
 else:assert source['all_bytes'][name]==base['all_bytes'][name],name
public_names={p.name for p in (R/'web').glob('*.js')}|{p.name for p in (R/'web').glob('*.css')}|{'index.php','.htaccess'}
private_names={p.name for p in (R/'hosting').glob('*.php')}|{'index.html'}
changes={}
for name,body in source['all_bytes'].items():
 if name=='private/release.json':continue
 permitted=(name.startswith('public/')and(name[7:]in public_names or name.startswith('public/locales/'))or name.startswith('private/')and(name[8:]in private_names or name.startswith('private/locale.')or name.startswith('private/site-documents.')))
 if permitted and body!=base['all_bytes'].get(name):changes[name]=body
assert {'private/index.html','public/app.js','public/styles.css','public/locale-runtime.js'}<=set(changes)
assert all(not name.startswith(('public/assets/','private/catalog.json','private/config.json'))for name in changes)
for name in sorted(set(base['manifest']['files'])|set(changes)):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
files={p.relative_to(O).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in O.rglob('*')if p.is_file()};fp=hashlib.sha256()
for name,digest in sorted(files.items()):fp.update((name+'\0'+digest+'\0').encode())
manifest={**base['manifest'],'releaseHash':fp.hexdigest(),'files':dict(sorted(files.items()))};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
assert (O/'private/catalog.json').read_bytes()==base['all_bytes']['private/catalog.json']
for name in retained:assert (O/name).read_bytes()==base['all_bytes'][name],name
proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':base['manifest']['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'sourcePackage':SOURCE.relative_to(R).as_posix(),'nativeCoverageSha256':hashlib.sha256((E/'coverage.json').read_bytes()).hexdigest(),'catalogueMediaPricesAndCommerceUnchanged':True,'checkoutEnabledBefore':True,'retainedLiveCatalogueSha256':hashlib.sha256(base['all_bytes']['private/catalog.json']).hexdigest(),'unpublishedSourcePriceChanges':pricing_review['changes']}
(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
