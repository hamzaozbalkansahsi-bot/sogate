"""Offline, resumable target-language translations; no English fallback is accepted."""
from pathlib import Path
import os
os.environ['CT2_USE_MKL']='0';os.environ['CT2_USE_EXPERIMENTAL_PACKED_GEMM']='0'
for folder in Path('artifacts/translation-tools/Lib/site-packages/nvidia').glob('*/bin'):
 os.environ['PATH']=str(folder.resolve())+os.pathsep+os.environ['PATH']
import ast,ctranslate2,sentencepiece as sp,json,re,hashlib,sqlite3,time,sys,unicodedata,argparse
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1];O=R/'artifacts/target-locales-20261111';inv=json.loads((O/'inventory.json').read_bytes());langs=inv['languages'];parser=argparse.ArgumentParser();parser.add_argument('--batches',type=int,default=0);args=parser.parse_args()
import sys
sys.path.insert(0,str(R))
from lib.target_locale_templates import protected_template,interface_source,canonical_segment,rebind_segment,model_placeholders,restore_model_placeholders,translation_quality_errors
proper=sorted(inv['properNames'],key=len,reverse=True)
token=re.compile(r'ZXQ\d+ZXQ');invariants={'MDF','PVC','PDF','CSV','JSON','SMS','USB','XL','XXL','TV','NODENO','PTYS','Stripe','en','tr','ru','ar','kg','cm','mm','m','m²','m2','m³','m3','TRY','USD','EUR','GBP','RUB','AZN','KZT','AED','SAR','JPY','CHF','CAD','kvkk','sales','returns','privacy','cookies','membership','seller','data-request','international'}
def template(text,interface=False):return protected_template(text,tuple(proper),interface)
jobs={};entries=[]
for row in inv['entries']:
 interface=interface_source(row)
 t,b=template(row['source'],interface);key=hashlib.sha256(t.encode()).hexdigest();entries.append({**row,'template':key,'bindings':b});old=jobs.setdefault(key,{'text':t,'ui':False});old['ui']|='ui'in row['kinds']
print(json.dumps({'sources':len(entries),'templates':len(jobs),'languages':langs}),flush=True)
cache=sqlite3.connect(O/'translations.sqlite',timeout=300);cache.execute('CREATE TABLE IF NOT EXISTS translations(language TEXT, key TEXT, source TEXT, target TEXT, method TEXT, PRIMARY KEY(language,key))');cache.commit()
manual={
 'Add to basket':['In den Warenkorb','Səbətə əlavə et','Себетке қосу','Sebede goş','Savatga qoʻshish','Себетке кошуу','افزودن به سبد خرید'],
 'Add to bag':['In den Warenkorb','Səbətə əlavə et','Себетке қосу','Sebede goş','Savatga qoʻshish','Себетке кошуу','افزودن به سبد خرید'],
 'My bag':['Mein Warenkorb','Səbətim','Себетім','Sebedim','Savatim','Себетим','سبد خرید من'],
 'Home':['Startseite','Ana səhifə','Басты бет','Baş sahypa','Bosh sahifa','Башкы бет','صفحه اصلی'],
 'Categories':['Kategorien','Kateqoriyalar','Санаттар','Kategoriýalar','Toifalar','Категориялар','دسته‌بندی‌ها'],
 'View all':['Alle ansehen','Hamısına bax','Барлығын көру','Ählisini gör','Barchasini koʻrish','Баарын көрүү','مشاهده همه'],
 'View product':['Produkt ansehen','Məhsula bax','Өнімді көру','Önümi gör','Mahsulotni koʻrish','Товарды көрүү','مشاهده محصول'],
 'Excluding VAT':['zzgl. MwSt.','ƏDV xaric','ҚҚС-сыз','GBS-siz','QQSsiz','КНСсиз','بدون مالیات بر ارزش افزوده'],
 'VAT':['MwSt.','ƏDV','ҚҚС','GBS','QQS','КНС','مالیات بر ارزش افزوده'],
 'Quantity':['Menge','Say','Саны','Mukdary','Miqdor','Саны','تعداد'],
 'Colour':['Farbe','Rəng','Түсі','Reňki','Rang','Түсү','رنگ'],
 'Material':['Material','Material','Материал','Material','Material','Материал','جنس'],
 'Language':['Sprache','Dil','Тіл','Dil','Til','Тил','زبان'],
 'Currency':['Währung','Valyuta','Валюта','Pul birligi','Valyuta','Валюта','واحد پول'],
 'Good design. Easy living.':['Gutes Design. Einfach leben.','Yaxşı dizayn. Rahat həyat.','Жақсы дизайн. Жайлы өмір.','Oňat dizaýn. Amatly durmuş.','Yaxshi dizayn. Qulay hayot.','Жакшы дизайн. Жеңил жашоо.','طراحی خوب. زندگی آسان.'],
 'Sign in':['Anmelden','Daxil ol','Кіру','Giriş','Kirish','Кирүү','ورود'],
 'Password':['Passwort','Şifrə','Құпия сөз','Açar söz','Parol','Сырсөз','گذرواژه'],
 'Returns':['Rückgabe','Qaytarma','Қайтару','Yzyna gaýtarmak','Qaytarish','Кайтаруу','مرجوعی'],
 'Pay by card':['Mit Karte bezahlen','Kartla ödə','Картамен төлеу','Kart bilen töle','Karta orqali toʻlash','Карта менен төлөө','پرداخت با کارت'],
}
manual.update(json.loads((O/'manual-overrides.json').read_bytes()))
termsTree=ast.parse((R/'scripts/review-target-locale-terms.py').read_text(encoding='utf8'))
approvedTerms=ast.literal_eval(next(n.value for n in termsTree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='terms'for x in n.targets)))
approvedTerms.update(json.loads((R/'data/localization/terminology.json').read_bytes()))
approvedTerms.update(json.loads((R/'data/localization/catalogue-terminology.json').read_bytes()))
approvedPhrases={(lang,source):target for source,values in approvedTerms.items()for lang,target in zip(langs,values)}
for source,target in json.loads((R/'data/localization/terminology.de.json').read_bytes()).items():approvedPhrases[('de',source)]=target

