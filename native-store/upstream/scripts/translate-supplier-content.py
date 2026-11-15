"""Translate public catalogue text with protected numerical facts and resumable evidence.

Only already-public supplier content is sent. No account data or credentials are used.
The public translation response is cached verbatim with source/response SHA-256.
"""
from pathlib import Path
import concurrent.futures,hashlib,importlib.util,json,re,threading,time,itertools,functools
import requests
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication';CACHE=O/'translation-cache';CACHE.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('publication_text',R/'lib/supplier_publication.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=json.loads((O/'content-tr.json').read_bytes())['products'];languages=['en','ru','ar'];proper=re.compile(r'\b(Class|Danish|Country|Zurna|Miami|Luppo|Selçuklu|Vega|Milan|Milano|Alex|Tokyo|Oslo|Lexus|Grand|Abelya|Polo|Tonet|Chester)\b',re.I)
sha=lambda x:hashlib.sha256(x.encode()).hexdigest();templates={};bindings={};lock=threading.Lock();next_request=0;local=threading.local()
manual={
 'Ürün cilasız ham gönderilecektir.':{'en':'Supplied unfinished and unvarnished.','ru':'Поставляется без отделки и лака.','ar':'يُسلَّم المنتج خامًا دون تشطيب أو طلاء.'},
 'Ürün fiyatlarına kargo dahil değildir.':{'en':'Shipping is not included in the product price.','ru':'Доставка не включена в стоимость товара.','ar':'الشحن غير مشمول في سعر المنتج.'},
 'Ürün fiyatları ürünün metretül fiyatlarıdır.':{'en':'The price is per linear metre.','ru':'Цена указана за погонный метр.','ar':'السعر للمتر الطولي.'},
 'Ürün fiyatları ürünün boy fiyatlarıdır.':{'en':'The price is for one full stock length.','ru':'Цена указана за одну целую заготовку стандартной длины.','ar':'السعر للقطعة الواحدة بطولها القياسي الكامل.'}}
def register(text,p,title=False):
 original=text;values={}
 if not title:
  for name in sorted([p['rawTitle'],p['title']],key=len,reverse=True):
   if len(name)>5 and re.search(re.escape(name),text,re.I):text=re.sub(re.escape(name),'ZXQPNZXQ',text,flags=re.I);values['ZXQPNZXQ']='PRODUCT_TITLE'
 def name(match):
  word=match.group();token='ZXQMODEL'+chr(65+len(values))+'ZXQ';values[token]=word.title();return token
 text=proper.sub(name,text);template,numbers=m.protect_numbers(text);key=sha(template);templates[key]=template
 return {'key':key,'numbers':numbers,'bindings':values,'source':original}
for p in rows:
 bindings[p['id']]={'title':register(p['title'],p,True),'paragraphs':[register(t,p)for t in p['paragraphs']]}
def file(key,lang):return CACHE/(lang+'-'+key+'.json')
def cached(key,lang):
 try:
  d=json.loads(file(key,lang).read_bytes());validate(templates[key],d['translation']);return d.get('sourceSha256')==key
 except (ValueError,OSError,KeyError):return False
@functools.lru_cache(maxsize=None)
def translated(key,lang):return json.loads(file(key,lang).read_bytes())['translation']
def validate(source,text):
 expected=re.findall(r'ZXQ\d+ZXQ|ZXQPNZXQ|ZXQMODEL[A-Z]ZXQ',source)
 actual=re.findall(r'ZXQ\d+ZXQ|ZXQPNZXQ|ZXQMODEL[A-Z]ZXQ',text)
 if sorted(expected)!=sorted(actual):raise ValueError('translation_token_mismatch')
 m.validate_dimension_layout(source,text)
 if not text.strip()or re.search(r'\b(?:ALKA|ADORE|ALTINISAGAC)\b',text,re.I):raise ValueError('translation_empty_or_brand')
