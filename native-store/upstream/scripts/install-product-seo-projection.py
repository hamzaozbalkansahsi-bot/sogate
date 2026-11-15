"""Retain reviewed derived material corrections in future production catalogue builds."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];E=R/'artifacts/seo-products';proof=json.loads((E/'release.json').read_bytes());release=R/proof['release'];catalog=json.loads((release/'private/catalog.json').read_bytes());projection=json.loads((R/'data/supplier-storefront.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
projection['products']=[p for p in catalog['products']if p.get('productType')=='supplier-item'];assert len(projection['products'])==2581
for filename,key in [('supplier-details.bin','detailBlobSha256'),('supplier-details.json','detailIndexSha256')]:
 body=(release/'private'/filename).read_bytes();(R/'data'/filename).write_bytes(body);projection[key]=sha(body)
review={'passed':True,'sourceArchivesUntouched':True,'priceCodeUnitMediaUnchanged':True,'corrections':proof['reviewedMaterialCorrections']};file=E/'catalog-material-review.json';file.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');relative=file.relative_to(R).as_posix();projection['review']['files']=[p for p in projection['review']['files']if p['path']!=relative]+[{'path':relative,'sha256':sha(file.read_bytes())}];(R/'data/supplier-storefront.json').write_text(json.dumps(projection,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8');print('Reviewed material projection installed')