for key,row in jobs.items():
 if row['text']in manual:
  for lang,value in zip(langs,manual[row['text']]):cache.execute('INSERT OR REPLACE INTO translations VALUES(?,?,?,?,?)',(lang,key,row['text'],value,'reviewed-interface-terminology'))
cache.commit()
# Uzbek storefront uses the Latin script. Proper names/codes remain untouched.
cyr=dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюяўғқҳ','abvgdeYojziyklmnoprstufxCChShShchIyEYuYaOʻGʻQH')) if False else {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'j','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'x','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'ʼ','ы':'i','ь':'','э':'e','ю':'yu','я':'ya','ў':'oʻ','ғ':'gʻ','қ':'q','ҳ':'h'}
def normalize(text,lang):
 text=''.join(str(unicodedata.decimal(c))if c.isdecimal()else c for c in text)
 text=re.sub(r'ZXQ\s*(\d+)\s*ZXQ',lambda m:'ZXQ'+m[1]+'ZXQ',text,flags=re.I)
 if lang=='uz':text=''.join(cyr.get(c,c)if not c.isupper()else cyr.get(c.lower(),c).capitalize()for c in text)
 return text.strip()
def invariant(t):return t in invariants or not re.search(r'[A-Za-z]',token.sub('',t))
invariants.update({'B','C','D','P','X','S','M','L','XS','XL','XXL','ALT','AOP','MKC','CM','MM','KG','Mdf','Pvc','DDP','EXW','FOB','CIF','CFR','TGIF','Luk','Lik','Lık','luk'})
def validate(source,target,lang):
 reviewed=approvedPhrases.get((lang,source))==target
 issues=translation_quality_errors(source,target,lang,reviewed=invariant(source)or reviewed)
 if 'fact_changed'in issues:raise ValueError('protected_value_changed')
 if issues:raise ValueError(issues[0])
 if not target.strip():raise ValueError('empty')
 if sorted(token.findall(source))!=sorted(token.findall(target)):raise ValueError('protected_value_changed')
 if invariant(source):return
 bare=token.sub('',source).strip(' -.,:;|()[]')
 if not invariant(source)and target.casefold()==source.casefold()and bare not in invariants and not reviewed:raise ValueError('english_copy')
 if lang in ['kk','ky','fa']and len(re.sub(r'\W','',bare))>3 and not re.search('[\u0400-\u04ff]'if lang in ['kk','ky']else'[\u0600-\u06ff]',target):raise ValueError('native_script_missing')
 if re.search(r'(\S{3,})(?:\s+\1){5,}',target):raise ValueError('repetition')
 if len(target)<len(source)*.2 and len(source)>60:raise ValueError('text_shortened')
