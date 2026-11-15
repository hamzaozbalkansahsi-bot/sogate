"""Build complete source-bound content before translation and publication."""
from pathlib import Path
import hashlib,importlib.util,json,collections
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion';OUT=O/'publication';OUT.mkdir(exist_ok=True)
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('supplier_publication','lib/supplier_publication.py');imp=module('supplier_import','scripts/import-wood-suppliers.py')
source=O/'download-catalog.json';raw=json.loads(source.read_bytes())['products'];parents={str(p.get('sourcePageId')):p for p in raw if not p.get('parentSourcePageId')};rows=[]
for p in raw:
 if p.get('parentSourcePageId'):p=m.inherit_variant(p,parents[str(p['parentSourcePageId'])])
 html=None
 if p['supplierId']=='altinis':html=imp.read_archive(R/p['evidence']['file']).decode('utf8')
 content=m.public_content(p,html);policy=m.quantity_policy(p)
 rows.append({'id':p['id'],'code':p['code'],'supplierId':p['supplierId'],'sourceCode':p['sourceCode'],'sourceUrl':p['sourceUrl'],'sourcePageId':p.get('sourcePageId'),'parentSourcePageId':p.get('parentSourcePageId'),'rawTitle':p['title'],'title':content['title'],'paragraphs':content['paragraphs'],'dimensions':content['dimensions'],'quantityPolicy':policy,'sourceCategories':p['categories'],'merchantCategory':p['merchantCategory'],'variantAttributes':p.get('variantAttributes',[]),'variants':p.get('variants',[]),'images':p['images'],'priceStatus':p['priceStatus'],'sourcePriceMinor':p['sourcePriceMinor'],'salePriceMinor':p['salePriceMinor'],'sourceEvidence':p.get('visiblePriceEvidence')or p['evidence'],'rawSpecs':p['specs']})
report={'products':len(rows),'suppliers':dict(collections.Counter(p['supplierId']for p in rows)),'paragraphs':sum(len(p['paragraphs'])for p in rows),'dimensions':sum(bool(p['dimensions'])for p in rows),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'titleCollisions':sum(n>1 for n in collections.Counter(p['title']for p in rows).values()),'publicationReady':False}
(OUT/'content-tr.json').write_text(json.dumps({'products':rows,'report':report},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(report))