def request_batch(job):
 global next_request
 lang,keys=job;missing=[k for k in keys if not cached(k,lang)]
 if not missing:return {'language':lang,'cached':len(keys)}
 def query_text(text):
  text=re.sub(r"(ZXQ\d+ZXQ)['’]?(?:lik|lık|luk|lük)\b",r'\1 ölçüsündeki',text,flags=re.I)
  text=re.sub(r'(ZXQ(?:\d+|MODEL[A-Z]|PN)ZXQ)',r' \1 ',text)
  return re.sub(r'\s+x\s+',' × ',text)
 query='\n'.join('ZXQENTRY'+str(i)+'ZXQ\n'+query_text(templates[k])for i,k in enumerate(missing))
 with lock:
  delay=max(0,next_request-time.monotonic());next_request=max(next_request,time.monotonic())+.30
 if delay:time.sleep(delay)
 if not hasattr(local,'session'):local.session=requests.Session()
 error='unknown'
 for attempt in range(4):
  try:
   response=local.session.get('https://translate.googleapis.com/translate_a/single',params={'client':'gtx','sl':'tr','tl':lang,'dt':'t','q':query},timeout=(10,40))
   if response.status_code==429:time.sleep(min(60,max(15,int(response.headers.get('Retry-After','30')))));continue
   response.raise_for_status();raw=response.content;payload=response.json();text=''.join(x[0]for x in payload[0]if x[0]);matches=list(re.finditer(r'ZXQENTRY\s*(\d+)\s*ZXQ',text))
   if [int(x[1])for x in matches]!=list(range(len(missing))):raise ValueError('translation_entry_markers_changed')
   results=[]
   for i,key in enumerate(missing):
    value=text[matches[i].end():matches[i+1].start()if i+1<len(matches)else len(text)].strip();validate(templates[key],value);results.append((key,value))
   for key,value in results:
    receipt={'sourceLanguage':'tr','targetLanguage':lang,'sourceSha256':key,'source':templates[key],'translation':value,'responseSha256':hashlib.sha256(raw).hexdigest(),'fetchedAt':time.time(),'provider':'Google Translate public interface','numericTokensVerified':True}
    file(key,lang).write_text(json.dumps(receipt,ensure_ascii=False)+'\n',encoding='utf8')
   return {'language':lang,'completed':len(missing)}
  except (ValueError,requests.RequestException)as e:error=str(e);time.sleep(min(8,2**attempt))
 if len(missing)>1:
  print(json.dumps({'splitBatch':len(missing),'language':lang,'reason':error}),flush=True)
  results=[request_batch((lang,[k]))for k in missing];return {'language':lang,'split':results}
 print(json.dumps({'translationFailed':missing[0],'language':lang,'reason':error}),flush=True)
 return {'language':lang,'key':missing[0],'error':error}
for key,template in templates.items():
 if template in manual:
  for lang in languages:
   if not file(key,lang).exists():file(key,lang).write_text(json.dumps({'source':template,'sourceSha256':key,'translation':manual[template][lang],'targetLanguage':lang,'provider':'reviewed terminology','numericTokensVerified':True},ensure_ascii=False)+'\n',encoding='utf8')
jobs=[]
for lang in languages:
 batch=[];size=0
 for key,text in templates.items():
  if file(key,lang).exists():continue
  if batch and size+len(text)+30>1700:jobs.append((lang,batch));batch=[];size=0
  batch.append(key);size+=len(text)+30
 if batch:jobs.append((lang,batch))
groups=[[j for j in jobs if j[0]==lang]for lang in languages];jobs=[j for group in itertools.zip_longest(*groups)for j in group if j]
def bind(entry,lang,title):
 value=m.restore_numbers(translated(entry['key'],lang),entry['numbers'])
 for token,word in entry['bindings'].items():value=value.replace(token,title if word=='PRODUCT_TITLE'else word)
 if 'ZXQ'in value:raise ValueError('unbound_translation_placeholder')
 return value
def export():
 out=[];errors=[]
 for p in rows:
  try:
   b=bindings[p['id']];name={'tr':p['title']};paragraphs={'tr':p['paragraphs']}
   for lang in languages:name[lang]=bind(b['title'],lang,'')
   for lang in languages:paragraphs[lang]=[bind(e,lang,name[lang])for e in b['paragraphs']]
   out.append({**p,'name':name,'translatedParagraphs':paragraphs,'translationVerified':True})
  except (ValueError,FileNotFoundError)as e:errors.append({'id':p['id'],'error':str(e)})
 report={'products':len(out),'expected':len(rows),'errors':errors,'sourceContentSha256':hashlib.sha256((O/'content-tr.json').read_bytes()).hexdigest(),'allNumericTokensVerified':not errors,'publicationReady':False}
 target=O/'content-translated.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps({'products':out,'report':report},ensure_ascii=False,indent=2)+'\n',encoding='utf8');tmp.replace(target)
 (O/'translation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'translatedProducts':len(out),'remaining':len(errors)}),flush=True)
 return report
print(json.dumps({'templates':len(templates),'jobs':len(jobs),'products':len(rows)}),flush=True);results=[];export()
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
 for i,result in enumerate(pool.map(request_batch,jobs),1):
  results.append(result)
  if i%10==0:print(json.dumps({'batches':i,'total':len(jobs),'cachedTranslations':len(list(CACHE.glob('*.json')))}),flush=True)
  if i%100==0:export()
report=export();print(json.dumps(report),flush=True)