modelPath='artifacts/target-locales-20261111/model';sp=sp.SentencePieceProcessor(model_file=modelPath+'/spiece.model');device='cuda'if ctranslate2.get_cuda_device_count()>0 else'cpu';model=ctranslate2.Translator(modelPath,device=device,compute_type='int8_float32',intra_threads=6 if device=='cpu'else 1,inter_threads=1)
print(json.dumps({'device':device,'compute':'int8_float32'}),flush=True)
def raw_translate(texts,languages):
 cache.commit()
 startInference=time.time();print(json.dumps({'inferenceStart':True,'items':len(texts),'maxChars':max(map(len,texts))}),flush=True)
 transported=[model_placeholders(text)for text in texts]
 inputs=[sp.encode('<2'+l+'> '+s,out_type=str)+['</s>']for (s,_),l in zip(transported,languages)]
 order=sorted(range(len(inputs)),key=lambda i:len(inputs[i]));translated=['']*len(inputs);truncated=0
 # Each small group has its own decoding bound. A single long legal paragraph
 # must not give a malformed two-word label a 512-token generation allowance.
 offset=0
 while offset<len(order):
  count=min(20,len(order)-offset)
  while True:
   indexes=order[offset:offset+count];limit=min(512,max(64,max(len(inputs[i])for i in indexes)*3+32))
   if count<=2 or count*limit<=3072:break
   count-=1
  result=model.translate_batch([inputs[i]for i in indexes],beam_size=2,max_batch_size=count,batch_type='examples',max_decoding_length=limit,repetition_penalty=1.08)
  for i,value in zip(indexes,result):
   if len(value.hypotheses[0])>=limit:truncated+=1;continue
   translated[i]=restore_model_placeholders(normalize(sp.decode(value.hypotheses[0]),languages[i]),transported[i][1])
  offset+=count
 print(json.dumps({'inferenceFinished':True,'items':len(texts),'seconds':round(time.time()-startInference,2),'truncated':truncated}),flush=True)
 return translated
def split(t):
 parts=re.split(r'(\n+)',t);out=[]
 for part in parts:
  if not part:continue
  if part.isspace():out.append(part);continue
  sentences=re.split(r'(?<=[.!?])\s+',part)if len(part)>380 else[part]
  for s in sentences:
   while len(s)>500:
    cut=s.rfind(' ',0,460);cut=cut if cut>100 else 460;out.append(s[:cut]);s=s[cut:].strip()
   if s:out.append(s)
 return out
cached={(l,k)for l,k in cache.execute('SELECT language,key FROM translations')};pending=[(lang,key,row)for key,row in sorted(jobs.items(),key=lambda x:(not x[1]['ui'],len(x[1]['text'])))for lang in langs if(lang,key)not in cached];print(json.dumps({'pending':len(pending),'cached':len(cached)}),flush=True)
cache.execute('CREATE TABLE IF NOT EXISTS fragments(language TEXT,source TEXT,target TEXT,PRIMARY KEY(language,source))')
fragmentCache={(l,s):t for l,s,t in cache.execute('SELECT language,source,target FROM fragments')}
termCache={(l,s):t for l,s,t in cache.execute('SELECT language,source,target FROM translations')if not token.search(s)}
fragmentCache.update(termCache);fragmentCache.update(approvedPhrases)
cache.execute('CREATE TABLE IF NOT EXISTS segments(language TEXT,source TEXT,target TEXT,method TEXT,PRIMARY KEY(language,source))')
segments={(l,s):(t,m)for l,s,t,m in cache.execute('SELECT language,source,target,method FROM segments')}
def remember_segment(lang,source,target,method='model-segment'):
 try:validate(source,target,lang)
 except ValueError as e:
  if str(e)!='english_copy'or not method.startswith('reviewed'):return False
 canonical,mapping=canonical_segment(source);forward={original:key for key,original in mapping.items()}
 try:value=rebind_segment(target,forward)
 except ValueError:return False
 if method.startswith('reviewed')or(lang,canonical)not in segments:
  cache.execute('INSERT OR REPLACE INTO segments VALUES(?,?,?,?)',(lang,canonical,value,method));segments[(lang,canonical)]=(value,method)
 return True
for(lang,source),target in fragmentCache.items():
 if len(source)<700:remember_segment(lang,source,target,'reviewed-terminology'if approvedPhrases.get((lang,source))==target else'model-fragment')
for lang,source,target,method in list(cache.execute('SELECT language,source,target,method FROM translations')):
 a,b=source.split('\n'),target.split('\n')
 if len(a)==len(b):
  for x,y in zip(a,b):
   if x.strip()and y.strip()and len(x)<700:remember_segment(lang,x.strip(),y.strip(),'reviewed-line'if method.startswith('reviewed')else'model-line')
cache.commit();print(json.dumps({'segmentMemory':len(segments)}),flush=True)
def translate(texts,languages):
 pieces=[split(text)for text in texts];tasks={};references=[];values={}
 for index,(parts,lang)in enumerate(zip(pieces,languages)):
  for partIndex,source in enumerate(parts):
   if not source.strip()or invariant(source):continue
   canonical,mapping=canonical_segment(source);key=(lang,canonical);references.append((index,partIndex,key,mapping))
   if key in segments:values[key]=segments[key][0]
   else:tasks[key]=canonical
 keys=list(tasks);outputs=raw_translate([tasks[k]for k in keys],[k[0]for k in keys])if keys else[]
 for (lang,canonical),target in zip(keys,outputs):
  if remember_segment(lang,canonical,target):values[(lang,canonical)]=target
  else:values[(lang,canonical)]=''
 failed=set()
 for index,partIndex,key,mapping in references:
  target=values[key]
  if not target:failed.add(index);continue
  try:pieces[index][partIndex]=rebind_segment(target,mapping)
  except ValueError:failed.add(index)
 return [''if i in failed else' '.join(parts).replace(' \n ','\n')for i,parts in enumerate(pieces)]
