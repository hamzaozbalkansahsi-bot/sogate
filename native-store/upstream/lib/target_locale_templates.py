"""Protect factual identifiers, not ordinary hyphenated English descriptions."""
import re
from functools import lru_cache
PROTECTED=re.compile(r'https?://[^\s<>]+|[\w.+-]+@[\w.-]+\.[A-Za-z]+|\{[^{}]+\}|<[^>]+>|\b[A-Za-z]{1,8}\d{1,8}(?:[-./](?!certified\b)[A-Za-z0-9]+)*\b|\b(?:ND|NDA|NDB|NDP)\s+\d+\b|\b(?:TRY|USD|EUR|GBP|RUB|AZN|KZT|AED|SAR|JPY|CHF|CAD|AUD|CNY|NOK|SEK|DKK|mm|cm|kg|m²|m2|m³|m3|GDPR|KVKK|EIN|IRS|SSN|RAL|Ral|TİP|TIP|MDF|PVC)\b|\b(?:[A-Z]{1,8}-(?=[A-Za-z0-9-]*\d)[A-Za-z0-9-]+)\b|\d+(?:[.,]\d+)*(?:\s*[x×]\s*\d+(?:[.,]\d+)*)*(?:\s*(?:mm|cm|m²|m2|kg|%))?')
COMPANIES=('PTYS Technologies L.L.C.','PTYS Technologies LLC')
BRANDS=re.compile(r'(?<!\w)(?:PTYS Technologies L\.L\.C\.|PTYS Technologies LLC|NODENO|PTYS|Stripe|Google|Apple|WhatsApp|Facebook|Pinterest|Instagram|YouTube|TikTok|Microsoft|TCMB)(?!\w)')
@lru_cache(maxsize=4)
def proper_pattern(proper):
 if not proper:return re.compile(r'(?!)')
 return re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(x)for x in sorted(proper,key=len,reverse=True))+r')(?!\w)')
def protected_template(text,proper=(),interface=False):
 bindings={}
 def bind(match):
  key='ZXQ'+str(len(bindings))+'ZXQ';bindings[key]=match.group();return ' '+key+' '
 text=PROTECTED.sub(bind,text);text=(BRANDS if interface else proper_pattern(tuple(proper)+COMPANIES)).sub(bind,text)
 return re.sub(r'[ \t]+',' ',text).strip(),bindings
def interface_source(row):
 return any(o.startswith(('web/','legal/','hosting/','config.json','catalog/brand','catalog/categories'))for o in row['origins'])
TOKEN=re.compile(r'ZXQ\d+ZXQ')
def terminology_key(value):
 """Match Python re.I's dotted/dotless I variants without altering facts."""
 return value.casefold().replace('ı','i').replace('\u0307','')
CODE_INVARIANTS={'tr','en','ru','ar','de','az','kk','tk','uz','ky','fa','kvkk','sales','returns','privacy','cookies','membership','seller','data-request','international','MDF','PVC','PDF','CSV','JSON','SMS','USB','kg','cm','mm','m²','m2','m³','m3','TRY','USD','EUR','GBP','RUB','AZN','KZT','AED','SAR','JPY','CHF','CAD'}
def canonical_segment(text):
 forward={};reverse={}
 def rename(match):
  original=match[0]
  if original not in forward:
   key='ZXQ'+str(len(forward))+'ZXQ';forward[original]=key;reverse[key]=original
  return forward[original]
 return TOKEN.sub(rename,text),reverse
def rebind_segment(text,mapping):
 def replace(match):
  if match[0]not in mapping:raise ValueError('segment_fact_not_in_source')
  return mapping[match[0]]
 return TOKEN.sub(replace,text)
def model_placeholders(text):
 """Numeric placeholders survive the model tokenizer without spelling errors."""
 values={};reverse={}
 def replace(match):
  marker=match[0]
  if marker not in values:
   opaque=str(870000+len(values));values[marker]=opaque;reverse[opaque]=marker
  return values[marker]
 return TOKEN.sub(replace,text),reverse
def restore_model_placeholders(text,mapping):
 # The model occasionally inserts grouping spaces or punctuation into digits.
 for opaque,marker in mapping.items():
  pattern=r'(?<!\d)'+r'[\s,\u066c]*'.join(opaque)+r'(?!\d)'
  text=re.sub(pattern,lambda _:marker,text)
 return text
def translation_quality_errors(source,target,lang,reviewed=False):
 """Block observable translation corruption before it reaches public output."""
 errors=[]
 if not target.strip():return ['empty']
 if sorted(TOKEN.findall(source))!=sorted(TOKEN.findall(target)):errors.append('fact_changed')
 source_bare=TOKEN.sub('',source);target_bare=TOKEN.sub('',target)
 if re.search(r'\d',target_bare)and not re.search(r'\d',source_bare):errors.append('new_numeric_fact')
 if re.search(r'(.{3,24})\1{5,}',target_bare,re.S):errors.append('repetition')
 if len(target)>max(180,len(source)*4+40):errors.append('expanded')
 if len(source)>60 and len(target)<len(source)*.2:errors.append('shortened')
 visible=target_bare
 # Postal names stay exactly as supplied, including on RTL/legal documents.
 if 'N Gould St Ste N, Sheridan, WY'in source_bare:visible=visible.replace('N Gould St Ste N, Sheridan, WY','').replace('United States','')
 if lang in ['kk','ky','fa']and re.search(r'[A-Za-z][A-Za-z ,;:’\x27-]{44,}',visible):errors.append('foreign_prose')
 if not re.search(r'encyclop|wikipedia|wikimedia',source,re.I)and re.search(r'энциклопед|wikipedia|wikimedia|viki(?:anbar|pedi)',target,re.I):errors.append('unrelated_reference')
 if not reviewed and source not in CODE_INVARIANTS and re.search('[A-Za-z]{2}',source_bare)and target.casefold()==source.casefold():errors.append('english_copy')
 return errors
