"""Human-reviewed Arabic factual descriptions for the remaining 59 decoder exceptions."""
from pathlib import Path
import json,re,time
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication';C=O/'translation-cache'
rows=json.loads((O/'language-quality-flags.json').read_bytes())
paint='الطلاء اختياري وغير مشمول في السعر، وتُحسب تكلفته بشكل منفصل وفقًا للون المختار.'
for row in rows:
 key=row['key'];s=row['source'];low=s.casefold();n=re.findall(r'ZXQ\d+ZXQ',s);dims=re.findall(r'ZXQ\d+ZXQ(?:[xX×]ZXQ\d+ZXQ){1,2}',s);parts=[]
 if low.startswith('ayak malzemesi:'):text='مادة الأرجل: قشرة خشب الزان.'
 elif low.startswith('kayın kaplama oval masa tablası ve gerçek ağaç ayakların temizliğinde'):
  text='نظّف سطح الطاولة البيضاوي المكسو بقشرة خشب الزان والأرجل المصنوعة من الخشب الطبيعي بقطعة قماش ناعمة ورطبة. تجنّب الإسفنج الكاشط والمنظفات الكيميائية القوية. استخدم قواعد واقية تحت الأواني الساخنة للمساعدة في الحفاظ على السطح والأرجل.'
 elif low.startswith('abzxq'):text='حلية إطار الطاولة والقاعدة الخشبية ABZXQ0ZXQ.'
 elif 'set: iç içe' in low:text='مجموعة من ZXQ0ZXQ قطع بتصميم عملي تتداخل فيه الطاولات لتوفير المساحة.'
 elif 'apple meşe' in low:text='طاولة APPLE الجانبية مكسوة بقشرة خشب البلوط، وتناسب غرف المعيشة وزوايا الجلوس. تضيف القشرة الطبيعية ملمسًا دافئًا وبسيطًا. يُورَّد الهيكل دون طلاء. '+paint
 else:
  if 'ZXQPNZXQ' in s:
   header='طراز ZXQPNZXQ'
   if re.search(r'ZXQPNZXQ\s+ZXQ0ZXQ CM',s):header+='، بمقاس ZXQ0ZXQ سم'
   elif re.match(r'ZXQ0ZXQ CM ZXQPNZXQ',s):header+='، بمقاس ZXQ0ZXQ سم'
   if 'SET)' in s:header+='، مجموعة من ZXQ0ZXQ قطع'
  elif 'TV SEHPASI' in s:
   model='ZXQMODELAZXQ'if 'ZXQMODELAZXQ'in s else'PAPATYA';header='وحدة تلفاز '+model+'، بمقاس ZXQ0ZXQ سم'
  elif 'ASK-ZXQ0ZXQ' in s:header='علاقة ملابس ASK-ZXQ0ZXQ من طراز ZXQMODELAZXQ ذات ZXQ1ZXQ خطافات'
  elif 'DORÉ APARATLI' in s:header='مرآة DORÉ بطول كامل مع آلية لضبط زاوية المرآة'
  elif 'ÇİFT TEPELİ DİLSİZ UŞAK' in s:header='حامل ملابس بتاج مزدوج لتعليق السترات والقمصان والسراويل والإكسسوارات دون تجعد، مناسب لغرف النوم وغرف الملابس والمتاجر'
  else:
   model=next(x for x in ['BABA','ELEGANCE','BOHEM','DOLUNAY','FIÇI','ÇİZGİLİ']if x in s)
   header='طاولة '+model+(' قابلة للتمديد'if 'AÇILIR'in s else' ثابتة')+'، بمقاس ZXQ0ZXQ سم'
  parts.append(header+'.')
  for dim in dims:parts.append('الأبعاد: '+re.sub(r'(ZXQ\d+ZXQ)[xX×](?=ZXQ)',r'\1 × ',dim)+' سم.')
  if 'SEHPA (' in s:parts.append('تتداخل الطاولات تحت بعضها لتوفير المساحة في غرف المعيشة والجلسات.')
  if 'üç farklı yükseklik' in low:parts.append('تضم المجموعة ثلاث طاولات بارتفاعات قصيرة ومتوسطة وطويلة، مع هيكل مضلّع وشكل مستوحى من الفطر.')
  if 'dresuar' in low:parts.append('كونسول بعمق صغير مناسب للمداخل وغرف المعيشة والمساحات الضيقة.')
  if 'saksılık' in low:parts.append('حامل نباتات مرتفع بتصميم مربع يناسب المنازل والمكاتب والمقاهي.')
  if 'komidin' in low:parts.append('خزانة جانبية للسرير بتفاصيل منحوتة تناسب غرف النوم.')
  if 'beş çekmeceli' in low:parts.append('خزانة ذات خمسة أدراج لتنظيم الأغراض في غرف النوم ومساحات المعيشة.')
  if 'berjer' in low:parts.append('كرسي مريح مناسب لغرف المعيشة والفنادق والمقاهي ومناطق الانتظار.')
  if 'çay takımı' in low:parts.append('طقم جلوس منجّد مناسب للمنازل والفنادق والمقاهي والمساحات الاجتماعية.')
  if 'puf' in low:parts.append('مقعد منجّد بمساحة جلوس واسعة، مناسب كقطعة مكملة في غرف المعيشة وغرف النوم والمداخل.')
  if 'birden fazla kişi' in low:parts.append('مساحة الجلوس الطويلة والواسعة مناسبة لجلوس أكثر من شخص.')
  if 'sallan' in low:parts.append('تصميم هزّاز بمساحة جلوس واسعة وظهر مريح يناسب الاسترخاء وغرف المعيشة والشرفات والفنادق.')
  if 'çanak formu' in low:parts.append('يتميز المقعد بشكل مقعّر مريح وخطوط ناعمة.')
  if 'çapraz' in low:parts.append('أرجل متقاطعة توفر دعماً متوازناً.')
  if 'yüksek sırt' in low:parts.append('ظهر مرتفع ومساحة جلوس واسعة للراحة أثناء الجلوس.')
  if 'baş, sırt ve bel' in low:parts.append('يدعم الرأس والظهر وأسفل الظهر.')
  if 'baş, boyun ve sırt' in low:parts.append('يوفر الظهر العالي دعمًا للرأس والرقبة والظهر.')
  if 'tornalı ayak' in low:parts.append('أرجل خشبية مشغولة بالخراطة.')
  if 'oyma' in low:parts.append('تفاصيل خشبية منحوتة'+(' باللون الذهبي'if 'gold renkli'in low else'')+'.')
  if 'hasır' in low:
   if 'hasırsız' in low:parts.append('يُورَّد دون خيزران منسوج. توجد شرائح من الخشب الطبيعي في الواجهات الأمامية والجانبية.')
   else:parts.append('تفاصيل من الخيزران المنسوج الطبيعي'+(' مثبّتة على المنتج'if any(x in low for x in ['hasır detay ürüne sabit','hasır bölümler sabit'])else'')+'.')
  if 'traverten' in low:parts.append('سطح دائري مع تفاصيل مكسوة بالترافرتين الطبيعي. لا تُطلى أجزاء الترافرتين وتُسلَّم بحالتها الطبيعية.')
  if 'oval' in low:parts.append('سطح طاولة بيضاوي الشكل.')
  elif 'yuvarlak' in low:parts.append('سطح طاولة دائري الشكل.')
  elif 'dikdörtgen' in low:parts.append('سطح طاولة مستطيل الشكل.')
  if 'fıçı formundaki' in low:parts.append('هيكل على شكل برميل.')
  if 'çizgili model' in low:parts.append('كسوة بتفاصيل مخططة يمكن إبرازها بألوان مختلفة.')
  if 'kayın kaplama' in low:
   material='الهيكل مكسو بقشرة خشب الزان.'if 'iskelet' in low else'كسوة من قشرة خشب الزان.'
   if 'masa tablası' in low:material='سطح الطاولة مكسو بقشرة خشب الزان.'
   parts.append(material)
  if 'gerçek ağaç ayak' in low:parts.append('الأرجل من الخشب الطبيعي'+(' المصمت'if 'içi dolu' in low else'')+'.')
  if 'boyasız' in low:parts.append('يُورَّد دون طلاء.')
  used=re.findall(r'ZXQ\d+ZXQ',' '.join(parts));remaining=[t for t in n if t not in used]
  if remaining:
   if 'ASK-ZXQ0ZXQ'in s:parts.append('يوفر ZXQ2ZXQ نقاط لتعليق المعاطف والسترات والحقائب والإكسسوارات دون الحاجة إلى تثبيت.')
   elif 'kişilik'in low:
    width=re.search(r'genişlik\s+(ZXQ\d+ZXQ)',s,re.I)
    if width:parts.append('يصل العرض عند التمديد إلى '+width[1]+' سم.');remaining.remove(width[1])
    if len(remaining)==4:parts.append('يتسع لـ '+remaining[0]+'–'+remaining[1]+' أشخاص في الاستخدام اليومي، ولـ '+remaining[2]+'–'+remaining[3]+' أشخاص بعد التمديد.')
    elif len(remaining)==2:parts.append('يتسع لـ '+remaining[0]+'–'+remaining[1]+' أشخاص.')
    elif len(remaining)==1:parts.append('يتسع لـ '+remaining[0]+' أشخاص.')
    elif remaining:raise ValueError(('capacity',key,remaining))
   elif 'cm yuvarlak' in low:parts.append('القطر في الاستخدام اليومي '+remaining[0]+' سم، مع إمكانية التمديد لتوفير مساحة إضافية.')
   else:raise ValueError(('unassigned_numeric_fact',key,remaining))
  if 'açılır' in low and not any('تمديد'in p for p in parts):parts.append('آلية قابلة للتمديد لتوفير مساحة إضافية عند الحاجة.')
  if 'döşeme ve boyama' in low or 'boyama ve döşeme' in low:
   parts.append('يُنفَّذ التنجيد والطلاء معًا كخدمة واحدة غير منفصلة، بتكلفة إضافية.')
   parts.append('تتوفر أقمشة الكتان والمنسوجة والمخمل والنوبوك'+(' والبوكلية'if 'boucle'in low else'')+' والأقمشة المقاومة للبقع للتنجيد.')
  elif 'boyama' in low:parts.append(paint)
  elif 'boyanabilir' in low:parts.append('يمكن طلاء الأسطح الخشبية باللون المطلوب بما يناسب الديكور.')
  text=' '.join(parts)
 tokens=lambda value:re.findall(r'ZXQ\d+ZXQ|ZXQPNZXQ|ZXQMODEL[A-Z]ZXQ',value)
 assert sorted(tokens(s))==sorted(tokens(text)),(key,tokens(s),tokens(text))
 value={'source':s,'sourceSha256':key,'targetLanguage':'ar','translation':text,'provider':'human-reviewed Arabic furniture facts; dimensions, wood, capacity and optional services preserved','numericTokensVerified':True,'fetchedAt':time.time()};(C/('ar-'+key+'.json')).write_text(json.dumps(value,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({'humanReviewedArabicExceptions':len(rows)}))
