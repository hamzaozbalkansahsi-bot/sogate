#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-catalog.py
# Açıklama   : Gerçek kaynak kayıtlarını özel çalışma dosyaları ve incelenmiş kapaklarla derlemeye hazırlar.
import hashlib,json
from native_catalog import LABELS,loc
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
HOME=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-catalog-20261115')
source=HOME/'catalog-source.json';data=json.loads(source.read_text('utf8'));images=json.loads((HOME/'images.json').read_text('utf8'));review=json.loads((HOME/'review/approved.json').read_text('utf8'))
approved={r['id']:r['sha256']for r in review['approved']};buckets={};media={};public_count=0
for product,work in zip(data['products'],data['workbench']):
 assert product['id']==work['id'] and not product['published'] and product['hidden'] and product['stockQuantity']is None
 rows=[{**images[url],'sourceUrl':url}for url in work['sourceImages']if url in images and 'sha256'in images[url]]
 indices=[i for i,row in enumerate(rows)if approved.get(product['id'])==row['sha256']]
 product.update(images=['/media/'+product['id']+'/'+str(i)for i in range(len(rows))],visualApprovedIndices=indices,privateRetailReference=work['source']['retailPriceMinor'])
 product['coverIndex']=indices[0]if indices else 0
 work['media']=rows;work['publicationApproved']=bool(indices)
 for row in rows:media[row['file']]=row
 buckets.setdefault(product['id'].rsplit('_',1)[1][:2],{})[product['id']]=work
 public_count+=bool(indices)and not product['eligibilityHold']and product['salePriceMinor']is not None
dataset=hashlib.sha256(source.read_bytes()+json.dumps(review,sort_keys=True).encode()).hexdigest()[:32]
prepared=HOME/'prepared';prepared.mkdir(exist_ok=True);workdir=prepared/'catalog-workbench';workdir.mkdir(exist_ok=True)
dump=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf8')
for key,value in buckets.items():dump(workdir/(key+'.json'),value)
manifest={'schema':1,'dataset':dataset,'sources':data['sources'],'sourceCategories':data['sourceCategories'],'products':len(data['products']),'reviewedCovers':public_count,'markupPercent':30,'checkoutEnabled':False,'rightsBasis':data['rightsBasis']}
dump(prepared/'catalog-spec-labels.json',{key:loc(LABELS[key])for key in ['materials','dimensions','sizeOptions','colorOptions']})
dump(prepared/'catalog-sources.json',manifest);dump(prepared/'catalog-data.json',{'products':data['products'],'categories':data['categories'],'catalogOrigin':data['sourceTag'],'dataset':dataset});dump(prepared/'media-manifest.json',list(media.values()))
selection={'path':str(prepared),'dataset':dataset,'sha256':hashlib.sha256((prepared/'catalog-data.json').read_bytes()).hexdigest(),'mediaRoot':str(HOME/'media'),'products':len(data['products']),'reviewedCovers':public_count}
dump(ROOT/'.local/native-catalog-selection.json',selection);print(json.dumps({'prepared':True,'products':len(data['products']),'reviewedCovers':public_count,'availableImages':len(media),'dataset':dataset}))
