"""Resumable local translation of the public editorial bank; no API keys or paid jobs."""
from pathlib import Path
import os,ctypes,json,re,time,hashlib,argparse
R=Path(__file__).resolve().parents[1]
os.chdir(R)
# CTranslate2 loads CUDA with LoadLibrary; PATH is needed in addition to Python's DLL handles.
handles=[]
for folder in (R/'artifacts/translation-tools/Lib/site-packages/nvidia').glob('*/bin'):
 os.environ['PATH']=str(folder)+os.pathsep+os.environ['PATH'];handles.append(os.add_dll_directory(str(folder)))
 if (folder/'cublas64_12.dll').exists():handles.append(ctypes.WinDLL(str(folder/'cublas64_12.dll')))
import ctranslate2,sentencepiece as sp
O=R/'data/blog-locales';O.mkdir(exist_ok=True)
C=R/'artifacts/blog-20261112';C.mkdir(exist_ok=True)
MODELS=R/'artifacts/supplier-expansion/publication/local-models'
sha=lambda value:hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def model(pair):
 p=next((MODELS/('translate-'+pair)).glob('*/sentencepiece.model')).parent
 return sp.SentencePieceProcessor(model_file=(p/'sentencepiece.model').relative_to(R).as_posix()),ctranslate2.Translator((p/'model').relative_to(R).as_posix(),device='cuda',compute_type='int8_float32')
engines={lang:model(pair)for lang,pair in [('en','tr_en'),('ru','en_ru'),('ar','en_ar')]}
def translate(texts,lang):
 tokenizer,translator=engines[lang];segments=[];owners=[]
 for i,text in enumerate(texts):
  for sentence in re.split(r'(?<=[.!?])\s+',text):
   # Short complete sentences keep the model inside its trained context window.
   if sentence.strip():segments.append(sentence);owners.append(i)
 encoded=[tokenizer.encode(x,out_type=str)for x in segments]
 result=translator.translate_batch(encoded,beam_size=3,replace_unknowns=True,max_batch_size=2048,batch_type='tokens',max_input_length=0,max_decoding_length=384,repetition_penalty=1.1)
 output=[''for _ in texts]
 for owner,row in zip(owners,result):
  value=tokenizer.decode(row.hypotheses[0]);output[owner]+= (' 'if output[owner]else'')+value
 return output
def flatten(a):
 return [a['title'],a['description'],a['intro'],*a['keywords'],*[text for s in a['sections']for text in [s['heading'],*s['paragraphs'],*s.get('list',[])]],*a['checklist']]
def rebuild(a,values):
 i=iter(values);b={k:next(i)for k in ['title','description','intro']};b['keywords']=[next(i)for _ in a['keywords']];b['sections']=[]
 for s in a['sections']:
  row={'heading':next(i),'paragraphs':[next(i)for _ in s['paragraphs']]}
  if s.get('list'):row['list']=[next(i)for _ in s['list']]
  b['sections'].append(row)
 b['checklist']=[next(i)for _ in a['checklist']];return b
def numbers(s):return sorted(re.findall(r'\d+(?:[.,]\d+)?',s.replace('٫','.').replace('،',',')))
def errors(source,translated,lang):
 result=[]
 for i,(s,t)in enumerate(zip(source,translated)):
  if not t.strip()or(len(s)>70 and len(t)<len(s)*.25):result.append([i,'empty_or_short'])
  sn=[x.replace(',','.')for x in numbers(s)];tn=[x.replace(',','.')for x in numbers(t)]
  if sn!=tn:result.append([i,'numeric_difference'])
  if re.search(r'(\S{3,})(?:\s+\1){5,}',t):result.append([i,'repetition'])
  if lang in ['ru','ar']and len(s)>25 and not re.search('[\u0400-\u04ff]'if lang=='ru'else'[\u0600-\u06ff]',t):result.append([i,'native_script_missing'])
 return result
def run():
 p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');p.add_argument('--minutes',type=int,default=120);args=p.parse_args();end=time.time()+args.minutes*60
 while True:
  articles=[]
  for path in sorted((R/'data/blog').glob('*/*.json')):
   try:articles.extend(json.loads(path.read_bytes()))
   except json.JSONDecodeError:continue
  completed=0;held=[]
  for a in articles:
   source=flatten(a);version=sha(source);outputs={}
   for lang in ['en','ru','ar']:
    folder=O/lang;folder.mkdir(exist_ok=True);target=folder/(a['id']+'.json')
    if target.exists():
     cached=json.loads(target.read_bytes())
     if cached.get('sourceSha256')==version:outputs[lang]=cached;continue
    texts=source if lang=='en'else flatten(outputs['en']['content'])
    translated=translate(texts,lang);issues=errors(texts,translated,lang)
    # Preserve factual numbers by translating the pieces around each literal when needed.
    for index,reason in list(issues):
     if reason!='numeric_difference':continue
     parts=re.split(r'(\d+(?:[.,]\d+)?)',texts[index]);words=[x for i,x in enumerate(parts)if i%2==0 and x.strip()];values=iter(translate(words,lang));translated[index]=''.join(next(values)if i%2==0 and x.strip()else x for i,x in enumerate(parts))
    issues=errors(texts,translated,lang)
    content=rebuild(a,translated)
    if lang=='ru':
     # Painting in these guides means coating a surface, not fine art.
     for s in content['sections']:
      s['paragraphs']=[x.replace('живопись','покраска').replace('Живопись','Покраска')for x in s['paragraphs']]
    receipt={'sourceSha256':version,'sourceLanguage':'tr','targetLanguage':lang,'provider':'Argos OpenNMT local pinned model','localOnly':True,'numericTokensVerified':not any(e[1]=='numeric_difference'for e in issues),'checks':issues,'reviewStatus':'automatic-checks-passed'if not issues else'held','content':content}
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');outputs[lang]=receipt
    print(json.dumps({'id':a['id'],'language':lang,'held':len(issues)}),flush=True)
   completed+=1
   for lang,receipt in outputs.items():
    if receipt['checks']:held.append({'id':a['id'],'locale':lang,'checks':receipt['checks']})
  (C/'translations.json').write_text(json.dumps({'articles':len(articles),'completed':completed,'localOnly':True,'paidRequests':0,'held':held},indent=2)+'\n')
  if not args.watch or time.time()>end or len(articles)>=250:break
  time.sleep(20)
if __name__=='__main__':run()
