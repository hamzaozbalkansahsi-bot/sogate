#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_catalog.py
# Açıklama   : Gerçek tedarikçi kayıtlarını kaynak kanıtı, %30 ilk fiyat ve katalog/SEO alanlarına eşler.
import argparse,hashlib,html,json,re,unicodedata
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
LANGUAGES=['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']
HOME=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-catalog-20261115')
BASE=HOME.parent
GROUPS={
 'toys':['Yetişkin Oyuncakları','Adult Toys','Игрушки для взрослых','ألعاب للبالغين','Erwachsenenspielzeug','Böyüklər üçün oyuncaqlar','Ересектерге арналған ойыншықтар','Uly ýaşlylar üçin oýunjaklar','Kattalar uchun o‘yinchoqlar','Чоңдор үчүн оюнчуктар','اسباب‌بازی بزرگسالان'],
 'lingerie':['İç Giyim ve Kostüm','Lingerie and Costumes','Бельё и костюмы','ملابس داخلية وأزياء','Dessous und Kostüme','Alt paltarı və kostyumlar','Іш киім және костюмдер','Iç geýim we lybaslar','Ichki kiyim va kostyumlar','Ич кийим жана костюмдар','لباس زیر و لباس نمایشی'],
 'couples':['Çift Ürünleri','For Couples','Для пар','للأزواج','Für Paare','Cütlüklər üçün','Жұптарға арналған','Jübütler üçin','Juftliklar uchun','Жубайлар үчүн','برای زوج‌ها'],
 'accessories':['Aksesuarlar','Accessories','Аксессуары','إكسسوارات','Accessoires','Aksesuarlar','Аксессуарлар','Aksessuarlar','Aksessuarlar','Аксессуарлар','لوازم جانبی'],
 'care':['Bakım Ürünleri','Care Products','Уход','منتجات العناية','Pflegeprodukte','Qulluq məhsulları','Күтім өнімдері','Ideg önümleri','Parvarish vositalari','Кам көрүү каражаттары','محصولات مراقبت'],
 'gifts':['Hediye Setleri','Gift Sets','Подарочные наборы','مجموعات هدايا','Geschenksets','Hədiyyə dəstləri','Сыйлық жиынтықтары','Sowgat toplumlary','Sovg‘a to‘plamlari','Белек топтомдору','مجموعه‌های هدیه']}
LABELS={
 'sku':['Ürün kodu','Product code','Код товара','رمز المنتج','Artikelnummer','Məhsul kodu','Өнім коды','Haryt kody','Mahsulot kodi','Товардын коду','کد محصول'],
 'brand':['Marka','Brand','Бренд','العلامة التجارية','Marke','Marka','Бренд','Marka','Brend','Бренд','برند'],
 'materials':['Malzeme','Material','Материал','الخامة','Material','Material','Материал','Material','Material','Материал','جنس'],
 'dimensions':['Ölçü','Dimensions','Размеры','الأبعاد','Abmessungen','Ölçülər','Өлшемдер','Ölçegler','O‘lchamlar','Өлчөмдөр','ابعاد'],
 'sizeOptions':['Beden seçenekleri','Size options','Размеры','خيارات المقاس','Größen','Ölçü seçimləri','Өлшем нұсқалары','Beden ölçegleri','O‘lcham variantlari','Өлчөмдөр','گزینه‌های اندازه'],
 'colorOptions':['Renk seçenekleri','Colour options','Цвета','خيارات اللون','Farben','Rəng seçimləri','Түс нұсқалары','Reňkler','Ranglar','Түстөр','گزینه‌های رنگ']}
def loc(values):return dict(zip(LANGUAGES,values))
def markup(value):return (value*130+50)//100 if isinstance(value,int)and not isinstance(value,bool)and 0<value<=100000000000 else None
def plain(value):
 if value is None or str(value).strip().lower()in ['none','null','undefined','']:return ''
 soup=BeautifulSoup(str(value),'lxml')
 for tag in soup.select('script,style,noscript'):tag.decompose()
 return re.sub(r'\s+',' ',soup.get_text(' ',strip=True)).strip()
