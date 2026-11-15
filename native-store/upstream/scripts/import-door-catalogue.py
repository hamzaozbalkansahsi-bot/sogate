"""Import only the actual product photographs and facts from the owner-supplied R4 PDFs."""
from pathlib import Path
from collections import Counter
import fitz,hashlib,json,re
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/doors-r4';OUT.mkdir(exist_ok=True)
CATALOGUE=Path('C:/Users/Hamza ÖZBALKAN/Desktop/NDECOR_Kapi_Katalogu_R4.pdf')
PRICES=Path('C:/Users/Hamza ÖZBALKAN/Desktop/NDECOR_Fiyat_Listesi_R4.pdf')
ASSETS=ROOT/'web/assets/doors';ASSETS.mkdir(parents=True,exist_ok=True)
sha=lambda body:hashlib.sha256(body).hexdigest()
doc=fitz.open(CATALOGUE);price_doc=fitz.open(PRICES)
catalogue_sha=sha(CATALOGUE.read_bytes())
assert len(doc)==205 and len(price_doc)==22
locales=['tr','en','ru','ar']
def loc(tr,en,ru,ar):return dict(zip(locales,[tr,en,ru,ar]))
families={'Klasik':loc('Klasik','Classic','Классик','كلاسيك'),'Elegant':loc('Elegant','Elegant','Элегант','إليغانت'),'Premium':loc('Premium','Premium','Премиум','بريميوم'),'Deluxe':loc('Deluxe','Deluxe','Делюкс','ديلوكس')}
finishes={
 'PVC Soft / Ahşap desen':('pvc-soft',loc('PVC Soft / Ahşap desen','Soft / woodgrain PVC','ПВХ Soft / древесный рисунок','بي في سي سوفت / بنقشة الخشب')),
 'PVC Bute':('pvc-bute',loc('PVC Bute','Bute PVC','ПВХ Bute','بي في سي بوته')),
 'Çift renk PVC':('pvc-dual',loc('Çift renk PVC','Two-tone PVC','Двухцветный ПВХ','بي في سي بلونين')),
 'Lake':('lacquer',loc('Lake','Lacquer','Лаковое покрытие','لاكيه')),
 'Ahşap kaplama':('veneer',loc('Ahşap kaplama','Wood veneer','Натуральный шпон','قشرة خشب طبيعي')),
 'Laminat':('laminate',loc('Laminat','Laminate','Ламинат','لامينيت')),
 'Melamin':('melamine',loc('Melamin','Melamine','Меламин','ميلامين')),
}
colors={
 'Soft fırtına gri':loc('Soft fırtına gri','Soft storm grey','Soft штормовой серый','سوفت رمادي عاصف'),
 'Soft koyu gri':loc('Soft koyu gri','Soft dark grey','Soft тёмно-серый','سوفت رمادي داكن'),
 'Soft açık gri':loc('Soft açık gri','Soft light grey','Soft светло-серый','سوفت رمادي فاتح'),
 'Soft beyaz':loc('Soft beyaz','Soft white','Soft белый','سوفت أبيض'),
 'Soft taş gri':loc('Soft taş gri','Soft stone grey','Soft каменно-серый','سوفت رمادي حجري'),
 'Antrasit':loc('Antrasit','Anthracite','Антрацит','أنثراسيت'),
 'Bute beyaz':loc('Bute beyaz','Bute white','Bute белый','بوته أبيض'),
 'Bute beyaz / Antrasit':loc('Bute beyaz / Antrasit','Bute white / anthracite','Bute белый / антрацит','بوته أبيض / أنثراسيت'),
 'Ilgaz ladin':loc('Ilgaz ladin','Ilgaz spruce','Ель Ilgaz','تنوب إيلغاز'),
 'Cappuccino':loc('Cappuccino','Cappuccino','Капучино','كابتشينو'),
 'İpek mat beyaz':loc('İpek mat beyaz','Silk-matt white','Шелковисто-матовый белый','أبيض حريري مطفأ'),
 'Afrika bambu':loc('Afrika bambu','African bamboo','Африканский бамбук','خيزران أفريقي'),
 'Ceviz':loc('Ceviz','Walnut','Орех','جوز'),
 'Hareli meşe':loc('Hareli meşe','Figured oak','Узорчатый дуб','بلوط متموج العروق'),
 'Tiger Wood':loc('Tiger Wood','Tiger Wood','Tiger Wood','تايغر وود'),
 'Greenport taşı':loc('Greenport taşı','Greenport stone','Камень Greenport','حجر غرينبورت'),
 'Kilimanjaro gül ağacı':loc('Kilimanjaro gül ağacı','Kilimanjaro rosewood','Палисандр Kilimanjaro','خشب الورد كليمنجارو'),
 'Yeni meşe':loc('Yeni meşe','New Oak','Новый дуб','بلوط جديد'),
}
assets={};products=[];sources=[]
def photo(page,xref):
 image=doc.extract_image(xref);body=image['image'];digest=sha(body);ext='jpg'if image['ext']=='jpeg'else image['ext'];name=digest+'.'+ext
 (ASSETS/name).write_bytes(body)
 assets[digest]={'path':'/assets/doors/'+name,'sha256':digest,'bytes':len(body),'width':image['width'],'height':image['height'],'sourcePage':page+1,'sourceXref':xref,'unchangedEmbeddedImage':True}
 return digest