def fragment_parts(source):return re.split(r'(ZXQ\d+ZXQ)',source)
def fragment_requires_translation(piece):return bool(piece.strip())and not token.fullmatch(piece)and not invariant(piece.strip())
def prepare_fragments(rows):
 pairs=[];seen=set()
 for lang,key,row in rows:
  for piece in fragment_parts(row['text']):
   pair=(lang,piece.strip())
   if fragment_requires_translation(piece)and pair not in fragmentCache and pair not in seen:seen.add(pair);pairs.append(pair)
 values=translate([s for l,s in pairs],[l for l,s in pairs])if pairs else[]
 for (lang,source),target in zip(pairs,values):
  try:validate(source,target,lang)
  except ValueError:continue
  cache.execute('INSERT OR REPLACE INTO fragments VALUES(?,?,?)',(lang,source,target));fragmentCache[(lang,source)]=target
def preserve_fragments(source,lang):
 # A translation that drops a protected fact is never patched by guessing it.
 # Translate the surrounding text separately and keep source facts in place.
 pieces=fragment_parts(source);result=[]
 for piece in pieces:
  if not fragment_requires_translation(piece):result.append(piece);continue
  leading=piece[:len(piece)-len(piece.lstrip())];trailing=piece[len(piece.rstrip()):];text=piece.strip();pair=(lang,text)
  value=fragmentCache.get(pair)
  if value is None:
   raise ValueError('protected_fragment_needs_review')
  result.append(leading+value+trailing)
 value=''.join(result);validate(source,value,lang);return value
held=[];start=time.time();saved=0
for batchNo,offset in enumerate(range(0,len(pending),48),1):
 batch=pending[offset:offset+48];tasks=[];owners=[];parts=[split(row['text'])for _,_,row in batch];outputs=[list(v)for v in parts]
 for i,((lang,key,row),pieces)in enumerate(zip(batch,parts)):
  bare=token.sub('',row['text'])
  if len(token.findall(row['text']))>=2 and len(bare)<120 and not invariant(row['text']):outputs[i]=[''];continue
  for j,piece in enumerate(pieces):
   if not invariant(piece)and not piece.isspace():tasks.append((piece,lang));owners.append((i,j))
 values=translate([x[0]for x in tasks],[x[1]for x in tasks])if tasks else[]
 for(i,j),v in zip(owners,values):outputs[i][j]=v
 rowValues=[''if any(original.strip()and not value.strip()for original,value in zip(originals,pieces))else' '.join(pieces).replace(' \n ','\n')for originals,pieces in zip(parts,outputs)]
 rescue=[]
 for (lang,key,row),value in zip(batch,rowValues):
  try:validate(row['text'],value,lang)
  except ValueError as e:
   if str(e)=='protected_value_changed'or str(e)=='empty'and token.search(row['text']):rescue.append((lang,key,row))
 prepare_fragments(rescue)
 for (lang,key,row),value in zip(batch,rowValues):
  try:
   method='MADLAD400-v3-validated-offline'
   try:validate(row['text'],value,lang)
   except ValueError as e:
    if str(e)!='protected_value_changed'and not(str(e)=='empty'and token.search(row['text'])):raise
    value=preserve_fragments(row['text'],lang);method='MADLAD400-v3-validated-fragments'
   cache.execute('INSERT OR IGNORE INTO translations VALUES(?,?,?,?,?)',(lang,key,row['text'],value,method));saved+=1
  except ValueError as e:held.append({'language':lang,'key':key,'reason':str(e),'source':row['text'],'candidate':value})
 cache.commit()
 if batchNo%5==0:(O/'translation-held.json').write_text(json.dumps(held,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'batch':batchNo,'processed':min(offset+48,len(pending)),'total':len(pending),'saved':saved,'held':len(held),'seconds':round(time.time()-start)}),flush=True)
 if args.batches and batchNo>=args.batches:break
(O/'translation-held.json').write_text(json.dumps(held,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(O/'bindings.json').write_text(json.dumps({'entries':entries,'templates':jobs},ensure_ascii=False)+'\n',encoding='utf8');print(json.dumps({'finished':True,'saved':saved,'held':len(held)}),flush=True)
