#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_catalog_taxonomy.py
# Açıklama   : Gerçek ürün türlerinden tutarlı alt kategoriler çıkarır; ürün başlığını kategori sanmaz.
import re
from native_catalog import fold,loc

# Sıra dar ürün türünden geniş türe doğrudur; büyük beden ayrıca ilişkilendirilir.
TYPES=[
 ('garters',r'jartiyer', ['Jartiyer Takımları','Garter Sets','Комплекты с подвязками','أطقم الجوارب','Strumpfhalter-Sets','Jartiyer dəstləri','Гартер жиынтықтары','Jartýer toplumlary','Garter to‘plamlari','Гартер топтомдору','ست جوراب‌بند']),
 ('costumes',r'kostum|hizmetci', ['Kostümler','Costumes','Костюмы','الأزياء','Kostüme','Kostyumlar','Костюмдер','Lybaslar','Kostyumlar','Костюмдар','لباس‌های نمایشی']),
 ('bodies',r'body|bodysuit|bodi', ['Body Modelleri','Bodysuits','Боди','البودي','Bodys','Bodi modelləri','Боди','Bodi görnüşleri','Bodi modellari','Боди','بادی']),
 ('shapewear',r'korse|toparlayici', ['Korse ve Toparlayıcılar','Shapewear','Корректирующее бельё','الملابس المشدّة','Shapewear','Korset və yığan geyimlər','Пішіндеуші іш киім','Korsetler','Korsetlar','Корсет жана ич кийим','گن و لباس فرم‌دهنده']),
 ('robes',r'sabahlik', ['Sabahlıklar','Robes','Халаты','أردية','Morgenmäntel','Xalatlar','Халаттар','Halatlar','Xalatlar','Халаттар','روبدوشامبر']),
 ('pajamas',r'pijama', ['Pijama Takımları','Pyjama Sets','Пижамы','أطقم البيجاما','Pyjamas','Pijama dəstləri','Пижамалар','Pižama toplumlary','Pijama to‘plamlari','Пижамалар','ست پیژامه']),
 ('chemises',r'gecelik|babydoll', ['Gecelikler','Chemises and Nightdresses','Ночные сорочки','قمصان النوم','Nachthemden','Gecəliklər','Түнгі көйлектер','Gijelikler','Tungi ko‘ylaklar','Түнкү көйнөктөр','لباس خواب']),
 ('tights',r'corap', ['Çoraplar','Stockings','Чулки','الجوارب','Strümpfe','Corablar','Шұлықтар','Joraplar','Paypoqlar','Байпактар','جوراب‌ها']),
 ('leggings',r'tayt', ['Taytlar','Leggings','Легинсы','الليغينغ','Leggings','Taytlar','Леггинстер','Legginsler','Legginslar','Леггинстер','لگ‌ها']),
 ('thermal',r'termal|iclik', ['Termal İçlikler','Thermal Underwear','Термобельё','ملابس داخلية حرارية','Thermounterwäsche','Termal alt geyim','Термокөйлек','Termal iç geýim','Termal ichki kiyim','Термалдык ич кийим','لباس زیر حرارتی']),
 ('tanks',r'atlet', ['Atletler','Undershirts','Майки','القمصان الداخلية','Unterhemden','Alt köynəklər','Іш жейделер','Iç köýnekler','Ichki maykalar','Ички майкалар','زیرپوش‌ها']),
 ('sets',r'takim|set|camasiri', ['İç Giyim Takımları','Lingerie Sets','Комплекты белья','أطقم الملابس الداخلية','Dessous-Sets','Alt geyim dəstləri','Іш киім жиынтықтары','Iç geýim toplumlary','Ichki kiyim to‘plamlari','Ич кийим топтомдору','ست لباس زیر']),
 ('bras',r'sutyen', ['Sütyenler','Bras','Бюстгальтеры','حمالات الصدر','BHs','Büstqalterlər','Көкірекшелер','Býustgalterler','Byustgalterlar','Бюстгалтерлер','سوتین‌ها']),
 ('briefs',r'kulot|kilot|tanga|string', ['Külot ve Tangalar','Briefs and Thongs','Трусы и стринги','السراويل الداخلية','Slips und Strings','Alt tumanları','Іш киімдер','Içki balaklar','Ichki ishtonlar','Ич кийимдер','شورت‌ها']),
 ('dresses',r'elbise', ['Elbiseler','Dresses','Платья','الفساتين','Kleider','Donlar','Көйлектер','Köýnekler','Ko‘ylaklar','Көйнөктөр','پیراهن‌ها']),
 ('plus',r'buyuk beden|\b(?:xl|xxl|xxxl|2xl|3xl)\b', ['Büyük Beden','Plus Size','Большие размеры','المقاسات الكبيرة','Große Größen','Böyük ölçülər','Үлкен өлшемдер','Uly bedenler','Katta o‘lchamlar','Чоң өлчөмдөр','سایز بزرگ']),
 ('vibrators',r'vibrator|titresim', ['Vibratörler','Vibrators','Вибраторы','الهزازات','Vibratoren','Vibratorlar','Вибраторлар','Wibratorlar','Vibratorlar','Вибраторлор','ویبراتورها']),
 ('plugs',r'plug|anal', ['Anal Oyuncaklar','Anal Toys','Анальные игрушки','ألعاب شرجية','Analspielzeug','Anal oyuncaqlar','Анал ойыншықтар','Anal oýunjaklar','Anal o‘yinchoqlar','Аналдык оюнчуктар','اسباب‌بازی مقعدی']),
 ('dildos',r'dildo|realistik|penis', ['Dildo Modelleri','Dildos','Фаллоимитаторы','الديلدو','Dildos','Dildo modelləri','Дилдо','Dildo görnüşleri','Dildo modellari','Дилдо','دیلدو']),
 ('pumps',r'pompa', ['Pompalar','Pumps','Помпы','المضخات','Pumpen','Pompalar','Помпалар','Pompalar','Pompalar','Помпалар','پمپ‌ها']),
 ('rings',r'halka', ['Halkalar','Rings','Кольца','الحلقات','Ringe','Halqalar','Сақиналар','Halkalar','Halqalar','Шакектер','حلقه‌ها']),
 ('straps',r'belden|kemer', ['Kemer ve Bağlamalar','Harnesses','Ремни и крепления','الأحزمة','Gurte','Kəmərlər','Белдіктер','Guşaklar','Kamarlar','Курлар','هارنس و کمربند']),
 ('masturbators',r'masturbator|vajina|manken', ['Mastürbatörler','Masturbators','Мастурбаторы','أجهزة الاستمناء','Masturbatoren','Masturbatorlar','Мастурбаторлар','Masturbatorlar','Masturbatorlar','Мастурбаторлор','ماستورباتورها']),
 ('lubricants',r'kayganlastirici', ['Kayganlaştırıcılar','Lubricants','Лубриканты','المزلقات','Gleitmittel','Lubrikantlar','Лубриканттар','Lubrikantlar','Lubrikantlar','Лубриканттар','روان‌کننده‌ها']),
 ('oils',r'masaj yag', ['Masaj Yağları','Massage Oils','Массажные масла','زيوت التدليك','Massageöle','Masaj yağları','Массаж майлары','Massaž ýaglary','Massaj moylari','Массаж майлары','روغن ماساژ']),
 ('condoms',r'prezervatif', ['Prezervatifler','Condoms','Презервативы','الواقيات','Kondome','Prezervativlər','Мүшеқаптар','Prezerwatiwler','Prezervativlar','Презервативдер','کاندوم‌ها']),
 ('cleaners',r'temizl|bakim', ['Temizlik ve Bakım','Cleaning and Care','Очистка и уход','التنظيف والعناية','Reinigung und Pflege','Təmizlik və qulluq','Тазалау және күтім','Arassalama we ideg','Tozalash va parvarish','Тазалоо жана кам көрүү','تمیزکردن و مراقبت']),
 ('accessories',r'kelepce|goz band|maske|kirbac|bdsm|fetis', ['Fantezi Aksesuarları','Fantasy Accessories','Аксессуары','إكسسوارات','Fantasy-Accessoires','Fantazi aksesuarlar','Аксессуарлар','Aksessuarlar','Aksessuarlar','Аксессуарлар','لوازم جانبی']),
]