def spec(label,value):return {'label':label,'value':value}
def add(product,page):
 product['sourceEvidence']={'documentSha256':catalogue_sha,'page':page+1}
 products.append(product)
def charges(group):return {'depth':{'17':18000,'19':30000,'21':45500},'architrave18':66000,'glazing':132000 if group in ['lacquer','veneer'] else 99000,'hardware':50000}
for i in range(2,55):
 page=doc[i];text=page.get_text(sort=True);code=re.search(r'ND\d{3,4}',text).group();family=next((f for f in families if f in text),None)
 line=next(line.strip()for line in text.splitlines()if any(line.strip().startswith(f+' / ')for f in finishes))
 prefix=next(f for f in finishes if line.startswith(f+' / '));group,finish=finishes[prefix];color=line[len(prefix)+3:]
 color_map=colors.get(color)or(loc(color,color,color,color)if re.fullmatch(r'RAL \d{4}',color)else None);assert color_map,color
 architrave=re.search(r'Pervaz:\s*(\d+)',text).group(1)
 match=re.search(r'([\d.]+)\s*TL\s+(\d+)\s*USD\s+(\d+)\s*EUR',text)
 amount=int(match[1].replace('.',''))*100 if match else None
 embedded=[im for im in page.get_images()if im[2]>1000];assert len(embedded)==1
 image=photo(i,embedded[0][0]);title=loc(f'{families[family]["tr"]+" "if family else ""}{code} İç Mekân Kapı Takımı',f'{families[family]["en"]+" "if family else ""}{code} Interior Door Set',f'{families[family]["ru"]+" "if family else ""}{code} Комплект межкомнатной двери',f'طقم باب داخلي {code}'+(' '+families[family]['ar']if family else''))
 variant={lang:finish[lang]+' · '+color_map[lang]for lang in locales}
 add({'id':'door-'+code.lower()+'-p'+str(i+1),'code':code,'modelId':'model-door-'+code.lower(),'name':title,'modelName':title,'variantColor':variant,'productType':'door','saleUnit':'set','currency':'TRY','salePriceMinor':amount,'salePrice':amount/100 if amount else None,'availability':'unknown','images':[],'assetHashes':[image],'coverIndex':0,'categoryIds':['kapilar','kapi-'+group],
 'specs':[spec(loc('Yüzey','Surface','Покрытие','السطح'),finish),spec(loc('Renk','Colour','Цвет','اللون'),color_map),spec(loc('Pervaz profili','Architrave profile','Профиль наличника','مقطع إطار التغطية'),loc(architrave,architrave,architrave,architrave))],
 'door':{'kind':'interior','family':family,'finishGroup':group,'architrave':architrave,'color':color_map,'finish':finish,'charges':charges(group),'glassAvailable':False,'taxIncluded':False,'freightIncluded':False,'delivery':'EXW Izmir','baseFrameDepthMaxCm':15,'baseFrameFinishHeightMaxCm':207},
 'description':loc('Kapı takımı fiyatı, 15 cm’ye kadar kasa derinliği ve 207 cm’ye kadar kasa bitiş yüksekliği içindir. Aksesuar, KDV ve nakliye hariçtir. İzmir fabrika teslimidir.','Set pricing covers frame depths up to 15 cm and finished frame heights up to 207 cm. Hardware, VAT and freight are excluded. Collection from the Izmir factory.','Цена комплекта рассчитана для коробки глубиной до 15 см и конечной высотой до 207 см. Фурнитура, НДС и перевозка оплачиваются отдельно. Самовывоз с фабрики в Измире.','سعر الطقم لعمق حلق حتى 15 سم وارتفاع نهائي حتى 207 سم. الملحقات والضريبة والنقل غير مشمولة. التسليم من مصنع إزمير.'),
 'sourcePrice':{'TRY':amount,'USD':int(match[2])*100 if match else None,'EUR':int(match[3])*100 if match else None}},i)
 counts=Counter()
