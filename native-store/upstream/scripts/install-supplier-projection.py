"""Retain the approved published catalogue in subsequent ordinary production builds."""
from pathlib import Path
import argparse,json,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication'
a=argparse.ArgumentParser();a.add_argument('--release',required=True);args=a.parse_args();release=R/args.release
sha=lambda b:hashlib.sha256(b).hexdigest()
proof=json.loads((O/(release.name+'-proof.json')).read_bytes());assert proof['publicationReady'] and not proof['held'] and not proof['untranslated']
catalog=json.loads((release/'private/catalog.json').read_bytes());products=[p for p in catalog['products'] if p.get('productType')=='supplier-item'];assert len(products)==2581
sources={p['id']:p for p in json.loads((O/'content-tr.json').read_bytes())['products']}
media=(release/'private/supplier-media-approved.json').read_bytes();index=(release/'private/supplier-details.json').read_bytes();blob=(release/'private/supplier-details.bin').read_bytes()
for name,body in [('supplier-media-approved.json',media),('supplier-details.json',index),('supplier-details.bin',blob)]: (R/'data'/name).write_bytes(body)
for url,row in json.loads(media)['images'].items():
 source=release/'public'/url.lstrip('/');assert sha(source.read_bytes())==row['outputSha256'];dest=R/'web'/url.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists()or sha(dest.read_bytes())!=row['outputSha256']:shutil.copyfile(source,dest)
files=[]
for name in ['media-review/altinis.json','media-review/alka-source-clean.json','media-review/alka-candidates-approved.json','publication-translation-review.json']:
 file=O/name;files.append({'path':file.relative_to(R).as_posix(),'sha256':sha(file.read_bytes())})
data={'schema':1,'publicationReady':True,'testOnly':False,'products':products,'categories':[c for c in catalog['categories']if c['id'].startswith('ahsap-')],'review':{'contactSheetsInspected':True,'files':files},'mediaSha256':sha(media),'detailIndexSha256':sha(index),'detailBlobSha256':sha(blob),'priceBindings':{p['id']:{'sourcePriceMinor':sources[p['id']]['sourcePriceMinor']if p['salePriceMinor']is not None else None}for p in products}}
(R/'data/supplier-storefront.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
print(json.dumps({'productionProjection':len(products),'images':len(json.loads(media)['images']),'categories':len(data['categories'])}))