def fold(value):return ''.join(c for c in unicodedata.normalize('NFKD',str(value).replace('ı','i').replace('İ','i').lower())if not unicodedata.combining(c))
def product_id(vendor,row):return 'sg_'+vendor[:3]+'_'+hashlib.sha256(row['sourceUrl'].encode()).hexdigest()[:16]
def gtin(value):
 value=str(value or '').strip()
 if not re.fullmatch(r'\d{8}|\d{12,14}',value):return None
 return value if sum(int(c)*(3 if i%2==0 else 1)for i,c in enumerate(value[-2::-1]))%10==(10-int(value[-1]))%10 else None
def safe_description(value):
 text=plain(value);sentences=re.split(r'(?<=[.!?])\s+|[\r\n]+',text)
 return ' '.join(s for s in sentences if not re.search(r'tedavi|kesin sonuç|medikal|sertifik|su geçirme|orgazm|en çok sat|en iyi|performans.*art|büyümesini|müşterilerimiz|whatsapp|https?://|@',s,re.I))[:3500]
def group_for(vendor,title):
 text=fold(title)
 if vendor in ['liona','sistina']:return 'lingerie'
 if any(k in text for k in ['hediye','seti','cift set']):return 'gifts'
 if any(k in text for k in ['ic giyim','gecelik','jartiyer','sutyen','body','string','kostum','corap','kilot']):return 'lingerie'
 if any(k in text for k in ['kayganlastirici','temizleyici','bakim','krem','kondom','prezervatif','masaj yagi','masaj jeli','sprey']):return 'care'
 if any(k in text for k in ['maske','kelepce','kirbac','baglama','kemer','aksesuar','pil','sarj']):return 'accessories'
 if any(k in text for k in ['cift','remote','uzaktan','kumanda']):return 'couples'
 return 'toys'
def next_data(soup):
 tag=soup.select_one('#__NEXT_DATA__')
 if not tag:return None
 try:
  value=json.loads(tag.get_text()).get('props',{}).get('pageProps',{}).get('pageSpecificData')
  return value if isinstance(value,dict)and isinstance(value.get('variants'),list)else None
 except ValueError:return None
