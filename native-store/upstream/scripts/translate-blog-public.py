"""Draft translations of public editorial text with resumable, fact-checked receipts.

Uses the same public translation endpoint already used by catalogue tooling. No credentials,
subscriptions, private account data or paid API are involved. Drafts require editorial review.
"""
from pathlib import Path
import argparse,json,hashlib,re,time,requests,threading
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1];O=R/'data/blog-translations';O.mkdir(exist_ok=True);E=R/'artifacts/blog-20261112';E.mkdir(exist_ok=True)
lock=threading.Lock();next_request=0
def flatten(a):return [a['title'],a['description'],a['intro'],*a['keywords'],*[text for s in a['sections']for text in [s['heading'],*s['paragraphs'],*s.get('list',[])]],*a['checklist']]
def rebuild(a,values):
 i=iter(values);b={k:next(i)for k in ['title','description','intro']};b['keywords']=[next(i)for _ in a['keywords']];b['sections']=[]
 for s in a['sections']:
  row={'heading':next(i),'paragraphs':[next(i)for _ in s['paragraphs']]}
  if s.get('list'):row['list']=[next(i)for _ in s['list']]
  b['sections'].append(row)
 b['checklist']=[next(i)for _ in a['checklist']];return b
def numbers(value):return sorted(x.replace(',','.')for x in re.findall(r'\d+(?:[.,]\d+)?',value.replace('٫','.')))
def quality(source,target,lang):
 issues=[]
 for i,(s,t)in enumerate(zip(source,target)):
  if not t.strip()or(len(s)>70 and len(t)<len(s)*.4):issues.append([i,'empty_or_short'])
  if numbers(s)!=numbers(t):issues.append([i,'numeric_difference'])
  for operator in ['×','÷','=']:
   if s.count(operator)!=t.count(operator):issues.append([i,'formula_operator_changed'])
  if lang in ['ru','ar']and len(s)>20 and not re.search('[\u0400-\u04ff]'if lang=='ru'else'[\u0600-\u06ff]',t):issues.append([i,'native_script_missing'])
 return issues
def request(text,lang):
 global next_request
 for attempt in range(5):
  with lock:
   now=time.monotonic();delay=max(0,next_request-now);next_request=max(now,next_request)+.7
  if delay:time.sleep(delay)
  response=requests.get('https://translate.googleapis.com/translate_a/single',params={'client':'gtx','sl':'tr','tl':lang,'dt':'t','q':text},timeout=(10,45))
  if response.status_code in [403,429]:time.sleep(min(120,15*(2**attempt)));continue
  response.raise_for_status();raw=response.content;data=response.json();return ''.join(x[0]for x in data[0]if x and x[0]),hashlib.sha256(raw).hexdigest()
 raise RuntimeError('translation_rate_limited')
def one(job):
 a,lang=job;source=flatten(a);version=hashlib.sha256(json.dumps(source,ensure_ascii=False,sort_keys=True).encode()).hexdigest();folder=O/lang;folder.mkdir(exist_ok=True);target=folder/(a['id']+'.json')
 old=None
 if target.exists():
  old=json.loads(target.read_bytes())
  if old.get('sourceSha256')==version and old.get('content',{}).get('visualLabels'):return
  if old.get('sourceSha256')==version and old.get('reviewStatus')=='editor-reviewed':
   labels=a.get('visual',{}).get('labels',[]);value,_=request('\n'.join(labels),lang);translated=value.splitlines()
   if len(translated)!=len(labels):translated=[request(x,lang)[0]for x in labels]
   old['content']['visualLabels']=translated;old['visualReviewPending']=True
   target.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return
 visual=a.get('visual',{}).get('labels',[]);input_texts=source+visual
 value,response_hash=request('\n'.join(input_texts),lang);translated=value.splitlines()
 if len(translated)!=len(input_texts):
  # Preserve exact editorial field boundaries when the service has joined lines.
  translated=[]
  for text in input_texts:translated.append(request(text,lang)[0])
 issues=quality(input_texts,translated,lang)
 content=rebuild(a,translated[:len(source)]);content['visualLabels']=translated[len(source):]
 receipt={'sourceSha256':version,'sourceLanguage':'tr','targetLanguage':lang,'provider':'Google public translation endpoint','responseSha256':response_hash,'paidRequests':0,'numericTokensVerified':not any(x[1]=='numeric_difference'for x in issues),'checks':issues,'reviewStatus':'needs-editor-review','content':content}
 temporary=target.with_suffix('.tmp');temporary.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temporary.replace(target)
 print(json.dumps({'id':a['id'],'locale':lang,'draft':True,'checks':issues}),flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');p.add_argument('--minutes',type=int,default=120);args=p.parse_args();end=time.monotonic()+args.minutes*60
 while True:
  articles=[]
  for file in sorted((R/'data/blog').glob('*/*.json')):
   try:articles.extend(json.loads(file.read_bytes()))
   except json.JSONDecodeError:continue
  with ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(one,[(a,lang)for a in articles for lang in ['en','ru','ar']]))
  counts={lang:len(list((O/lang).glob('*.json')))for lang in ['en','ru','ar']};(E/'public-translations.json').write_text(json.dumps({'articles':len(articles),'translations':counts,'paidRequests':0,'requiresEditorialReview':True},indent=2)+'\n')
  if not args.watch or len(articles)>=250 or time.monotonic()>end:break
  time.sleep(15)
if __name__=='__main__':main()
