"""Extract real cabinet-front models from the editable PDF page composition.

The public images are lossless renders of product-only PDF regions. Supplier
headers, footers, cover logos and company history are never public assets.
"""
from pathlib import Path
import fitz,hashlib,json,re,math,unicodedata,xml.etree.ElementTree as ET,sys,io
from PIL import Image,ImageDraw
ET.register_namespace('','http://www.w3.org/2000/svg')
ET.register_namespace('xlink','http://www.w3.org/1999/xlink')

ROOT=Path(__file__).resolve().parents[1];DESKTOP=Path('C:/Users/Hamza ÖZBALKAN/Desktop')
sys.path.insert(0,str(ROOT))
from lib.cabinet_front_decoration import caption_rules,caption_rule_fragments,remove_caption_rules,clean_fragment_pixels
OUT=ROOT/'artifacts/cabinet-fronts-2026';ASSETS=ROOT/'web/assets/fronts';OUT.mkdir(exist_ok=True);ASSETS.mkdir(parents=True,exist_ok=True)
FILES={'pvc':'Göktaş Kapak Kataloğu 2026 - Yatay.pdf','lacquer':'Göktaş Lake Kapak Kataloğu 2026.pdf','lakePrice':'LAKE KAPAK FİYAT LİSTESİ 2026-3.pdf','pvcPrice':'MEBRANE KAPAK 2026-3 NOLU FİYAT LİSTESİ.pdf'}
sha=lambda b:hashlib.sha256(b).hexdigest();docs={key:fitz.open(DESKTOP/name)for key,name in FILES.items()};hashes={key:sha((DESKTOP/name).read_bytes())for key,name in FILES.items()}
def loc(tr,en,ru,ar):return {'tr':tr,'en':en,'ru':ru,'ar':ar}
groups={
 0:'206 207 208 209 210 212 224 228 229 230 239 301',
 30:'201 204 205 244 720 269 290 291 296 297 711 302 303 305 308',
 50:'246 248 260 261 287 289 701 702 703 704 705 707 709 710 712 713 715 721 722 724 728 731 732 733 735 736 739 740 741',
 110:'101 102 103 104 107 108 109 110 111',
 75:'267 273 285 286 288 292 725 716 723 729 726 306 299',
 350:'106 225 265 266 298 293 294 295 717 718 727 730 714 719 706 737 743 744 745 304 307 113 112 114 115 116 117 300',
 450:'GT01 GT02 GT03 GT04 GT06 GT07'}
fees={code:amount*100 for amount,codes in groups.items()for code in codes.split()}
for n in range(1,13):fees['GB'+str(n)]=(110 if n<=6 else 350)*100
base={'soft':252500,'supermatt':273500,'emboss':268000,'matt':242500,'glossy':262000}
lakeGroups={'9010':349500,'1013':349500,'1024':349500,'7037':349500,'6001':368000,'5010':368000,'1018':368000,'7043':368000,'7044':368000,'7040':368000,'7018':368000,'7023':368000}
aliases={'lake beyaz':'9010','lake cappucino':'1024','lake cappuccino':'1024','lake krem':'1013'}
assets={};records={};unparsed=[];all_cells=[]
text_free_pages={}
def fold(value):return ''.join(c for c in unicodedata.normalize('NFKD',value.lower().replace('ı','i'))if not unicodedata.combining(c))
def text_clean(text):
 text=re.sub(r'(?<=\d)[ \t]+(?=\d)', '',text)
 text=re.sub(r'(?:[A-ZİŞÜÇÖĞ] ){3,}[A-ZİŞÜÇÖĞ]',' ',text)
 return re.sub(r'\s+',' ',text).strip()
def code_from(text,override=None):
 if override:return override
 cleaned=re.sub(r'(?<=\d)[ \t]+(?=\d)','',text)
 pref=re.search(r'\b(GK[ABP]?|GB|GT|GM)[ -]?(\d{1,4}(?:-\d)?)(?:\s*TİP\s*(\d{3}))?',cleaned)
 if pref:return pref.group().strip()
 matches=re.findall(r'(?<![A-Za-z0-9])\d{3}(?:-\d)?(?!\d)',cleaned)
 # RAL colours and measurements are excluded by the source layout/explicit overrides.
 return matches[0]if matches else None
