#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_marketplace_taxonomy.py
# Açıklama   : Ham ürün başlığı ve gerçek kaynak kategorisinden değişmez mağaza türlerini çıkarır.
import re
from native_catalog import fold,loc
from native_catalog_taxonomy import TYPES

SUBTYPE_LABELS={key:labels for key,_,labels in TYPES}
SUBTYPE_LABELS.update({
 'boxers':['Boxer Modelleri','Boxers','Боксеры','البوكسر','Boxershorts','Bokserlər','Боксёрлер','Bokserler','Bokserlar','Боксерлер','شورت باکسر'],
 'sleeves':['Penis Kılıfları','Penis Sleeves','Насадки на пенис','أغلفة القضيب','Penishüllen','Penis qılıfları','Пенис қаптамалары','Penis örtükleri','Penis qoplamalari','Пенис каптамалары','روکش‌های آلت'],
 'chastity':['Kafes ve Kilitler','Cages and Locks','Клетки и замки','الأقفاص والأقفال','Käfige und Schlösser','Qəfəslər və kilidlər','Торлар мен құлыптар','Kapasalar we gulplar','Qafaslar va qulflar','Торлор жана кулпулар','قفس‌ها و قفل‌ها'],
 'dice':['Oyun Zarları','Game Dice','Игральные кости','نرد الألعاب','Spielwürfel','Oyun zərləri','Ойын сүйектері','Oýun zarlary','O‘yin zarlari','Оюн чүкөлөрү','تاس‌های بازی'],
 'cards':['Kart Oyunları','Card Games','Карточные игры','ألعاب البطاقات','Kartenspiele','Kart oyunları','Карта ойындары','Kart oýunlary','Karta o‘yinlari','Карта оюндары','بازی‌های کارتی'],
 'games':['Çift Oyunları','Couples Games','Игры для пар','ألعاب للأزواج','Spiele für Paare','Cüt oyunları','Жұптарға арналған ойындар','Jübüt oýunlary','Juftliklar o‘yinlari','Жубайлар оюндары','بازی‌های زوج‌ها'],
 'breastforms':['Göğüs Formları','Breast Forms','Накладные формы груди','قوالب الصدر','Brustformen','Sinə formaları','Кеуде пішіндері','Döş şekilleri','Ko‘krak shakllari','Көкүрөк формалары','فرم‌های سینه'],
 'machines':['Seks Makineleri','Sex Machines','Секс-машины','أجهزة جنسية','Sexmaschinen','Seks maşınları','Секс машиналары','Seks maşynlary','Seks mashinalari','Секс машиналары','دستگاه‌های جنسی'],
 'positioning':['Pozisyon Destekleri','Positioning Aids','Опоры для позиций','وسائل دعم الوضعيات','Positionshilfen','Pozisiya dəstəkləri','Қалып тіректері','Duruş goldawlary','Holat tayanchlari','Абалды колдоочу буюмдар','وسایل کمکی وضعیت'],
})

# Sayısal kimlikler yalnız ait oldukları platformda anlam taşır.
SOURCE_TYPES={
 '3101':('lingerie','boxers'),'3102':('lingerie','tights'),'3103':('lingerie','sets'),
 '3104':('lingerie','garters'),'3108':('lingerie','briefs'),'3110':('lingerie','chemises'),
 '3100':('lingerie','chemises'),'3097':('lingerie','costumes'),
 '5234':('toys','masturbators'),'5092':('toys','plugs'),'5097':('toys','vibrators'),
 '5094':('toys','rings'),'5243':('toys','dildos'),'5242':('toys','sleeves'),
 '5095':('toys','pumps'),'5235':('toys','breastforms'),
}
SOURCE_ROOTS={'3096':'lingerie','3097':'lingerie','3098':'accessories','5240':'toys','5241':'toys'}
NAME_TYPES={
 'fantezi boxer':('lingerie','boxers'),'boxer':('lingerie','boxers'),
 'fantezi corap':('lingerie','tights'),'coraplar':('lingerie','tights'),
 'fantezi ic camasir takimi':('lingerie','sets'),'ic giyim takimlari':('lingerie','sets'),
 'fantezi jartiyer':('lingerie','garters'),'jartiyer':('lingerie','garters'),
 'fantezi string':('lingerie','briefs'),'fantezi gecelik':('lingerie','chemises'),
 'fantezi babydoll':('lingerie','chemises'),'fantezi kostum':('lingerie','costumes'),
 'masturbator':('toys','masturbators'),'anal oyuncak':('toys','plugs'),
 'vibrator':('toys','vibrators'),'penis halkasi':('toys','rings'),
 'dildo':('toys','dildos'),'penis kilifi':('toys','sleeves'),
 'penis pompasi':('toys','pumps'),'yapay gogus':('toys','breastforms'),
 'kayganlastiricilar':('care','lubricants'),'kayganlastirici':('care','lubricants'),
 'prezervatif':('care','condoms'),'masaj yaglari':('care','oils'),
 'oyuncak temizleyici':('care','cleaners'),'hediye setleri':('gifts',None),
}

