"""Reviewed short interface terminology and exact compound-label composition."""
from pathlib import Path
import json,re,sqlite3,hashlib
R=Path(__file__).resolve().parents[1];O=R/'artifacts/target-locales-20261111';langs=['de','az','kk','tk','uz','ky','fa']
de={'Page':'Seite','Play':'Abspielen','sets':'Sets','Sets':'Sets','Sort':'Sortieren','Undo':'Rückgängig','Added':'Hinzugefügt','Clear':'Leeren','Doors':'Türen','Front':'Möbelfront','Pause':'Pausieren','Filter':'Filter','Finish':'Ausführung','Pieces':'Stück','Seller':'Verkäufer','Carrier':'Transportunternehmen','Default':'Standard','Details':'Details','Explore':'Entdecken','Shipped':'Versandt','Subject':'Betreff','Assembly':'Montage','Decrease':'Verringern','Discover':'Entdecken','Increase':'Erhöhen','optional':'optional','Returned':'Zurückgesendet','Cancelled':'Storniert','Connected':'Verbunden','Delivered':'Zugestellt','Disconnect':'Trennen','Self-handled':'Mit integrierter Griffleiste','Handing undecided':'Öffnungsrichtung noch offen'}
terms={
 'White':['Weiß','Ağ','Ақ','Ak','Oq','Ак','سفید'],
 'Black':['Schwarz','Qara','Қара','Gara','Qora','Кара','سیاه'],
 'Grey':['Grau','Boz','Сұр','Çal','Kulrang','Боз','خاکستری'],
 'Dark Grey':['Dunkelgrau','Tünd boz','Қою сұр','Goýy çal','Toʻq kulrang','Кочкул боз','خاکستری تیره'],
 'Light Grey':['Hellgrau','Açıq boz','Ашық сұр','Açyk çal','Och kulrang','Ачык боз','خاکستری روشن'],
 'Navy blue':['Marineblau','Tünd göy','Қою көк','Goýy gök','Toʻq koʻk','Кочкул көк','سرمه‌ای'],
 'Mint Green':['Mintgrün','Nanə yaşılı','Жалбыз жасылы','Narpyz ýaşyl','Yalpiz yashil','Жалбыз жашылы','سبز نعنایی'],
 'Forest Green':['Waldgrün','Meşə yaşılı','Орман жасылы','Tokaý ýaşyl','Oʻrmon yashil','Токой жашылы','سبز جنگلی'],
 'Denim Blue':['Jeansblau','Cins mavisi','Джинс көгі','Jins gök','Jinsi koʻk','Жынсы көк','آبی جین'],
 'Cosmic Blue':['Kosmisches Blau','Kosmik mavi','Ғарыш көгі','Kosmos gök','Kosmik koʻk','Космостук көк','آبی کیهانی'],
 'Anthracite':['Anthrazit','Antrasit','Антрацит','Antrasit','Antrasit','Антрацит','آنتراسیت'],
 'Cashmere':['Kaschmir','Kaşmir','Кашемир','Kaşmir','Kashmir','Кашемир','کشمیر'],
 'Cappuccino':['Cappuccino','Kapuçino','Капучино','Kapučino','Kapuchino','Капучино','کاپوچینو'],
 'Powder':['Puderrosa','Pudra','Ұнтақ қызғылт','Pudra','Pushti pudra','Упа кызгылт','صورتی پودری'],
 'Cream':['Creme','Krem','Крем','Krem','Krem','Крем','کرم'],
 'Walnut':['Walnuss','Qoz','Жаңғақ','Hoz','Yongʻoq','Жаңгак','گردویی'],
 'Oak':['Eiche','Palıd','Емен','Dub','Eman','Эмен','بلوط'],
 'Taupe':['Taupe','Vizon','Сұр қоңыр','Çal goňur','Kulrang jigarrang','Боз күрөң','خاکی مایل به خاکستری'],
 'Green':['Grün','Yaşıl','Жасыл','Ýaşyl','Yashil','Жашыл','سبز'],
 'Lacquer':['Lackiert','Laklı','Лакталған','Lakly','Laklangan','Лакталган','لاک‌شده'],
 'Matt PVC':['Mattes PVC','Mat PVC','Күңгірт PVC','Mat PVC','Mat PVC','Күңүрт PVC','پی‌وی‌سی مات'],
 'PVC / membrane':['PVC / Membran','PVC / membran','PVC / мембрана','PVC / membrana','PVC / membrana','PVC / мембрана','پی‌وی‌سی / ممبران'],
 'Wood veneer':['Holzfurnier','Taxta şpon','Ағаш шпон','Agaç şpon','Yogʻoch shpon','Жыгач шпон','روکش چوب'],
 'woodgrain PVC':['PVC in Holzoptik','Taxta naxışlı PVC','Ағаш өрнекті PVC','Agaç nagyşly PVC','Yogʻoch naqshli PVC','Жыгач өңдүү PVC','پی‌وی‌سی طرح چوب'],
 'Melamine':['Melamin','Melamin','Меламин','Melamin','Melamin','Меламин','ملامین'],
 'Acrylic / supermatt':['Acryl / Supermatt','Akril / super mat','Акрил / өте күңгірт','Akril / super mat','Akril / super mat','Акрил / өтө күңүрт','اکریلیک / فوق مات'],
 'Supermatt':['Supermatt','Super mat','Өте күңгірт','Super mat','Super mat','Өтө күңүрт','فوق مات'],
 'Email':['E-Mail','E-poçt','Электрондық пошта','E-poçta','Elektron pochta','Электрондук почта','ایمیل'],
 'Minimum':['Minimum','Minimum','Ең аз','Iň az','Eng kam','Эң аз','حداقل'],
 'Maximum':['Maximum','Maksimum','Ең көп','Iň köp','Eng koʻp','Эң көп','حداکثر'],
 'full stock length':['Volle Lieferlänge','Tam profil uzunluğu','Толық дайындама ұзындығы','Doly uzynlyk','Toʻliq profil uzunligi','Толук узундук','طول کامل شاخه'],
 'product selection':['Produktauswahl','Məhsul seçimi','Тауарлар таңдауы','Önümler toplumy','Mahsulotlar tanlovi','Товарлар тандоосу','گزیده محصولات'],
 'product list':['Produktliste','Məhsul siyahısı','Тауарлар тізімі','Önümler sanawy','Mahsulotlar roʻyxati','Товарлар тизмеси','فهرست محصولات'],
 'account':['Konto','Hesab','Тіркелгі','Hasap','Hisob','Каттоо эсеби','حساب کاربری'],
 'password':['Passwort','Şifrə','Құпия сөз','Açar söz','Parol','Сырсөз','گذرواژه'],
 'architrave':['Bekleidung','Pərvaz','Есік жақтауы','Gapy perwazy','Eshik hoshiyasi','Эшик кашеги','قاب دور در'],
}
terms.update(json.loads((R/'data/localization/terminology.json').read_bytes()));terms.update(json.loads((R/'data/localization/catalogue-terminology.json').read_bytes()))
token=re.compile(r'ZXQ\d+ZXQ');pattern=re.compile(r'(?<![A-Za-z])(?:'+'|'.join(re.escape(x)for x in sorted(terms,key=len,reverse=True))+r')(?![A-Za-z])',re.I)
lower={k.casefold():v for k,v in terms.items()};cache=sqlite3.connect(O/'translations.sqlite',timeout=300)
rows=list(cache.execute('SELECT DISTINCT key,source FROM translations'));held=json.loads((O/'translation-held.json').read_bytes());rows+=[(r['key'],r['source'])for r in held];count=0
invariant={'kvkk','sales','returns','privacy','cookies','membership','seller','data-request','international','price-desc','priceHighLow','productMappings','MDF','PVC','PDF','CSV','JSON','SMS','USB','XL','XXL','TV','kg','mm','cm','m²','m2','m3','m³','TRY','USD','EUR','GBP','RUB','AZN','KZT','AED','SAR','JPY','CHF','CAD'}
for key,source in dict(rows).items():
 for i,lang in enumerate(langs):
  target=None
  if source in invariant:target=source
  elif lang=='de'and source in de:target=de[source]
  elif source.casefold()in lower:target=lower[source.casefold()][i]
  else:
   remainder=pattern.sub('',token.sub('',source))
   if not re.search(r'[A-Za-z\u0400-\u04ff\u0600-\u06ff]',remainder):target=pattern.sub(lambda m:lower[m[0].casefold()][i],source)
  if target is not None:
   assert sorted(token.findall(source))==sorted(token.findall(target))
   cache.execute('INSERT OR REPLACE INTO translations VALUES(?,?,?,?,?)',(lang,key,source,target,'reviewed-interface-or-compound-terminology'));count+=1
cache.commit();(O/'reviewed-terms.json').write_text(json.dumps({'count':count,'terms':terms,'germanInterfaceTerms':de,'technicalInvariants':sorted(invariant)},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'reviewedEntries':count}))