def color_from(text,code):
 lines=[re.sub(r'\s+',' ',line).strip()for line in text.splitlines()if line.strip()]
 for line in lines:
  if re.search(r'^(?:Soft |Süpermat |Süpermatt |Supermat |Lake |Parlak |P\. |Ral |RAL |Bute |Beyaz |Açık |Koyu |Silver |Ilgaz |Tortuga |Ventura |Çamlıca |Antik |Ahşap |Pelit |Kafkas |Kahve |Su Yeşili|Antrasit|Kaşmir|Cappuccino|Yeni Gri|Krem|Siyah|Metalik)',line,re.I):
   if 'S E R'in line or 'S E R'==line:return ''
   if not re.fullmatch(r'[A-ZÇĞİÖŞÜ ]+',line)or re.search(r'RAL\s*\d',line,re.I):return re.split(r'\s+Lacquer\b',line,flags=re.I)[0]
 return ''
terms={
 'beyaz':('White','белый','أبيض'),'krem':('Cream','кремовый','كريمي'),'cappucino':('Cappuccino','капучино','كابتشينو'),'cappuccino':('Cappuccino','капучино','كابتشينو'),
 'aytaşı':('Moonstone','лунный камень','حجر القمر'),'kaşmir':('Cashmere','кашемир','كشمير'),'ipek':('Silk','шелковистый','حريري'),'gri':('Grey','серый','رمادي'),
 'pudra':('Powder','пудровый','بودري'),'mint':('Mint','мятный','نعناعي'),'yeşili':('Green','зелёный','أخضر'),'yeşil':('Green','зелёный','أخضر'),
 'orman':('Forest','лесной','غابي'),'kozmik':('Cosmic','космический','كوزميك'),'mavi':('Blue','синий','أزرق'),'lacivert':('Navy blue','тёмно-синий','كحلي'),
 'vizon':('Taupe','тауп','بني رمادي'),'antrasit':('Anthracite','антрацит','أنثراسيت'),'açık':('Light','светлый','فاتح'),'koyu':('Dark','тёмный','داكن'),
 'denim':('Denim','деним','دنيم'),'retro':('Retro','ретро','ريترو'),'somon':('Salmon','лососёвый','سلموني'),'su':('Water','водный','مائي'),
 'kiremit':('Terracotta','терракотовый','قرميدي'),'siyah':('Black','чёрный','أسود'),'dişbudak':('Ash','ясень','مران'),'italyan':('Italian','итальянский','إيطالي'),
 'ceviz':('Walnut','орех','جوز'),'koton':('Cotton','коттон','قطني'),'kahve':('Brown','коричневый','بني'),'ladin':('Spruce','ель','تنوب'),
 'meşe':('Oak','дуб','بلوط'),'oksit':('Oxide','оксид','أكسيدي'),'taşbahçe':('Stonegarden','Стоунгарден','ستون غاردن'),'kiraz':('Cherry','вишня','كرز'),
 'antik':('Antique','антик','عتيق'),'ahşap':('Wood','дерево','خشبي'),'pelit':('Pelit','Пелит','بيليت'),'metalik':('Metallic','металлик','معدني'),
 'parlak':('Glossy','глянцевый','لامع'),'mat':('Matt','матовый','مطفي'),'yeni':('New','новый','جديد'),'lake':('Lacquer','лак','لاكيه'),
 'soft':('Soft','Soft','سوفت'),'süpermat':('Supermatt','суперматовый','فائق المطفي'),'süpermatt':('Supermatt','суперматовый','فائق المطفي')}
def color_loc(color):
 if not color:return loc('Katalog modeli','Catalogue model','Модель из каталога','موديل الكتالوج')
 tokens=color.split();result=[]
 for language in range(3):result.append(' '.join(terms.get(token.lower(),(token,token,token))[language]for token in tokens))
 return loc(color,*result)