def _match(pattern,text):return re.search(pattern,text) is not None

def _garment_title(text):
 for subtype,pattern in [
  ('costumes',r'\b(?:kostum|fantasy costume|hizmetci)\w*'),
  ('tights',r'\b(?:vucut cora|kulotlu cora|body stocking)\w*'),
  ('bodies',r'\b(?:body|bodysuit|bodi|teddy)\b'),
  ('boxers',r'\bboxer\w*'),('briefs',r'\bjockstrap\w*')]:
  if _match(pattern,text):return subtype
 return None

def _title_type(text):
 for group,subtype,pattern in [
  ('couples','dice',r'\bzar(?:i|lar(?:i)?|li)?\b|\bdice\b'),
  ('couples','cards',r'\b(?:kart|karti|kartlari|tarot|card)\b'),
  ('couples','games',r'\btombala\w*|denge oyunu|oyun carki|kamasutra.*oyun'),
  ('care','lubricants',r'\bkayganlastirici\w*|\blubricant\w*'),
  ('care','oils',r'\bmasaj yag\w*|\bmassage oil\w*'),
  ('care','condoms',r'\b(?:prezervatif|kondom|condom)\w*'),
  ('care','cleaners',r'\b(?:oyuncak temizleyici|toy cleaner|anal cleaner|temizleyici|anal dus)\w*'),
  ('toys','sleeves',r'\bpenis kilif\w*'),('toys','pumps',r'\bpomp[ao]\w*'),
  ('toys','rings',r'\b(?:penis|testis) halka\w*|\bpenis yuzug\w*'),
  ('toys','masturbators',r'\bmasturbator\w*|\bsuni vajina\b|\byapay vajina\b'),
  ('toys','vibrators',r'\bvibrator\w*'),('toys','plugs',r'\bplug\w*|\banal tikac\w*'),
  ('toys','dildos',r'\bdildo\w*|\byapay penis\b'),
  ('accessories','straps',r'\b(?:harness|kemer|kayis|belden bagla)\w*'),
  ('accessories','accessories',r'\b(?:kelepce|kirbac|baglama|kiskac|maske|goz band|agiz topu|ball gag|bdsm|fetis)\w*'),
  ('lingerie','garters',r'\bjartiyer\w*'),('lingerie','chemises',r'\b(?:gecelik|babydoll)\w*'),
  ('lingerie','bras',r'\bsutyen\w*'),('lingerie','briefs',r'\b(?:kulot|kilot|tanga|string)\w*'),
  ('lingerie','pajamas',r'\bpijama\w*'),('lingerie','robes',r'\bsabahlik\w*'),
  ('lingerie','shapewear',r'\bkorse\w*'),('lingerie','tights',r'\bcorap\w*'),
 ]:
  if _match(pattern,text):return group,subtype
 return None

