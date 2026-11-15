"""Create an immutable ready batch from translated, visually approved source records."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,re,shutil,sys,os
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication'
spec=importlib.util.spec_from_file_location('supplier_release',R/'lib/supplier_release.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
parser=argparse.ArgumentParser();parser.add_argument('--base',default='artifacts/cpanel-release-stripe-api-20261110');parser.add_argument('--output',default='artifacts/cpanel-release-suppliers-20261110');parser.add_argument('--implementation');args=parser.parse_args()
base=R/args.base;out=R/args.output
implementation=R/args.implementation if args.implementation else None
if out.exists():raise SystemExit('Use a new immutable output directory')
assert out.parent==R/'artifacts'and out.name.startswith('cpanel-release-')
reviews={}
for group in ['altinis','alka-source-clean']:
 review=json.loads((O/'media-review'/f'{group}.json').read_bytes());reviews.update(m.verify_review(review,R))
if (O/'media-review/alka-candidates-approved.json').exists():reviews.update(m.verify_review(json.loads((O/'media-review/alka-candidates-approved.json').read_bytes()),R))
source=json.loads((O/'content-tr.json').read_bytes())['products'];translated=json.loads((O/('content-publication-approved.json'if(O/'content-publication-approved.json').exists()else'content-translated.json')).read_bytes())['products']
by_source={p['id']:p for p in source};url_media={}
for p in source:
 for url in p['images']:
  file=R/'artifacts/supplier-expansion/media'/(hashlib.sha256(url.encode()).hexdigest()+'.bin')
  if file.exists():url_media[url]=m.digest(file)

def category(p):
 text=' '.join(p['sourceCategories']).casefold()
 if any(x in text for x in ['çalışma masası','yemek masası']):return 'ahsap-masalar'
 if any(x in text for x in ['sandalye','tabure']):return 'ahsap-sandalyeler'
 if any(x in text for x in ['koltuk','berjer','oturma grubu','puf']):return 'ahsap-oturma'
 if any(x in text for x in ['sehpa','fiskos','tavla']):return 'ahsap-sehpalar'
 if any(x in text for x in ['konsol','dresuar','gümüşlük','vitrin','kitaplık','tv sehpası']):return 'ahsap-depolama'
 if any(x in text for x in ['başlığı','komodin','şifonyer','makyaj masası']):return 'ahsap-yatak-odasi'
 if 'ayna' in text:return 'ahsap-aynalar'
 if any(x in text for x in ['çıt','taçlar','alın tahtası']):return 'ahsap-citalar'
 if any(x in text for x in ['ayak','ayaklar']):return 'ahsap-ayaklar'
 if any(x in text for x in ['merdiven','trabzan','küpeşte']):return 'ahsap-merdiven'
 if any(x in text for x in ['hasır','hazeran']):return 'ahsap-hasir'
 if any(x in text for x in ['seperatör','panjur']):return 'ahsap-paneller'
 if any(x in text for x in ['aplik','göbek','rozet','payanda']):return 'ahsap-suslemeler'
 if any(x in text for x in ['kulp','bağlantı','kavela']):return 'ahsap-baglanti'
 return 'ahsap-aksesuarlar'
names=[
 ('ahsap-masalar','Ahşap masalar','Wooden tables and desks','Деревянные столы','طاولات ومكاتب خشبية'),
 ('ahsap-sandalyeler','Ahşap sandalyeler','Wooden chairs and stools','Деревянные стулья и табуреты','كراسي ومقاعد خشبية'),
 ('ahsap-oturma','Ahşap koltuk ve iskeletler','Wooden seating and frames','Деревянная мягкая мебель и каркасы','مقاعد وهياكل خشبية'),
 ('ahsap-sehpalar','Ahşap sehpalar','Wooden occasional tables','Деревянные журнальные столики','طاولات جانبية وقهوة خشبية'),
 ('ahsap-depolama','Ahşap konsol ve depolama','Wooden consoles and storage','Деревянные консоли и хранение','كونسولات ووحدات تخزين خشبية'),
 ('ahsap-yatak-odasi','Ahşap yatak odası parçaları','Wooden bedroom furniture','Деревянная мебель для спальни','أثاث غرف نوم خشبي'),
 ('ahsap-aynalar','Ahşap ayna çerçeveleri','Wooden mirror frames','Деревянные рамы для зеркал','إطارات مرايا خشبية'),
 ('ahsap-citalar','Ahşap ve MDF çıtalar','Wood and MDF mouldings','Погонаж из дерева и МДФ','حليات خشبية ومن MDF'),
 ('ahsap-ayaklar','Mobilya ayakları','Furniture legs','Мебельные ножки','أرجل الأثاث'),
 ('ahsap-merdiven','Merdiven parçaları','Stair components','Детали лестниц','مكونات السلالم'),
 ('ahsap-hasir','Hasır ve hazeran','Cane and woven panels','Ротанг и плетёные полотна','خيزران وألواح منسوجة'),
 ('ahsap-paneller','Seperatör ve panjur paneller','Dividers and louvre panels','Перегородки и жалюзийные панели','فواصل وألواح شرائح'),
 ('ahsap-suslemeler','Ahşap oyma ve süslemeler','Wooden carvings and ornaments','Деревянная резьба и декор','زخارف ونقوش خشبية'),
 ('ahsap-baglanti','Kulp ve bağlantı parçaları','Handles and fittings','Ручки и фурнитура','مقابض ووصلات'),
 ('ahsap-aksesuarlar','Ahşap aksesuarlar','Wooden accessories','Деревянные аксессуары','إكسسوارات خشبية')]
rootcat={'id':'ahsap-mobilya-malzemeleri','parentId':None,'name':m.localized('Ahşap mobilya ve yardımcı ürünler','Wooden furniture and accessories','Деревянная мебель и вспомогательные изделия','أثاث خشبي ومنتجات مساعدة')}
categories=[rootcat]+[{'id':x[0],'parentId':rootcat['id'],'name':m.localized(*x[1:])}for x in names]
eligible={};held=[];assets={};provenance={};excluded=[]
missing_photo=json.loads((O/'source-exceptions/AK74.json').read_bytes());assert m.digest(R/missing_photo['path'])==missing_photo['sha256']
for p in translated:
 if p['id']=='altinis-c691ad1170':
  assert p['rawTitle']=='test'and not p['images'];excluded.append({'id':p['id'],'reason':'supplier_test_record'});continue
 try:
  assert p['translationVerified']is True
  assert all(p['name'].get(l)and isinstance(p['translatedParagraphs'].get(l),list)for l in ['tr','en','ru','ar'])
  sale=m.retail_price(p);images=[]
  for url in p['images']:
   sourcehash=url_media[url];row=reviews[sourcehash];file=R/row['path'];fmt=Image.open(file).format;ext={'JPEG':'jpg','PNG':'png','WEBP':'webp'}[fmt];target=f'assets/suppliers/{row["outputSha256"]}.{ext}';images.append('/'+target);assets[target]=file
   provenance[target]={**row,'originalUrl':url,'reviewGroup':'altinis'if p['supplierId']=='altinis'else'alka'}
  if not images:assert p['id']==missing_photo['id']and p['sourceUrl']==missing_photo['url']and missing_photo['reason']=='supplier_has_no_product_photo'
  unit=p['quantityPolicy']['unit'];specs=[{'label':m.UNIT_LABEL,'value':m.UNITS[unit]}]
  if p['dimensions']:
   dim=p['dimensions'];value=' × '.join(str(dim[k])for k in ['width','height','depth']if k in dim)+' cm'
   specs.append({'label':m.localized('Ölçüler','Dimensions','Размеры','الأبعاد'),'value':dict.fromkeys(['tr','en','ru','ar'],value)})
  sizes=m.listed_sizes(p['rawTitle'])
  if sizes and not p['dimensions']:specs.append({'label':m.localized('Ölçü bilgisi','Listed size','Размер по описанию','المقاس المذكور'),'value':dict.fromkeys(['tr','en','ru','ar'],' / '.join(sizes))})
  q=p['quantityPolicy'];minimum=q['minimum'];step=q['step']
  if minimum>1 or step>1:specs.append({'label':m.localized('En az alım ve artış','Minimum and increment','Минимум и шаг','الحد الأدنى والزيادة'),'value':{l:f'{minimum} / {step} {m.UNITS[unit][l]}'for l in m.UNITS[unit]}})
  if q.get('stockLengthM'):specs.append({'label':m.localized('Standart boy','Stock length','Стандартная длина','الطول القياسي'),'value':dict.fromkeys(['tr','en','ru','ar'],str(q['stockLengthM'])+' m')})
  description={l:'\n\n'.join(p['translatedParagraphs'][l])or p['name'][l]for l in ['tr','en','ru','ar']}
  assert not re.search(r'\b(?:alka|altinisagac|adore)\b',json.dumps(description,ensure_ascii=False),re.I)
  pub={'id':p['id'],'code':p['code'],'name':p['name'],'modelId':p['id'],'modelName':p['name'],'description':description,'categoryIds':[rootcat['id'],category(p)],'images':list(dict.fromkeys(images)),'coverIndex':0,'specs':specs,'salePriceMinor':sale,'currency':'TRY','productType':'supplier-item','saleUnit':unit,'quantityPolicy':q,'priceTaxPolicy':m.tax_policy(p['supplierId']),'variantColor':dict.fromkeys(['tr','en','ru','ar'],''),'published':True}
  if any(a['value']=='ihlamur-kisa-boy'for a in p['variantAttributes']):
   pub['quantityPolicy']={k:v for k,v in q.items()if k!='stockLengthM'};pub['specs']=[item for item in pub['specs']if item['label']['tr']!='Standart boy']
   keep=[i for i,text in enumerate(p['paragraphs'])if not re.search(r'standart\s+boyu',text,re.I)]
   pub['description']={lang:'\n\n'.join(p['translatedParagraphs'][lang][i]for i in keep)or p['name'][lang]for lang in ['tr','en','ru','ar']}
   pub['scopeNote']=m.localized('Kısa boy seçeneği. Parça boyları teklif aşamasında netleştirilir.','Short stock length option. Individual lengths are confirmed in the quotation.','Короткая заготовка. Длины отдельных частей уточняются в предложении.','خيار القطع القصيرة. تُحدَّد أطوال القطع في عرض السعر.')
  if re.search(r'\bApel\b',p['rawTitle'],re.I):pub['productBrand']='APEL'
  if p['id']=='alka-baaedc4671':pub['scopeNote']=m.localized('Bu fiyat kısa boy ürünler için geçerlidir. Boy ölçüsünü sipariş öncesinde netleştirin.','This price applies to short stock lengths. Confirm the length before ordering.','Цена относится к коротким заготовкам. Уточните длину перед заказом.','يسري هذا السعر على القطع القصيرة. يُرجى تأكيد الطول قبل الطلب.')
  eligible[p['id']]=pub
 except (AssertionError,ValueError,KeyError)as e:held.append({'id':p['id'],'reason':str(e)or'publication_gate'})
# A variant family is published only when every recorded choice has passed its gates.
families={}
for p in source:
 if p.get('parentSourcePageId'):families.setdefault(p['parentSourcePageId'],[]).append(p['id'])
for parent,children in families.items():
 parent_id=next((p['id']for p in source if p['supplierId']=='alka'and p['sourcePageId']==parent),None)
 members=children+([parent_id]if parent_id else[])
 if not all(id in eligible for id in members):
  for id in members:
   if eligible.pop(id,None):held.append({'id':id,'reason':'variant_family_incomplete'})
 else:
  for id in members:eligible[id]['modelId']='alka-family-'+parent
  # Explicitly named choices; never manufacture colour variants or combinations.
  for id in members:
   attrs=by_source[id]['variantAttributes']
   if attrs:
    eligible[id]['variantLabel']=m.variant_label(attrs)
    eligible[id]['specs']+=[{'label':m.ATTRIBUTE_LABELS[a['name']],'value':m.MATERIAL_VALUES.get(a['value'],dict.fromkeys(['tr','en','ru','ar'],a['value'].replace('-',' ')))}for a in attrs]
   else:
    eligible[id]['variationSelectionRequired']=True
    eligible[id]['scopeNote']=m.localized('Önce aşağıdan ürün seçeneğinizi belirleyin.','Choose your product option below.','Сначала выберите вариант товара ниже.','اختر خيار المنتج أدناه أولاً.')
    eligible[id]['variantLabel']=m.localized('Seçenek belirleyin','Choose an option','Выберите вариант','اختر خيارًا')
products=list(eligible.values());products.sort(key=lambda p:(p['salePriceMinor']is None,bool(by_source[p['id']].get('variants')),p['id']))
used={url.lstrip('/')for p in products for url in p['images']};assets={k:v for k,v in assets.items()if k in used};provenance={k:v for k,v in provenance.items()if k in used}
catalog=json.loads((base/'private/catalog.json').read_bytes());existing={p['id']for p in catalog['products']};old_suppliers=[p for p in catalog['products']if p.get('productType')=='supplier-item'];assert {p['id']for p in old_suppliers}<=set(eligible),'Previously published supplier rows must remain ready'
products=[p for p in products if p['id']not in existing]
codes=[p['code']for p in products];assert len(codes)==len(set(codes));assert not set(codes).intersection(p['code']for p in catalog['products'])
for path in base.rglob('*'):
 if not path.is_file():continue
 rel=path.relative_to(base);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);os.link(path,dest)
catalog['products']=[eligible.get(p['id'],p)if p.get('productType')=='supplier-item'else p for p in catalog['products']];catalog['products']+=products;category_ids={c['id']for c in catalog['categories']};catalog['categories']+=[c for c in categories if c['id']not in category_ids];catalog['meta']['supplierPublication']={'date':'2026-11-10','products':len(products),'reviewedImages':len(assets)}
def write(rel,body):
 file=out/rel;file.parent.mkdir(parents=True,exist_ok=True)
 if file.exists():
  if file.read_bytes()==body:return
  assert file.is_relative_to(out)and not file.is_symlink();file.unlink()
 file.write_bytes(body)
# Full descriptions are packed privately with exact frame offsets and hashes; the listing stays compact.
detail_blob=bytearray();detail_index={}
old_detail_index=json.loads((base/'private/supplier-details.json').read_bytes())if(base/'private/supplier-details.json').exists()else None
old_detail_blob=(base/'private/supplier-details.bin').read_bytes()if old_detail_index else None
for product in catalog['products']:
 if product.get('productType')!='supplier-item':continue
 description=product['description']
 if product.get('supplierDetailsHash')and old_detail_index:
  entry=old_detail_index['products'][product['id']];frame=old_detail_blob[entry['offset']:entry['offset']+entry['bytes']];assert hashlib.sha256(frame).hexdigest()==entry['sha256'];description=json.loads(frame)['description']
 frame=json.dumps({'id':product['id'],'description':description},ensure_ascii=False,separators=(',',':')).encode();assert len(frame)<=262144
 digest=hashlib.sha256(frame).hexdigest();detail_index[product['id']]={'offset':len(detail_blob),'bytes':len(frame),'sha256':digest};detail_blob.extend(frame);product['supplierDetailsHash']=digest;product['description']=product['name']
supplier_refs={p['id']+':'+str(i):url for p in catalog['products']if p.get('productType')=='supplier-item'for i,url in enumerate(p['images'])}
supplier_images={}
for url in dict.fromkeys(supplier_refs.values()):
 row=provenance[url.lstrip('/')];supplier_images[url]={'sourceSha256':row['sourceSha256'],'outputSha256':row['outputSha256'],'visualReview':True,'reviewedAt':'2026-11-10'}
write('private/supplier-media-approved.json',json.dumps({'schema':1,'publicationReady':True,'testOnly':False,'images':supplier_images,'references':supplier_refs},separators=(',',':')).encode())
write('private/supplier-details.bin',bytes(detail_blob));write('private/supplier-details.json',json.dumps({'schema':1,'products':detail_index},separators=(',',':')).encode())
write('private/catalog.json',json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode())
for name in ['app.js','shop-core.js','supplier-products.js']:
 body=(implementation/'public'/name if implementation else R/'web'/name).read_bytes()
 if name=='app.js':
  text=body.decode();old='<small class="price-tax-note">${esc(isSupplierProduct(p)?supplierTaxNote(p,locale):paymentText(locale,\'netLabel\'))}</small>${esc(supplierPriceSuffix(p,locale))}'
  new='<small class="price-tax-note">${esc(isSupplierProduct(p)?[supplierPriceSuffix(p,locale).trim(),supplierTaxNote(p,locale)].filter(Boolean).join(\'  \'):paymentText(locale,\'netLabel\'))}</small>'
  assert text.count(old)==1 or text.count(new)==1;body=text.replace(old,new).encode()
 write('public/'+name,body)
for name in ['account.php','door-commerce.php','seo.php','supplier-products.php']:write('private/'+name,(implementation/'private'/name if implementation else R/'hosting'/name).read_bytes())
write('public/index.php',(implementation/'public/index.php'if implementation else R/'hosting/index.php').read_bytes())
for rel,file in assets.items():write('public/'+rel,file.read_bytes())
html=(base/'private/index.html').read_text(encoding='utf8');html=re.sub(r'(app\.js\?v=)[^"\s]+',r'\g<1>nodeno-suppliers-20261110-r4',html);write('private/index.html',html.encode())
manifest=json.loads((base/'private/release.json').read_bytes());manifest['products']=len(catalog['products']);manifest['categories']=len(catalog['categories']);manifest['files']={str(p.relative_to(out)).replace('\\','/'):m.digest(p)for p in out.rglob('*')if p.is_file()and p!=out/'private/release.json'};manifest['files']=dict(sorted(manifest['files'].items()));finger=hashlib.sha256()
for name,h in manifest['files'].items():finger.update((name+'\0'+h+'\0').encode())
manifest['releaseHash']=finger.hexdigest();write('private/release.json',json.dumps(manifest,indent=2).encode())
receipt={'publicationReady':True,'baseReleaseHash':json.loads((base/'private/release.json').read_bytes())['releaseHash'],'releaseHash':manifest['releaseHash'],'products':len(products),'images':len(assets),'held':held,'excludedSourceRecords':excluded,'sourcePhotoMissingIds':[missing_photo['id']],'untranslated':len(source)-len(translated),'productIds':[p['id']for p in products],'publishedSupplierIds':[p['id']for p in catalog['products']if p.get('productType')=='supplier-item'],'assets':provenance,'sourceContentSha256':m.digest(O/'content-tr.json'),'translatedContentSha256':m.digest(O/'content-publication-approved.json'),'checkoutEnabled':False}
(O/(out.name+'-proof.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items()if k not in ['assets','held','productIds']},ensure_ascii=False))