def public_code(code):return re.sub(r'^G(?:K|B|T|M)','ND',code)
def native_asset(key,page_index,cell):
 page=docs[key][page_index];images=[fitz.Rect(info['bbox']) for info in page.get_image_info()if cell.contains((fitz.Rect(info['bbox']).tl+fitz.Rect(info['bbox']).br)/2)]
 if key=='pvc' and page_index==96:images=[fitz.Rect(info['bbox'])&cell for info in page.get_image_info()if (fitz.Rect(info['bbox'])&cell).get_area()>30]
 if not images:return None
 rect=images[0];
 for image in images[1:]:rect|=image
 rect&=page.rect
 if rect.width<15 or rect.height<25:return None
 # Native PDF vector text is inspected before any region is made public.
 inside=page.get_text(clip=rect)
 branded=bool(re.search(r'g[oö]kta[sş]|rinodoor|goktasmobilya',inside,re.I))
 # Exclude the PDF's editable text layer, preserving the original raster/photo
 # layers and geometry. This is native vector rendering, not photo retouching.
 page_key=(key,page_index)
 if page_key not in text_free_pages:
  derivative=fitz.open();derivative.insert_pdf(docs[key],from_page=page_index,to_page=page_index)
  clean=derivative[0]
  for block in clean.get_text('blocks'):
   if len(block)>6 and block[6]==0:clean.add_redact_annot(fitz.Rect(block[:4]),fill=False,cross_out=False)
  clean.apply_redactions(images=0,graphics=0,text=0)
  remove_caption_rules(clean)
  text_free_pages[page_key]=derivative
 scale=min(3,1800/max(rect.width,rect.height));pix=text_free_pages[page_key][0].get_pixmap(matrix=fitz.Matrix(scale,scale),clip=rect,alpha=False)
 rules=caption_rules(page);fragments=caption_rule_fragments(page)+rules
 if fragments:
  cleaned=clean_fragment_pixels(pix,scale,fragments);buffer=io.BytesIO();cleaned.save(buffer,format='PNG');body=buffer.getvalue()
 else:body=pix.tobytes('png')
 digest=sha(body)
 (ASSETS/(digest+'.png')).write_bytes(body)
 assets[digest]={'path':'/assets/fronts/'+digest+'.png','sha256':digest,'bytes':len(body),'width':pix.width,'height':pix.height,'sourceDocumentSha256':hashes[key],'sourcePage':page_index+1,'sourceRect':[round(v,5)for v in rect],'nativePdfProductRegion':True,'nativeTextLayerExcluded':True,'photoPixelsRetouched':False,'supplierTextInsideRegion':False,'sourceSupplierTextInsideRegion':branded,'reviewRequired':True}
 return digest