def grid_items(page_index,pattern):
 page=doc[page_index];words=[w for w in page.get_text('words')if re.fullmatch(pattern,w[4])];result=[]
 for im in page.get_images():
  if im[0]==3:continue
  rect=page.get_image_rects(im[0])[0];cx=(rect.x0+rect.x1)/2
  candidates=[w for w in words if rect.y1<=w[1]<=rect.y1+70 and abs((w[0]+w[2])/2-cx)<55]
  assert candidates,(page_index,rect)
  word=min(candidates,key=lambda w:abs(w[1]-rect.y1)+abs((w[0]+w[2])/2-cx));result.append((rect.y0,rect.x0,im[0],word[4]))
 return sorted(result)
for i in range(55,59):
 for _,_,xref,code in grid_items(i,r'ND\d{3,4}'):
  counts[code]+=1;image=photo(i,xref);basis=next((p for p in products if p['code']==code),None);assert basis,code
  title=basis['name'];variant=loc('Camlı model'+(' '+str(counts[code])if counts[code]>1 else''),'Glazed model'+(' '+str(counts[code])if counts[code]>1 else''),'Остеклённая модель'+(' '+str(counts[code])if counts[code]>1 else''),'موديل مزجج'+(' '+str(counts[code])if counts[code]>1 else''))
  add({'id':'door-'+code.lower()+'-glass-'+str(counts[code]),'code':code,'modelId':basis['modelId'],'name':title,'modelName':title,'variantColor':variant,'productType':'door','saleUnit':'set','currency':'TRY','salePriceMinor':None,'salePrice':None,'availability':'unknown','assetHashes':[image],'coverIndex':0,'categoryIds':['kapilar','kapi-camli'],'specs':[spec(loc('Model','Model','Модель','الموديل'),variant)],'door':{'kind':'glazed','family':basis['door']['family'],'finishGroup':None,'glassAvailable':True,'charges':{},'taxIncluded':False,'freightIncluded':False,'delivery':'EXW Izmir'},'description':loc('Camlı modelin yüzeyi, rengi ve cam uygulaması için teklif isteyin. Fotoğraf katalogdaki model referansıdır.','Request a quote for the surface, colour and glazing. The photo is the catalogue model reference.','Запросите предложение на покрытие, цвет и остекление. Фото показывает модель из каталога.','اطلب عرضاً للسطح واللون والتزجيج. الصورة مرجع الموديل في الكتالوج.')},i)
for p in products:
 if p['door']['kind']=='interior':p['door']['glassAvailable']=p['code']in counts
for _,_,xref,code in grid_items(59,r'SP-\d{4}'):
 image=photo(59,xref);title=loc(code+' Süpürgelik',code+' Skirting Profile',code+' Плинтус',code+' وزرة')
 add({'id':'door-profile-'+code.lower(),'code':code,'modelId':'model-door-profile-'+code.lower(),'name':title,'modelName':title,'productType':'door-profile','saleUnit':'piece','salePriceMinor':None,'salePrice':None,'availability':'unknown','assetHashes':[image],'coverIndex':0,'categoryIds':['kapilar','kapi-profiller'],'specs':[],'description':loc('Ölçü, yüzey ve miktar için teklif isteyin.','Request a quote for dimensions, finish and quantity.','Запросите предложение на размеры, покрытие и количество.','اطلب عرضاً للمقاس والسطح والكمية.')},59)
profile_image=next(im for im in doc[60].get_images()if im[2]>1000);digest=photo(60,profile_image[0])
for code in ['NDP 101','NDP 102']:
 title=loc(code+' Pervaz Profili',code+' Architrave Profile',code+' Наличник',code+' إطار تغطية')
 add({'id':'door-profile-'+code.lower().replace(' ','-'),'code':code,'modelId':'model-door-profile-'+code.lower().replace(' ','-'),'name':title,'modelName':title,'productType':'door-profile','saleUnit':'piece','salePriceMinor':None,'salePrice':None,'availability':'unknown','assetHashes':[digest],'coverIndex':0,'categoryIds':['kapilar','kapi-profiller'],'specs':[],'description':loc('Katalog görseli NDP 101 ve NDP 102 profillerini birlikte gösterir. Seçili profil ve ölçü için teklif isteyin.','The catalogue image shows NDP 101 and NDP 102 together. Request a quote for the selected profile and dimensions.','На фото из каталога показаны NDP 101 и NDP 102. Запросите предложение на выбранный профиль и размеры.','تعرض صورة الكتالوج مقطعي NDP 101 وNDP 102 معاً. اطلب عرضاً للمقطع والمقاس المطلوبين.')},60)
