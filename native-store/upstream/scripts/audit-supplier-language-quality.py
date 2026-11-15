"""Find untranslated Arabic clauses and known material/nesting mistranslations."""
from pathlib import Path
import json,re,concurrent.futures
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication';C=O/'translation-cache'
flags=[];english_fixes=0
def inspect(f):
 global english_fixes
 d=json.loads(f.read_bytes());source=d['source'];text=d['translation'];key=d['sourceSha256'];local=d.get('localOnly')
 ef=C/('en-'+key+'.json')
 if 'iç içe' in source.casefold() and ef.exists():
  en=json.loads(ef.read_bytes());old=en['translation']
  if 'iç içe' in source.casefold():
   en['translation']=re.sub(r'which can be imported','which fit inside one another',old,flags=re.I)
   if old!=en['translation']:ef.write_text(json.dumps(en,ensure_ascii=False)+'\n',encoding='utf8');english_fixes+=1
 stripped=re.sub(r'ZXQ(?:\d+|PN|MODEL[A-Z])ZXQ',' ',text)
 latin=re.findall(r'[A-Za-z]{3,}',stripped)
 bad_latin=bool(re.search(r'\b(?:the|with|which|wooden|is|can|and|surface|for|painted|price|table|size|coating|not|veneer|quality)\b',stripped,re.I))
 material='kayın kaplama' in source.casefold() and ('خبيث' in text or (local and 'الزان' not in text))
 nesting='iç içe' in source.casefold() and 'استيراد' in text
 if local and (bad_latin or material or nesting):return {'key':key,'reason':'untranslated_clause'if bad_latin else'material'if material else'nesting','source':source,'old':text}
with concurrent.futures.ThreadPoolExecutor(max_workers=24)as pool:
 for i,result in enumerate(pool.map(inspect,C.glob('ar-*.json'))):
  if result:flags.append(result)
  if i%1500==0:print(json.dumps({'scanned':i,'flagged':len(flags)}),flush=True)
(O/'language-quality-flags.json').write_text(json.dumps(flags,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'flaggedArabic':len(flags),'englishNestingFixed':english_fixes}),flush=True)
