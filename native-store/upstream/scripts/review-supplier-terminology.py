"""Source-conditional terminology and dimensional typography corrections; no facts added."""
from pathlib import Path
import json,re,concurrent.futures,collections
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication';C=O/'translation-cache'
def review(file):
 d=json.loads(file.read_bytes());source=d['source'];old=d['translation'];text=old;lang=d['targetLanguage'];low=source.casefold()
 # Multiplication signs from the decoder must remain unambiguous between numeric slots.
 text=re.sub(r'(ZXQ\d+ZXQ)\s*(?:[xX]{1,3}|س\s*س)\s*(?=ZXQ\d+ZXQ)',r'\1 × ',text)
 if lang=='en':
  if 'kayın kaplama' in low:text=re.sub(r'\bbeech\s+coating\b','beech veneer',text,flags=re.I)
  if 'iç içe' in low:text=re.sub(r'which can be imported','which fit inside one another',text,flags=re.I)
 if lang=='ar':
  for match in re.finditer(r'(?=(ZXQ\d+ZXQ)[xX×](ZXQ\d+ZXQ))',source):
   first,second=match.groups()
   text=re.sub(re.escape(first)+r'(?:\s|\.|>>ara<<|س|×|x)+'+re.escape(second),first+' × '+second,text)
  if '>>ara<<' in text:text=text.replace('>>ara<<','و'if '+'in source else' ')
  if 'kayın kaplama' in low:
   text=text.replace('القشرة خشب الزان','قشرة خشب الزان').replace('الزان القشرة','قشرة خشب الزان').replace('خشب الزان القشرة','قشرة خشب الزان').replace('قشرة الزان','قشرة خشب الزان')
  if 'boyama' in low:
   text=text.replace('الرسم','الطلاء').replace('الرسمات','أعمال الطلاء').replace('ويتم شحنها بشكل منفصل','وتُحسب تكلفته بشكل منفصل').replace('يتم شحنها بشكل منفصل','تُحسب تكلفته بشكل منفصل')
  if 'döşeme' in low:text=text.replace('الأرضيات','التنجيد').replace('الارضيات','التنجيد')
  if 'bar sandalyesi' in low:text=text.replace('كرسي شريط','كرسي بار')
  if 'kişilik' in low:text=re.sub(r'(ZXQ\d+ZXQ)\s*-نعم\s*(ZXQ\d+ZXQ)',r'\1–\2',text)
 if text!=old:
  tokens=lambda x:re.findall(r'ZXQ\d+ZXQ|ZXQPNZXQ|ZXQMODEL[A-Z]ZXQ',x)
  assert sorted(tokens(old))==sorted(tokens(text));d['translation']=text;d['terminologyReview']='2026-11-10: source-conditional veneer, painting and dimensional typography';file.write_text(json.dumps(d,ensure_ascii=False)+'\n',encoding='utf8');return lang
with concurrent.futures.ThreadPoolExecutor(max_workers=24)as pool:counts=collections.Counter(x for x in pool.map(review,C.glob('*.json'))if x)
(O/'terminology-review.json').write_text(json.dumps(dict(counts),indent=2)+'\n');print(json.dumps(dict(counts)))