def classify_marketplace(title,source_categories,platform='trendyol'):
 """Ham başlık ve kaynak ağacını sınıflandırır; ürün, stok veya onay verisi üretmez."""
 if not isinstance(title,str):raise TypeError('RAW_SOURCE_TITLE_REQUIRED')
 if not isinstance(source_categories,(list,tuple)):raise TypeError('SOURCE_CATEGORY_LIST_REQUIRED')
 rows=[{'id':str(row.get('id','')),'name':row.get('name',row.get('title',''))}for row in source_categories if isinstance(row,dict)]
 rows=[row for row in rows if isinstance(row['name'],str)]
 text=fold(title);ids={row['id']for row in rows}if platform=='trendyol'else set()
 leaf=next((row for row in reversed(rows)if platform=='trendyol'and row['id']in SOURCE_TYPES),None)
 evidence={'basis':'unresolved','sourceCategoryId':None,'sourceCategoryName':None}
 group=subtype=None
 garment=_garment_title(text)
 clothing_context=ids.intersection({'3096','3097'})or(leaf and SOURCE_TYPES[leaf['id']][0]=='lingerie')or(rows and NAME_TYPES.get(fold(rows[-1]['name']),(None,))[0]=='lingerie')or _match(r'\b(?:ic giyim|dantel|lingerie)\b',text)
 if garment=='bodies'and _match(r'\bbody\b',text)and not _match(r'\b(?:bodysuit|bodi|teddy)\b',text)and not clothing_context:garment=None
 if garment and not(leaf and SOURCE_TYPES[leaf['id']][0]=='toys'):
  group,subtype='lingerie',garment;evidence['basis']='raw_title'
 elif _match(r'\b(?:penis kafes|chastity|penis kilid)\w*',text):
  group,subtype='accessories','chastity';evidence['basis']='raw_title'
 elif _match(r'\banal cleaner\b|\banal dus\b',text):
  group,subtype='care','cleaners';evidence['basis']='raw_title'
 elif _match(r'\bseks makine\w*|\bsex machine\w*',text):
  group,subtype='toys','machines';evidence['basis']='raw_title'
 elif _match(r'\b(?:seks pozisyon yastigi|pozisyon yastigi|kalca destek|kucak askisi)\b',text):
  group,subtype='accessories','positioning';evidence['basis']='raw_title'
 elif leaf:
  group,subtype=SOURCE_TYPES[leaf['id']];evidence={'basis':'source_category_id','sourceCategoryId':leaf['id'],'sourceCategoryName':leaf['name']}
 elif rows and fold(rows[-1]['name'])in NAME_TYPES:
  group,subtype=NAME_TYPES[fold(rows[-1]['name'])];evidence={'basis':'source_category_name','sourceCategoryId':rows[-1]['id'],'sourceCategoryName':rows[-1]['name']}
 else:
  match=_title_type(text)
  if match:group,subtype=match;evidence['basis']='raw_title'
  elif _match(r'\bhediye seti\b|\bhediye kutusu\b',text):group='gifts';evidence['basis']='raw_title'
  elif platform=='trendyol':
   row=next((row for row in reversed(rows)if row['id']in SOURCE_ROOTS),None)
   if row:group=SOURCE_ROOTS[row['id']];evidence={'basis':'source_category_id','sourceCategoryId':row['id'],'sourceCategoryName':row['name']}
  if group is None and _match(r'\bic giyim\b',text):group='lingerie';evidence['basis']='raw_title'
 if group=='toys'and subtype in ['vibrators','dildos','rings','masturbators']and _match(r'uzaktan kumanda|telefon kontrol|partnerli',text):group='couples'
 category_ids=[];categories=[]
 if group:
  root='sg_'+group;category_ids.append(root)
  keys=[subtype]if subtype else[]
  if group=='lingerie'and _match(r'\bbuyuk beden\b',text)and'plus'not in keys:keys.append('plus')
  for key in keys:
   identifier=root+'_'+key;category_ids.append(identifier);categories.append({'id':identifier,'parentId':root,'name':loc(SUBTYPE_LABELS[key]),'slug':group+'-'+key})
 return {'schema':1,'group':group,'subtype':subtype,'categoryIds':category_ids,'categories':categories,'evidence':evidence,'needsReview':group is None}