def source_detail(vendor,row):
 facts={'materials':None,'dimensions':None,'sizeOptions':None,'colorOptions':None,'manufacturer':None,'origin':None,'barcode':None,'batteryInformation':None,'shippingWeight':None,'packageDimensions':None,'ingredients':None,'warranty':None,'care':None,'safety':None,'documents':None,'costMinor':None}
 detail={'description':plain(row.get('description')),'brand':plain(row.get('brand'))or None,'sourceSku':plain(row.get('sku'))or None,'facts':facts,'variants':row.get('variants',[]),'categories':row.get('categories')or row.get('breadcrumbs')or[],'observedAt':row.get('observedAt'),'sourceHtmlSha256':row.get('sourceHtmlSha256')}
 cache=BASE/'supplier-catalog'/vendor/'cache'/(hashlib.sha256(row['sourceUrl'].encode()).hexdigest()+'.body')
 if cache.is_file()and vendor in ['liona','sistina']:
  raw=cache.read_bytes();soup=BeautifulSoup(raw,'lxml');detail['sourceHtmlSha256']=hashlib.sha256(raw).hexdigest();product=next_data(soup)
  if product:
   detail['description']=plain(product.get('description'))or detail['description'];detail['brand']=plain((product.get('brand')or{}).get('name'))or detail['brand'];detail['categories']=product.get('categories',[])
   variants=[]
   for variant in product.get('variants',[]):
    if variant.get('deleted'):continue
    variants.append({k:variant.get(k)for k in ['id','sku','barcodeList','variantValues','isActive','sellIfOutOfStock','weight']})
   detail['variants']=variants
   skus={plain(v.get('sku'))for v in variants if plain(v.get('sku'))}
   if len(skus)==1:detail['sourceSku']=next(iter(skus))
   codes={code for v in variants for raw_code in(v.get('barcodeList')or[])if(code:=gtin(raw_code))}
   if len(variants)==1 and len(codes)==1:facts['barcode']=next(iter(codes))
   for variant_type in product.get('variantTypes',[]):
    value=variant_type.get('variantType')or{};name=fold(value.get('name',''));selected=set(variant_type.get('variantValueIds',[]));options=[plain(v.get('name'))for v in value.get('values',[])if not selected or v.get('id')in selected]
    if options and name in ['beden','size','renk','color']:facts['sizeOptions'if name in ['beden','size']else'colorOptions']=', '.join(dict.fromkeys(options))
  elif vendor=='liona':
   body=soup.select_one('#tab-description,.product-description,[itemprop="description"]')
   if body:detail['description']=plain(str(body))or detail['description']
   for select in soup.select('select[name^="option["]'):
    label=plain(str(select.find_previous('label')));options=[o.get_text(' ',strip=True)for o in select.select('option[value]')if o.get('value')and o.get_text(' ',strip=True)];name=fold(label)
    if options:facts['sizeOptions'if'beden'in name else'colorOptions'if'renk'in name else'sizeOptions']=', '.join(dict.fromkeys(options))
   for table_row in soup.select('table.attribute tr,table.table-bordered tr'):
    cells=table_row.select('td')
    if len(cells)==2:
     name=fold(cells[0].get_text(' ',strip=True));value=cells[1].get_text(' ',strip=True)
     if name in ['materyal','malzeme','kumas','kumas bilgisi']:facts['materials']=value
 text=detail['description']
 for name,pattern in {'materials':r'(?:Malzeme|Materyal|Kumaş)\s*:\s*([^.;]{2,120})','dimensions':r'(?:(?:Ürün )?Ölçü(?:leri|sü)?|Uzunluk)\s*:\s*([^.;]{2,120})','care':r'(?:Bakım|Yıkama|Temizleme)(?: talimatı| bilgisi)?\s*:\s*([^.;]{3,250})','ingredients':r'(?:İçindekiler|İçerik)\s*:\s*([^.;]{3,250})'}.items():
  match=re.search(pattern,text,re.I)
  if match and not facts[name]:facts[name]=match.group(1).strip()
 for field in ['manufacturer','origin','batteryInformation','shippingWeight','packageDimensions','warranty','safety','documents']:facts[field]=None
 return detail
def api_records():
 records={}
 for path in (BASE/'supplier-api-live-20261115/xshopum/cache').glob('*.body'):
  try:values=json.loads(path.read_bytes())
  except (ValueError,UnicodeDecodeError):continue
  if not isinstance(values,list):continue
  for value in values:
   if isinstance(value,dict)and isinstance(value.get('id'),int)and'prices'in value:records[value['id']]=value
 return records
def enrich_api(detail,raw):
 if not raw:return detail
 brands=[plain(b.get('name'))for b in raw.get('brands',[])if isinstance(b,dict)and plain(b.get('name'))]
 if len(brands)==1:detail['brand']=brands[0]
 aliases={'marka':'brand','markasi':'brand','brand':'brand','materyal':'materials','malzeme':'materials','kumas':'materials','uretici':'manufacturer','mense':'origin','mensei':'origin','pil tipi':'batteryInformation','pil turu':'batteryInformation','guc kaynagi':'batteryInformation','barkod':'barcode','gtin':'barcode','ean':'barcode'}
 for attribute in raw.get('attributes',[]):
  key=aliases.get(fold(attribute.get('name','')));values=[plain(v.get('name'))for v in attribute.get('terms',[])if plain(v.get('name'))]
  if not key or not values:continue
  value=', '.join(values)
  if key=='brand':detail['brand']=value
  elif key=='barcode':detail['facts']['barcode']=gtin(value)
  else:detail['facts'][key]=value
 for source,key in [('formatted_weight','shippingWeight'),('formatted_dimensions','dimensions')]:
  value=plain(raw.get(source))
  if value and re.search('[1-9]',value):detail['facts'][key]=value
 return detail