def add_cell(key,page_index,cell,series,kind='front',override=None,color_override=None):
 page=docs[key][page_index];text_region=fitz.Rect(cell);text_region.y1=min(page.rect.height-20,text_region.y1+26);raw=page.get_text(clip=text_region,sort=False);code=code_from(raw,override);color=color_override if color_override is not None else color_from(raw,code)
 color=re.sub(r'R\s+AL|R\s+A\s+L','RAL',color,flags=re.I)
 if not code:unparsed.append({'document':key,'page':page_index+1,'rect':list(cell),'text':text_clean(raw)});return
 image=native_asset(key,page_index,cell)
 if not image:unparsed.append({'document':key,'page':page_index+1,'code':code,'reason':'no_product_image'});return
 material='lacquer'if series=='lacquer'else'pvc'if series in base else series
 code_key=re.sub(r'\s+','',code).upper();fee=fees.get(code_key);rate=None;reason=None
 if material=='pvc':
  if fee is not None and series in base:rate=base[series]+fee
  else:reason='model_or_surface_price_not_listed'
 elif material=='lacquer':
  ral_match=re.search(r'(?:RAL|Ral)\s*(\d{4})',color);ral=ral_match[1]if ral_match else {fold(k):v for k,v in aliases.items()}.get(fold(color))
  if ral in lakeGroups and fee is not None:rate=lakeGroups[ral]+fee
  else:reason='model_or_ral_group_not_listed'
 else:reason='material_or_accessory_price_not_listed'
 if '/'in color or re.search(r'\s-\s',color):rate=None;reason='mixed_surface_requires_quote'
 if kind!='front':rate=None
 identity=material+'|'+code_key+'|'+color.lower();public=public_code(code)
 if identity in records:
  p=records[identity]
  if image not in p['assetHashes']:p['assetHashes'].append(image)
  p['sourceEvidence'].append({'documentSha256':hashes[key],'page':page_index+1,'sourceCode':code,'sourceColor':color});return
 ptype='cabinet-front'if kind=='front'else'cabinet-profile';title=loc(public+' Dolap Kapağı',public+' Cabinet Front',public+' Мебельный фасад',public+' واجهة خزانة')if kind=='front'else loc(public+' Tamamlayıcı Ürün',public+' Complementary Product',public+' Дополнительный элемент',public+' منتج مكمل')
 material_name={'pvc':loc('PVC / Membran','PVC / membrane','ПВХ / мембрана','بي في سي / ممبران'),'lacquer':loc('Lake','Lacquer','Лак','لاكيه'),'acrylic':loc('Akrilik / Süpermat','Acrylic / supermatt','Акрил / супермат','أكريليك / فائق المطفي'),'complement':loc('Tamamlayıcı','Complementary','Дополнительный','مكمل'),'profile':loc('Profil','Profile','Профиль','مقطع'),'headboard':loc('Karyola başlığı','Headboard','Изголовье','لوح رأس السرير'),'mirror':loc('Ayna çerçevesi','Mirror frame','Рама зеркала','إطار مرآة'),'self-handled':loc('Kendinden kulplu','Self-handled','Со встроенной ручкой','بمقبض مدمج'),'glazed':loc('Camlı model','Glazed model','Остеклённая модель','موديل مزجج')}[material]
 colour=color_loc(color);variant={lang:material_name[lang]+' · '+colour[lang]for lang in ['tr','en','ru','ar']}
 p={'id':'front-'+sha(identity.encode())[:16],'code':public,'sourceCode':code,'modelId':('model-front-'if kind=='front'else'model-front-accessory-')+re.sub(r'[^a-z0-9-]','-',public.lower()),'name':title,'modelName':title,'variantColor':variant,'productType':ptype,'saleUnit':'m2'if kind=='front'else'piece','currency':'TRY','salePriceMinor':rate,'salePrice':rate/100 if rate is not None else None,'availability':'unknown','assetHashes':[image],'coverIndex':0,'categoryIds':['dolap-kapaklari','kapak-'+series],
 'description':loc('Ölçüye göre dolap kapağı. En, boy ve adet girerek toplam alanı hesaplayın. Görsel, katalogdaki model ve yüzey örneğidir; mobilya gövdesi ve aksesuarlar dahil değildir.','Made-to-measure cabinet fronts. Enter width, height and quantity to calculate the area. The image shows the catalogue model and surface; furniture carcasses and hardware are excluded.','Мебельный фасад по размерам. Укажите ширину, высоту и количество для расчёта площади. Фото показывает модель и покрытие из каталога; корпус мебели и фурнитура не включены.','واجهة خزانة حسب المقاس. أدخل العرض والارتفاع والعدد لحساب المساحة. الصورة مرجع للموديل والسطح؛ جسم الأثاث والملحقات غير مشمولة.'),
 'specs':[{'label':loc('Yüzey','Surface','Покрытие','السطح'),'value':material_name},{'label':loc('Renk','Colour','Цвет','اللون'),'value':colour}],
 'front':{'material':material,'series':series,'priceBasis':'square_metre'if kind=='front'else'quote','minimumApplies':material in ['pvc','lacquer'],'taxIncluded':False,'supplierFreightIncluded':True,'deliveryTermsRequireConfirmation':True,'priceListDate':'2026-09-10','modelSurchargeMinor':fee,'priceReason':reason,'glazingPriceVerified':False},'sourceEvidence':[{'documentSha256':hashes[key],'page':page_index+1,'sourceCode':code,'sourceColor':color}]}
 records[identity]=p;all_cells.append({'id':p['id'],'page':page_index+1,'code':code,'colour':color,'series':series,'priceMinor':rate})
def grid(page_no,cols,rows,series,kind='front',row_columns=None,overrides=None,margin=0):
 page=docs['pvc'][page_no-1];w,h=page.rect.width,page.rect.height
 for y in range(rows):
  rowcols=(row_columns or [cols]*rows)[y]
  for x in range(rowcols):
   cell=fitz.Rect(margin+x*(w-2*margin)/rowcols,45+y*(h-80)/rows,margin+(x+1)*(w-2*margin)/rowcols,45+(y+1)*(h-80)/rows)
   add_cell('pvc',page_no-1,cell,series,kind,(overrides or {}).get((y,x)))
