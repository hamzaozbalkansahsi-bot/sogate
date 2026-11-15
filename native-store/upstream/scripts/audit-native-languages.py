"""Check public long-form translations for high-confidence wrong-language output.

Run in the isolated translation-tools environment. Model weights are QA tools,
not website assets. Short codes, names and literal postal addresses are not prose.
"""
from pathlib import Path
import collections,hashlib,json,re,sys,os
import fasttext
R=Path(__file__).resolve().parents[1];O=R/'artifacts/target-locales-20261111'
proofBytes=(O/'coverage.json').read_bytes();proof=json.loads(proofBytes);os.chdir(R);model=fasttext.load_model('artifacts/target-locales-20261111/lid.176.ftz')
issues=[];checked=collections.Counter();exceptions={}
exceptionFile=R/'data/localization/language-audit-exceptions.json'
if exceptionFile.exists():exceptions={(r['locale'],r['source'],r['targetSha256']):r['reason']for r in json.loads(exceptionFile.read_bytes())}
files={}
for locale in proof['locales']:
 files[locale]={}
 for kind,suffix in [('ui',''),('catalogue','.catalogue')]:
  body=(R/('web/locales/'+locale+suffix+'.json')).read_bytes();digest=hashlib.sha256(body).hexdigest();files[locale][kind]=digest
  if digest!=proof['files'][locale][kind]:raise RuntimeError('language_audit_dictionary_changed')
  payload=json.loads(body)
  if payload['locale']!=locale or payload['sourceInventorySha256']!=proof['sourceInventorySha256']:raise RuntimeError('language_audit_inventory_changed')
  for source,target in payload['translations'].items():
   text=re.sub(r'https?://\S+|[\w.+-]+@[\w.-]+|\d+(?:[.,]\d+)*','',target).replace('\n',' ')
   if 'N Gould St Ste N, Sheridan, WY'in source:text=text.replace('N Gould St Ste N, Sheridan, WY','').replace('United States','')
   if len(text)<200 or len(re.findall(r'[^\W\d_]+',text))<25:continue
   checked[locale]+=1
   # Use the underlying binding: the published Python wrapper's copy=False
   # conversion is incompatible with NumPy 2; no package is monkey-patched.
   predicted=model.f.predict(text+'\n',1,0.0,'strict')
   if not predicted:raise RuntimeError('language_audit_prediction_unavailable')
   confidence,label=predicted[0];actual=label.removeprefix('__label__');confidence=float(confidence)
   targetDigest=hashlib.sha256(target.encode()).hexdigest()
   if actual!=locale and confidence>=.8 and (locale,source,targetDigest)not in exceptions:issues.append({'locale':locale,'detected':actual,'confidence':round(confidence,4),'source':source,'target':target,'targetSha256':targetDigest})
(O/'current-language-candidates.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
result={'schema':1,'passed':proof['complete']and not issues,'complete':proof['complete'],'coverageSha256':hashlib.sha256(proofBytes).hexdigest(),'sourceInventorySha256':proof['sourceInventorySha256'],'files':files,'checked':dict(checked),'candidateCount':len(issues),'modelSha256':hashlib.sha256((O/'lid.176.ftz').read_bytes()).hexdigest(),'threshold':.8}
(O/'language-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({'complete':proof['complete'],'checked':sum(checked.values()),'candidates':len(issues),'pairs':dict(collections.Counter(r['locale']+'->'+r['detected']for r in issues))}))
if proof['complete']and issues:raise SystemExit(1)