for p in products:p['images']=['/media/'+p['id']+'/'+str(i)for i,_ in enumerate(p['assetHashes'])]
ids=[p['id']for p in products];assert len(set(ids))==len(ids)
price_text='\n'.join(price_doc[i].get_text()for i in range(1,4))
source_amounts={int(v.replace('.',''))*100 for v in re.findall(r'([\d.]+)\s*TL',price_text)}
assert all(p['salePriceMinor']in source_amounts for p in products if p['salePriceMinor']is not None)
for p in products:
 if p['salePriceMinor']is None:continue
 family=p['door']['family'];page=price_doc[{'Klasik':1,'Elegant':2,'Premium':3,'Deluxe':3}[family]].get_text(sort=True)
 if family=='Premium':page=page.split('Deluxe')[0]
 if family=='Deluxe':page=page.split('Deluxe',1)[1]
 finish=next(name for name,(group,_)in finishes.items()if group==p['door']['finishGroup'])
 row=re.search(re.escape(finish)+r'\s+([\d.]+)\s*TL\s+(\d+)\s*USD\s+(\d+)\s*EUR',page)
 assert row and int(row[1].replace('.',''))*100==p['salePriceMinor'],p['id']
 assert int(row[2])*100==p['sourcePrice']['USD']and int(row[3])*100==p['sourcePrice']['EUR'],p['id']
category_names={'kapilar':loc('Kapılar','Doors','Двери','الأبواب'),'kapi-camli':loc('Camlı kapılar','Glazed doors','Остеклённые двери','أبواب مزججة'),'kapi-profiller':loc('Süpürgelik ve pervaz','Skirting and architraves','Плинтусы и наличники','وزرات وإطارات تغطية')}
for key,(_,title)in finishes.items():category_names['kapi-'+finishes[key][0]]=title
categories=[{'id':key,'parentId':None if key=='kapilar'else'kapilar','name':title,'count':sum(key in p['categoryIds']for p in products)}for key,title in category_names.items()]
data={'schema':1,'version':'NDECOR-R4-2026-11-10','sourceDocuments':[{'name':p.name,'sha256':sha(p.read_bytes())}for p in [CATALOGUE,PRICES]],'publicationReady':False,'reviewRequired':True,'products':products,'categories':categories,'assets':assets,'policy':{'domesticMinimumSets':5,'internationalMinimumSets':10,'minimumBasis':'aggregate_door_sets_per_delivery_country','vatIncluded':False,'freightIncluded':False,'delivery':'EXW Izmir','foreignPriceBasis':'TRY_divided_by_week_to_date_highest_Tcmb_ForexSelling','hardwareIncluded':False,'handleFromMinor':28000,'handleAverageIndicativeMinor':80000,'specialHeightsCm':[212,220]},'specialDoors':{'cataloguePage':62,'catalogueFireRatingMinutes':[30,60,90,120],'requiresProjectQuoteAndCertification':True}}
(ROOT/'data/door-catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for offset in range(0,len(products),36):
 group=products[offset:offset+36];sheet=Image.new('RGB',(1440,((len(group)+5)//6)*300),'#f5f2e9');draw=ImageDraw.Draw(sheet)
 for j,p in enumerate(group):
  asset=assets[p['assetHashes'][0]];im=Image.open(ROOT/'web'/asset['path'].lstrip('/'));im.thumbnail((228,260));x=(j%6)*240+(240-im.width)//2;y=(j//6)*300;sheet.paste(im,(x,y));draw.text(((j%6)*240+8,y+263),p['id'],fill='#172d38')
 sheet.save(OUT/('contact-sheet-'+str(offset//36+1)+'.jpg'))
receipt={'products':len(products),'interiorVariants':53,'glazedVariants':sum(counts.values()),'profiles':9,'uniqueImages':len(assets),'pricedVariants':sum(p['salePriceMinor']is not None for p in products),'models':len(set(p['modelId']for p in products)),'sourceDocuments':data['sourceDocuments'],'reviewRequired':True}
(OUT/'import.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