def apply_taxonomy(data):
 categories={c['id']:c for c in data['categories']};work={w['id']:w for w in data['workbench']}
 for product in data['products']:
  entry=work[product['id']];root='sg_'+entry['group'];name=fold(product['name']['tr']);source=' '.join(fold(c.get('name',''))for c in entry['sourceCategories'] if c.get('name'))
  options=TYPES[:16] if entry['group']=='lingerie' else TYPES[16:]
  if entry['group']=='care':options=[row for row in options if row[0]in ['lubricants','oils','condoms','cleaners']]
  if entry['group']=='gifts':options=[]
  # Pompa, halka ve kemer başlığını genel penis/dildo eşleşmesinden önce ayır.
  if entry['group']!='lingerie':options=sorted(options,key=lambda row:0 if row[0]in ['pumps','rings','straps','cleaners']else 1)
  matches=[row for row in options if re.search(row[1],name+' '+source)]
  chosen=matches[:1]
  if entry['group']=='lingerie'and re.search(TYPES[15][1],name)and all(row[0]!='plus'for row in chosen):chosen.append(TYPES[15])
  ids=[root]
  for key,pattern,labels in chosen:
   category_id=root+'_'+key;ids.append(category_id)
   categories[category_id]={'id':category_id,'parentId':root,'name':loc(labels),'slug':entry['group']+'-'+key}
  product['categoryIds']=ids
 return list(categories.values())