def make_product(vendor,row,detail):
 detail=detail or source_detail(vendor,row);identifier=product_id(vendor,row);source_sku=detail['sourceSku'];sku=vendor[:3].upper()+'-'+(source_sku or identifier.rsplit('_',1)[1].upper());title=plain(row.get('title'))[:240];group=group_for(vendor,title);facts=detail['facts'];brand=detail['brand'];price=markup(row.get('quotedRetailMinor'))if row.get('quotedCurrency')=='TRY'else None
 names={language:(title if language=='tr'else' '.join(s for s in [brand,loc(GROUPS[group])[language],source_sku or sku]if s))for language in LANGUAGES}
 descriptions={};seo={};attributes=[]
 for key in ['materials','dimensions','sizeOptions','colorOptions']:
  if facts.get(key):attributes.append({'name':loc(LABELS[key]),'value':{language:facts[key]for language in LANGUAGES}})
 for language in LANGUAGES:
  parts=[names[language]+'.',loc(LABELS['sku'])[language]+': '+sku+'.']
  if language=='tr'and(clean:=safe_description(detail['description'])):parts.append(clean)
  for key in ['materials','dimensions','sizeOptions','colorOptions']:
   if facts.get(key):parts.append(loc(LABELS[key])[language]+': '+facts[key]+'.')
  descriptions[language]=' '.join(parts);seo[language]=' '.join(parts[:2]+parts[-min(len(attributes),2):]if attributes else parts[:2])[:165]
 regulated=bool(re.search(r'\b(hap|tablet|kapsul|viagra|cialis|ilac|tedavi|afrodizyak|medikal)\b|su gecirmez|klinik',fold(title+' '+(facts.get('materials')or''))));missing=[key for key,value in facts.items()if value is None and key not in ['costMinor']]
 product={'id':identifier,'modelId':identifier,'modelName':names,'name':names,'code':sku,'sku':sku,'brand':brand,'categoryIds':['sg_'+group],'description':descriptions,'seoTitle':{language:names[language][:150]for language in LANGUAGES},'seoDescription':seo,'slug':re.sub('[^a-z0-9]+','-',fold(title)).strip('-')+'-'+identifier[-8:],'attributes':attributes,'images':['/media/'+identifier+'/'+str(i)for i in range(len(row.get('images',[])))],'coverIndex':0,'salePriceMinor':price,'currency':'TRY','stockKnown':False,'stockQuantity':None,'published':False,'hidden':True,'productType':'adult-product','catalogOrigin':'sexogate-suppliers-v1','sourceVendor':vendor,'facts':{k:v for k,v in facts.items()if k!='costMinor'},'variantColor':{language:facts['colorOptions']or''for language in LANGUAGES},'variationSelectionRequired':False,'referencePriceVerified':False,'taxTreatment':'unverified','eligibilityHold':regulated}
 source={'vendor':vendor,'url':row['sourceUrl'],'sourceSku':source_sku,'retailPriceMinor':row.get('quotedRetailMinor'),'currency':row.get('quotedCurrency'),'publicInStock':row.get('publicInStock'),'quantity':None,'observedAt':row.get('observedAt'),'htmlSha256':detail.get('sourceHtmlSha256'),'method':row.get('sourceMethod','public_page_snapshot')}
 work={'id':identifier,'sku':sku,'brand':brand,'group':group,'source':source,'facts':facts,'sourceDescription':detail['description'],'sourceCategories':detail['categories'],'sourceVariants':detail['variants'],'sourceImages':row.get('images',[]),'missingFields':missing,'rights':{'basis':'user_declaration','at':'2026-11-15','scope':'product_images_and_content','writtenContractClaimed':False},'initialMarkupPercent':30,'eligibilityHold':regulated,'translationMethod':'source_TR_and_localized_factual_summaries','publicationApproved':False}
 return product,work