# The source layouts are deliberately explicit; do not infer models from page numbers.
for n in list(range(10,22))+[28,29]:grid(n,2,1,'soft')
for n in [25,26,27]:grid(n,3,2,'soft')
for n in [22,23,24]:grid(n,1,1,'soft',overrides={(0,0):{22:'309',23:'292',24:'295'}[n]})
for n in [32,33]:grid(n,2,1,'supermatt')
for n in [36,37,38,39]:grid(n,3,2,'emboss')
for n in [42,43]:grid(n,3,2,'matt')
for n in [46,47]:grid(n,3,2,'glossy')
for n in [50,51,52,53]:grid(n,3,2,'lacquer')
grid(54,3,2,'soft')
for n in range(55,60):grid(n,1,1,'soft',overrides={(0,0):{55:'118',56:'119',57:'120',58:'299',59:'300'}[n]})
for n in range(61,70):grid(n,2,1,'soft')
grid(70,4,2,'glazed',row_columns=[4,3],margin=60);grid(71,4,2,'glazed',row_columns=[4,3],margin=60);grid(72,6,1,'glazed',overrides={(0,5):'GB 13'})
grid(73,3,2,'complement','profile')
grid(74,3,3,'complement','profile',row_columns=[3,3,1],overrides={(0,0):'GM 2',(0,1):'GM 2 TİP 204',(0,2):'GM 2 TİP 203',(1,0):'GM 2 TİP 201',(1,1):'GM 2 TİP 223',(1,2):'GM 2 TİP 701',(2,0):'GM 2 TİP 727'})
grid(75,2,3,'complement','profile')
for page_no,codes in [(76,list(range(1,9))),(77,[9,10,11,12,13,21,22])]:
 page=docs['pvc'][page_no-1]
 for info,number in zip(page.get_image_info(),codes):
  box=fitz.Rect(info['bbox']);add_cell('pvc',page_no-1,box+(-8,-4,8,22),'profile','profile',override='GKP '+str(number))
for n in [78,79]:grid(n,2,1,'headboard','profile')
for n in [80,81]:grid(n,3,1,'mirror','profile')
for n in [84,85,86]:grid(n,4,1,'acrylic')
for n in [90,91]:grid(n,4,1,'self-handled')
grid(92,2,1,'self-handled');grid(93,3,1,'self-handled')
for code,(top,bottom)in zip(['6478','5890','4261','6250'],[(100,217),(221,328),(332,441),(445,557)]):add_cell('pvc',96,fitz.Rect(85,top,750,bottom),'profile','profile',override=code)
# Lake catalogue: preserve both the staged image and its product-only detail region.
for page_no in [6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36]:
 page=docs['lacquer'][page_no-1];text=page.get_text(sort=True);code=re.search(r'MODEL\s*(?:I\s*)?(\d{3})',text)
 if not code:unparsed.append({'document':'lacquer','page':page_no,'text':text});continue
 colour=re.split(r'\b(?:I|RENK)\b',re.sub(r'\s+',' ',text).strip())[-1];colour=re.sub(r'\s+\d{1,4}$','',colour).strip()
 if page_no==26:colour='RAL 9007'
 cell=fitz.Rect(0,0,page.rect.width,page.rect.height-40);add_cell('lacquer',page_no-1,cell,'lacquer',override=code[1],color_override=colour)
 if page_no in [6,8,10,14,16,18,22,24,26,30,32,34]:
  detail=docs['lacquer'][page_no];add_cell('lacquer',page_no,fitz.Rect(30,35,detail.rect.width-15,detail.rect.height-45),'lacquer',override=code[1],color_override=colour)
# Explicitly identified room photographs are gallery/collection references.
for page_no,series,code,colour in [(9,'soft','303','Soft Kaşmir / Safir Meşe'),(31,'supermatt','260-2','Süpermat Su Yeşili'),(35,'emboss','301','Ilgaz Ladin / Soft Antrasit'),(45,'glossy','735','Parlak Beyaz'),(49,'lacquer','743','Lake Beyaz / RAL 7040'),(60,'soft','112','Soft Beyaz')]:
 page=docs['pvc'][page_no-1];add_cell('pvc',page_no-1,fitz.Rect(0,0,page.rect.width,page.rect.height-30),series,override=code,color_override=colour)
