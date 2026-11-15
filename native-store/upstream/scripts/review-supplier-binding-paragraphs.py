"""Reviewed furniture translations for the decoder's malformed placeholder cases."""
from pathlib import Path
import json,re,hashlib,time
R=Path(__file__).resolve().parents[1]; O=R/'artifacts/supplier-expansion/publication'; C=O/'translation-cache'
keys=list(dict.fromkeys(x['key'] for x in json.loads((O/'binding-repair-keys.json').read_bytes())))
def trio(en,ru,ar): return dict(en=en,ru=ru,ar=ar)
paint=trio('Painting is optional and charged separately.','Окраска выполняется по желанию и оплачивается отдельно.','الطلاء اختياري وتُحسب تكلفته بشكل منفصل.')
unfinished=trio('The body is supplied unfinished with beech veneer.','Корпус отделан буковым шпоном и поставляется без окраски.','الهيكل مكسو بقشرة خشب الزان ويُورَّد دون طلاء.')
for key in keys:
 source=json.loads((C/('en-'+key+'.json')).read_bytes())['source']; low=source.casefold(); dims=re.findall(r'ZXQ\d+ZXQ(?:\s*[xX×]\s*ZXQ\d+ZXQ){1,2}',source)
 if 'SEHPA (' in source:
  size=dims[0] if dims else None
  texts=trio('ZXQPNZXQ is a nesting table set containing ZXQ0ZXQ pieces'+(', measuring '+size+' cm' if size else '')+'. The tables fit inside one another to save space in living and seating areas.',
   'ZXQPNZXQ — комплект из ZXQ0ZXQ приставных столиков'+(' размером '+size+' см' if size else '')+'. Столики задвигаются друг под друга и экономят место в гостиной и зонах отдыха.',
   'ZXQPNZXQ مجموعة طاولات متداخلة من ZXQ0ZXQ قطع'+('، بمقاس '+size+' سم' if size else '')+'. تدخل الطاولات تحت بعضها لتوفير المساحة في غرف المعيشة والجلسات.')
  walnut='ceviz kaplama' in low
  material=trio('Made with '+('walnut' if walnut else 'beech')+' veneer.','Изготовлено с отделкой '+('ореховым' if walnut else 'буковым')+' шпоном.','مصنوعة بكسوة من قشرة خشب '+('الجوز' if walnut else 'الزان')+'.')
  texts={lang:texts[lang]+' '+material[lang]+' '+paint[lang] for lang in texts}
 elif 'saksılık gövdesi' in low:
  texts=trio('ZXQPNZXQ measures '+dims[0]+' cm. Its balanced proportions and classical ZXQMODELBZXQ styling make it a decorative plant stand for homes, offices and cafés.',
   'ZXQPNZXQ размером '+dims[0]+' см — подставка для растений с гармоничными пропорциями и классическими чертами ZXQMODELBZXQ для дома, офиса и кафе.',
   'ZXQPNZXQ حامل نباتات بمقاس '+dims[0]+' سم، بتناسب متوازن وتصميم كلاسيكي مستوحى من ZXQMODELBZXQ، يناسب المنازل والمكاتب والمقاهي.')
  texts={lang:texts[lang]+' '+unfinished[lang]+' '+paint[lang] for lang in texts}
 elif 'sehpa gövdesi' in low:
  texts=trio('ZXQPNZXQ measures '+dims[0]+' cm. Its compact, balanced design makes it a practical side table beside a sofa or armchair in living and seating areas.',
   'ZXQPNZXQ размером '+dims[0]+' см — компактный приставной столик с гармоничными пропорциями для размещения рядом с диваном или креслом в гостиной и зоне отдыха.',
   'ZXQPNZXQ طاولة جانبية بمقاس '+dims[0]+' سم، بتصميم مدمج ومتوازن يناسب وضعها بجوار الأريكة أو الكرسي في غرف المعيشة وزوايا الجلوس.')
  texts={lang:texts[lang]+' '+unfinished[lang]+' '+paint[lang] for lang in texts}
 elif key.startswith('04e0b'):
  texts=trio('ZXQPNZXQ '+dims[0]+' is a modern table leg with rounded lines and a balanced design. Its compact '+dims[1]+' cm base supports small and medium tabletops. The full-moon form suits residential and commercial interiors. Made from real wood with a natural texture.',
   'ZXQPNZXQ '+dims[0]+' — современная ножка стола с округлыми линиями и сбалансированным дизайном. Компактное основание '+dims[1]+' см подходит для небольших и средних столешниц. Форма полной луны уместна в жилых и коммерческих интерьерах. Изготовлена из натурального дерева с естественной текстурой.',
   'ZXQPNZXQ '+dims[0]+' رجل طاولة حديثة بخطوط مستديرة وتصميم متوازن. قاعدتها المدمجة بمقاس '+dims[1]+' سم تدعم أسطح الطاولات الصغيرة والمتوسطة. يناسب شكل البدر المساحات المنزلية والتجارية، وهي مصنوعة من الخشب الطبيعي الذي يُظهر ملمسه المميز.')
 elif key.startswith('ff89bf'):
  texts=trio('ZXQPNZXQ '+dims[0]+' is a decorative table leg with a spherical, modern design. Its '+dims[1]+' cm base offers balanced support, and its ZXQ5ZXQ cm height suits standard tables. The planet-inspired form creates a distinctive feature in modern interiors. When made in real wood, it combines natural texture with its sculptural appearance.',
   'ZXQPNZXQ '+dims[0]+' — декоративная ножка стола сферической современной формы. Основание '+dims[1]+' см обеспечивает устойчивую опору, а высота ZXQ5ZXQ см подходит для стандартных столов. Форма, напоминающая планету, создаёт выразительный акцент в современном интерьере. При изготовлении из натурального дерева сочетает природную текстуру со скульптурным обликом.',
   'ZXQPNZXQ '+dims[0]+' رجل طاولة بتصميم كروي حديث. توفر قاعدتها بمقاس '+dims[1]+' سم دعماً متوازناً، ويلائم ارتفاعها البالغ ZXQ5ZXQ سم الطاولات القياسية. يضيف شكلها المستوحى من الكواكب لمسة مميزة للديكورات الحديثة. وعند تصنيعها من الخشب الطبيعي تجمع بين ملمسه الطبيعي وشكلها المنحوت.')
 elif key.startswith('ffe5a78'):
  texts=trio('ZXQPNZXQ '+dims[0]+' is a decorative table leg measuring '+dims[1]+' cm, with simple, modern lines. Its ZXQMODELBZXQ form provides balanced support for small and medium tabletops. The wooden surface can be painted to suit the room. Painting is optional and is not included in the price.',
   'ZXQPNZXQ '+dims[0]+' — декоративная ножка стола размером '+dims[1]+' см с простыми современными линиями. Форма ZXQMODELBZXQ обеспечивает сбалансированную опору для небольших и средних столешниц. Деревянную поверхность можно окрасить под интерьер. Окраска выполняется по желанию и не входит в цену.',
   'ZXQPNZXQ '+dims[0]+' رجل طاولة زخرفية بمقاس '+dims[1]+' سم، بخطوط بسيطة وحديثة. يوفر شكل ZXQMODELBZXQ دعماً متوازناً لأسطح الطاولات الصغيرة والمتوسطة. يمكن طلاء سطحها الخشبي بما يناسب الغرفة. الطلاء اختياري وغير مشمول في السعر.')
 elif key.startswith('7b09d8'):
  texts=trio('ZXQPNZXQ '+dims[0]+' is a decorative supporting table leg with modern lines and a sturdy structure. Its '+dims[1]+' cm dimensions provide a compact, balanced base for residential and commercial projects. It can be produced in real wood for a natural appearance.',
   'ZXQPNZXQ '+dims[0]+' — декоративная опорная ножка стола с современными линиями и прочной конструкцией. Размеры '+dims[1]+' см обеспечивают компактное устойчивое основание для жилых и коммерческих проектов. Может изготавливаться из натурального дерева для сохранения естественного облика.',
   'ZXQPNZXQ '+dims[0]+' رجل طاولة داعمة وزخرفية بخطوط حديثة وبنية متينة. توفر أبعادها '+dims[1]+' سم قاعدة مدمجة ومتوازنة للمشاريع المنزلية والتجارية. ويمكن تصنيعها من الخشب الطبيعي للحصول على مظهر طبيعي.')
 elif 'paketleme:' in low:
  texts=trio('Packaging: ZXQ0ZXQ stock length equals ZXQ1ZXQ metres. If you buy ZXQ2ZXQ stock lengths, ZXQ3ZXQ strips of ZXQ4ZXQ metres will be sent. Cut-to-length products cannot be returned.',
   'Упаковка: ZXQ0ZXQ стандартная длина составляет ZXQ1ZXQ м. При покупке ZXQ2ZXQ стандартных длин поставляются ZXQ3ZXQ рейки длиной ZXQ4ZXQ м. Отрезанные по размеру изделия возврату не подлежат.',
   'التعبئة: طول ZXQ0ZXQ قياسي يعادل ZXQ1ZXQ متر. عند شراء ZXQ2ZXQ أطوال قياسية، تُرسل ZXQ3ZXQ شرائح بطول ZXQ4ZXQ متر. لا تُقبل إعادة المنتجات المقطوعة حسب الطول.')
 elif source.startswith('Düz Mdf'):
  texts=trio('Plain MDF decorative moulding MMCZXQ0ZXQ','Гладкий декоративный молдинг МДФ MMCZXQ0ZXQ','حلية زخرفية سادة من MDF، طراز MMCZXQ0ZXQ')
 elif 'ceviz kaplama yüzeylerin temizliğinde' in low:
  texts=trio('Clean walnut veneer surfaces with a soft, damp cloth. Avoid abrasive sponges and strong chemical cleaners. Suitable varnish and regular care help the veneer retain its shape and colour for years.',
   'Очищайте поверхности с ореховым шпоном мягкой влажной тканью. Не используйте абразивные губки и агрессивные химические средства. Подходящий лак и регулярный уход помогают шпону долго сохранять форму и цвет.',
   'نظّف أسطح قشرة خشب الجوز بقطعة قماش ناعمة ورطبة. تجنّب الإسفنج الكاشط والمنظفات الكيميائية القوية. يساعد الورنيش المناسب والعناية المنتظمة على احتفاظ القشرة بشكلها ولونها لسنوات.')
 elif 'yatak odanıza' in low:
  texts=trio('The ZXQMODELAZXQ headboard measures ZXQ0ZXQ × ZXQ1ZXQ cm. Its simple lines and refined, balanced design complement both classical and modern bedroom interiors.',
   'Изголовье ZXQMODELAZXQ имеет размеры ZXQ0ZXQ × ZXQ1ZXQ см. Простые линии и изящный сбалансированный дизайн сочетаются с классическим и современным интерьером спальни.',
   'يبلغ مقاس لوح رأس السرير ZXQMODELAZXQ مقدار ZXQ0ZXQ × ZXQ1ZXQ سم. وتناسب خطوطه البسيطة وتصميمه الأنيق والمتوازن غرف النوم الكلاسيكية والحديثة.')
 elif 'ahşap yüzeyler nemli' in low:
  texts=trio('Wipe wooden surfaces with a damp cloth. Clean upholstered surfaces according to the fabric type. Avoid abrasive and chemical cleaners.',
   'Протирайте деревянные поверхности влажной тканью. Для обивки выбирайте способ очистки с учётом типа ткани. Не используйте абразивные и химические чистящие средства.',
   'امسح الأسطح الخشبية بقطعة قماش رطبة. نظّف الأسطح المنجدة بطريقة تناسب نوع القماش. تجنّب المنظفات الكاشطة والكيميائية.')
 elif 'askılık gövdesi' in low:
  texts=trio('The ZXQMODELAZXQ coat stand with ZXQ0ZXQ hooks can be used without mounting in entrance areas, offices, cafés and living spaces. Its ZXQ1ZXQ hanging points organise coats, jackets, bags and accessories. The simple, timeless shape suits different interiors.',
   'Напольная вешалка ZXQMODELAZXQ на ZXQ0ZXQ крючков не требует крепления и подходит для прихожих, офисов, кафе и жилых помещений. ZXQ1ZXQ мест для подвешивания помогают разместить пальто, куртки, сумки и аксессуары. Простая лаконичная форма сочетается с разными интерьерами.',
   'علاقة الملابس ZXQMODELAZXQ ذات ZXQ0ZXQ خطافات مناسبة للمداخل والمكاتب والمقاهي ومساحات المعيشة دون تثبيت. تساعد نقاط التعليق البالغ عددها ZXQ1ZXQ على تنظيم المعاطف والسترات والحقائب والإكسسوارات. ويناسب شكلها البسيط مختلف الديكورات.')
  texts={lang:texts[lang]+' '+unfinished[lang]+' '+paint[lang] for lang in texts}
 elif 'Askılık ZXQ' in source:
  texts=trio('ZXQMODELAZXQ coat stand with ZXQ0ZXQ hooks','Вешалка ZXQMODELAZXQ на ZXQ0ZXQ крючков','علاقة ملابس ZXQMODELAZXQ ذات ZXQ0ZXQ خطافات')
 else:raise ValueError('Unreviewed template '+key)
 for lang,text in texts.items():
  tokens=lambda x:re.findall(r'ZXQ\d+ZXQ|ZXQPNZXQ|ZXQMODEL[A-Z]ZXQ',x)
  assert sorted(tokens(source))==sorted(tokens(text)),(key,lang,tokens(source),tokens(text))
  assert 'ZXQ' not in re.sub(r'ZXQ\d+ZXQ|ZXQPNZXQ|ZXQMODEL[A-Z]ZXQ','',text)
  value={'source':source,'sourceSha256':key,'targetLanguage':lang,'translation':text,'provider':'reviewed furniture translation; nesting, material, dimensions and optional services checked','numericTokensVerified':True,'fetchedAt':time.time()}
  (C/(lang+'-'+key+'.json')).write_text(json.dumps(value,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({'reviewedTemplates':len(keys),'languages':3}))
