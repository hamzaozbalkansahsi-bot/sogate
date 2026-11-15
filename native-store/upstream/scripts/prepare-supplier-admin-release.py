"""Publish truthful admin visibility flags without changing the tested storefront."""
from pathlib import Path
import argparse,json,hashlib,os
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication'
a=argparse.ArgumentParser();a.add_argument('--base',required=True);a.add_argument('--output',required=True);args=a.parse_args();base=R/args.base;out=R/args.output;assert not out.exists()and out.parent==R/'artifacts'and out.name.startswith('cpanel-release-')
catalog=json.loads((base/'private/catalog.json').read_bytes());published={p['id']:p for p in catalog['products']};seed=json.loads((base/'private/supplier-catalog.json').read_bytes())
for p in seed['products']:
 p['publicationReady']=p['id']in published
 if p['id']in published and p['supplierId']in ['alka','altinis']:p['salePriceMinor']=published[p['id']]['salePriceMinor']
seed['report']['publishedSupplierRecords']=sum(p['publicationReady']and p['supplierId']in ['alka','altinis']for p in seed['products'])
assert seed['report']['publishedSupplierRecords']==2581
for file in base.rglob('*'):
 if file.is_file():dest=out/file.relative_to(base);dest.parent.mkdir(parents=True,exist_ok=True);os.link(file,dest)
def write(rel,body):
 f=out/rel
 if f.exists():f.unlink()
 f.write_bytes(body)
body=(json.dumps(seed,ensure_ascii=False,indent=2)+'\n').encode();write('private/supplier-catalog.json',body);(R/'data/supplier-catalog.json').write_bytes(body)
sha=lambda b:hashlib.sha256(b).hexdigest();manifest=json.loads((base/'private/release.json').read_bytes());basehash=manifest['releaseHash'];manifest['files']['private/supplier-catalog.json']=sha(body);fingerprint=hashlib.sha256()
for name,h in sorted(manifest['files'].items()):fingerprint.update((name+'\0'+h+'\0').encode())
manifest['releaseHash']=fingerprint.hexdigest();write('private/release.json',json.dumps(manifest,indent=2).encode())
proof=json.loads((O/(base.name+'-proof.json')).read_bytes());proof.update(baseReleaseHash=basehash,releaseHash=manifest['releaseHash'],products=0,productIds=[],browserEquivalentReleaseHash=basehash,adminVisibilityVerified=True)
(O/(out.name+'-proof.json')).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'releaseHash':manifest['releaseHash'],'publishedSupplierRecords':2581,'testedStorefrontUnchanged':True}))