def build(reuse_details=False):
 HOME.mkdir(exist_ok=True);paths={'xshopum':BASE/'supplier-api-live-20261115/xshopum/xshopum.ndjson',**{v:BASE/'supplier-catalog'/v/(v+'.ndjson')for v in ['liona','sistina']}}
 products=[];work=[];categories=[];sources=[];raw_api=api_records();old={}
 if reuse_details:
  previous=json.loads((HOME/'catalog-source.json').read_text('utf8'))
  for source in previous['sources']:
   if source['sha256']!=hashlib.sha256(paths[source['vendor']].read_bytes()).hexdigest():raise ValueError('REUSED_SOURCE_CHANGED')
  old={w['id']:w for w in previous['workbench']}
 for vendor,path in paths.items():
  rows=[json.loads(line)for line in path.read_text('utf8').splitlines()];sources.append({'vendor':vendor,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'file':path.name,'products':sum(r['kind']=='product'for r in rows)})
  for row in rows:
   if row['kind']=='category':categories.append({**row,'vendor':vendor});continue
   identifier=product_id(vendor,row);cached=old.get(identifier)
   source_value={'description':cached['sourceDescription'],'brand':cached['brand'],'sourceSku':cached['source']['sourceSku'],'facts':cached['facts'],'variants':cached['sourceVariants'],'categories':cached['sourceCategories'],'sourceHtmlSha256':cached['source']['htmlSha256']}if cached else source_detail(vendor,row)
   product,detail=make_product(vendor,row,enrich_api(source_value,raw_api.get(row.get('sourceApiId')))if vendor=='xshopum'else source_value);products.append(product);work.append(detail)
   if len(products)%200==0:print(json.dumps({'preparedProducts':len(products)}),flush=True)
 ids=[p['id']for p in products];assert len(ids)==len(set(ids))==2194
 codes=Counter(p['code']for p in products)
 for product,detail in zip(products,work):
  if codes[product['code']]>1:product['code']=product['sku']=detail['sku']=product['code']+'-'+product['id'][-6:]
 for p in products:
  if '\ufffd'in json.dumps(p,ensure_ascii=False):raise ValueError('UTF8_REPLACEMENT_CHARACTER')
 output={'schema':1,'sourceTag':'sexogate-suppliers-v1','builtAt':datetime.now(timezone.utc).isoformat(),'sources':sources,'products':products,'categories':[{'id':'sg_'+group,'name':loc(labels),'parentId':None,'slug':group}for group,labels in GROUPS.items()],'sourceCategories':categories,'workbench':work,'markupPercent':30,'rightsBasis':'user_declaration_2026-11-15','checkoutEnabled':False}
 (HOME/'catalog-source.json').write_text(json.dumps(output,ensure_ascii=False),encoding='utf8')
 report={'products':len(products),'sourceCategories':len(categories),'storeCategories':len(GROUPS),'priced':sum(p['salePriceMinor']is not None for p in products),'priceMissing':sum(p['salePriceMinor']is None for p in products),'regulatedReview':sum(p['eligibilityHold']for p in products),'sourceDescriptionRecovered':sum(bool(w['sourceDescription'])for w in work),'withVariantMetadata':sum(bool(w['sourceVariants'])for w in work),'withBarcode':sum(bool(w['facts']['barcode'])for w in work),'missingFacts':dict(Counter(key for w in work for key in w['missingFields'])),'fakeStockOrCost':False,'sourceHashes':sources};(HOME/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--reuse-details',action='store_true');build(parser.parse_args().reuse_details)