products=list(records.values())
for p in products:p['images']=['/media/'+p['id']+'/'+str(i)for i in range(len(p['assetHashes']))]
series_names={'soft':loc('Soft PVC','Soft PVC','ПВХ Soft','بي في سي سوفت'),'supermatt':loc('Süpermat PVC','Supermatt PVC','Суперматовый ПВХ','بي في سي فائق المطفي'),'emboss':loc('Embos PVC','Embossed PVC','Текстурный ПВХ','بي في سي منقوش'),'matt':loc('Mat PVC','Matt PVC','Матовый ПВХ','بي في سي مطفي'),'glossy':loc('Parlak PVC','Glossy PVC','Глянцевый ПВХ','بي في سي لامع'),'lacquer':loc('Lake kapaklar','Lacquer fronts','Лаковые фасады','واجهات لاكيه'),'glazed':loc('Camlı kapaklar','Glazed fronts','Остеклённые фасады','واجهات مزججة'),'complement':loc('Tamamlayıcılar','Complementary elements','Дополнительные элементы','عناصر مكملة'),'profile':loc('Kapak profilleri','Front profiles','Профили фасадов','مقاطع الواجهات'),'headboard':loc('Karyola başlıkları','Headboards','Изголовья','ألواح رأس السرير'),'mirror':loc('Ayna çerçeveleri','Mirror frames','Рамы зеркал','إطارات المرايا'),'acrylic':loc('Akrilik ve süpermat','Acrylic and supermatt','Акрил и супермат','أكريليك وفائق المطفي'),'self-handled':loc('Kendinden kulplu','Self-handled fronts','Фасады со встроенной ручкой','واجهات بمقبض مدمج')}
categories=[{'id':'dolap-kapaklari','parentId':None,'name':loc('Dolap kapakları','Cabinet fronts','Мебельные фасады','واجهات الخزائن'),'count':len(products)}]+[{'id':'kapak-'+key,'parentId':'dolap-kapaklari','name':name,'count':sum('kapak-'+key in p['categoryIds']for p in products)}for key,name in series_names.items()]
data={'schema':1,'version':'NODENO-fronts-2026-3','publicationReady':False,'reviewRequired':True,'sourceDocuments':[{'name':FILES[key],'sha256':hashes[key]}for key in FILES],'products':products,'categories':categories,'assets':assets,'policy':{'domesticMinimumAreaMm2':5000000,'internationalMinimumAreaMm2':10000000,'minimumMaterials':['pvc','lacquer'],'minimumBasis':'aggregate_confirmed_front_area','rounding':'ROUND_HALF_UP_PER_LINE_AREA','priceListDate':'2026-09-10','vatIncluded':False,'supplierFreightIncluded':True,'nodenoDeliveryTerms':'confirmation_required'},'sourcePricing':{'pvcSeriesMinorPerM2':base,'lakeRalMinorPerM2':lakeGroups,'modelSurchargesMinorPerM2':fees,'customRalSurchargeMinorPerM2':13000}}
(ROOT/'data/cabinet-fronts.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'candidates.json').write_text(json.dumps(all_cells,ensure_ascii=False,indent=2),encoding='utf8');(OUT/'unparsed.json').write_text(json.dumps(unparsed,ensure_ascii=False,indent=2),encoding='utf8')
for offset in range(0,len(products),30):
 group=products[offset:offset+30];sheet=Image.new('RGB',(1500,math.ceil(len(group)/6)*300),'#f5f2e9');draw=ImageDraw.Draw(sheet)
 for j,p in enumerate(group):
  asset=assets[p['assetHashes'][0]];im=Image.open(ROOT/'web'/asset['path'].lstrip('/'));im.thumbnail((240,245));x=(j%6)*250+(250-im.width)//2;y=(j//6)*300;sheet.paste(im,(x,y));draw.text(((j%6)*250+5,y+247),p['sourceCode'],fill='#172d38');draw.text(((j%6)*250+5,y+265),p['front']['series']+' / p'+str(p['sourceEvidence'][0]['page']),fill='#172d38')
 sheet.save(OUT/('front-contact-'+str(offset//30+1)+'.jpg'))
print(json.dumps({'products':len(products),'assets':len(assets),'priced':sum(p['salePriceMinor']is not None for p in products),'unparsed':len(unparsed),'brandedRegions':sum(a['supplierTextInsideRegion']for a in assets.values()),'reviewRequired':True}))
