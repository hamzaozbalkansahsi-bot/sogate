"""Compile source-bound public dictionaries, preserving protected product facts.

Partial output is for local QA only. The production build requires complete=True
and current source digests in the generated coverage manifest.
"""
from pathlib import Path
import argparse,hashlib,json,re,sqlite3
R=Path(__file__).resolve().parents[1];O=R/'artifacts/target-locales-20261111'
p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');args=p.parse_args()
inventoryBytes=(O/'inventory.json').read_bytes();inv=json.loads(inventoryBytes)
import sys
sys.path.insert(0,str(R))
from lib.target_locale_templates import protected_template,interface_source,translation_quality_errors
proper=sorted(inv['properNames'],key=len,reverse=True)
token=re.compile(r'ZXQ\d+ZXQ')
def template(text,interface=False):return protected_template(text,tuple(proper),interface)
def restore(target,bindings):
 return re.sub(r'[ \t]+',' ',token.sub(lambda m:bindings[m[0]],target)).strip()
cache=sqlite3.connect(O/'translations.sqlite',timeout=300);records={(l,k):(s,t,m)for l,k,s,t,m in cache.execute('SELECT language,key,source,target,method FROM translations')}
compiled={};missing=[];methods={};sources={r['source']:r for r in inv['entries']}
for lang in inv['languages']:
 strings={}
 for source,row in sources.items():
  interface=interface_source(row)
  text,bindings=template(source,interface);key=hashlib.sha256(text.encode()).hexdigest();record=records.get((lang,key))
  if not record:missing.append({'locale':lang,'source':source,'template':key,'kinds':row['kinds']});continue
  original,target,method=record
  if original!=text:raise RuntimeError('translation_template_mismatch')
  if sorted(token.findall(text))!=sorted(token.findall(target)):raise RuntimeError('translation_protected_value_changed')
  issues=translation_quality_errors(text,target,lang,reviewed=method.startswith(('reviewed','source-fact-composition')))
  if issues:missing.append({'locale':lang,'source':source,'template':key,'kinds':row['kinds'],'quality':issues});continue
  strings[source]=restore(target,bindings);methods[method]=methods.get(method,0)+1
 # Complete composed legal blocks are stored as paragraphs in source JSON. The
 # public seller configuration uses exactly these paragraphs joined with blanks.
 legal=json.loads((R/'data/legal/payment-documents.en.json').read_bytes())
 for section in ['terms','returns']:
  if all(value in strings for value in legal[section]):strings['\n\n'.join(legal[section])]='\n\n'.join(strings[v]for v in legal[section])
 compiled[lang]={'schema':1,'locale':lang,'translations':strings,'sourceInventorySha256':hashlib.sha256(inventoryBytes).hexdigest()}
report={'schema':1,'complete':not missing,'locales':inv['languages'],'sources':len(sources),'missingCount':len(missing),'methods':methods,'sourceInventorySha256':hashlib.sha256(inventoryBytes).hexdigest(),'files':{},'sourceFiles':{}}
(O/'compile-missing.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if missing and not args.partial:
 (O/'coverage.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');raise SystemExit('Native dictionaries incomplete: '+str(len(missing)))
out=R/'web/locales';out.mkdir(parents=True,exist_ok=True)
for lang,payload in compiled.items():
 def is_ui(source):
  row=sources.get(source,{})
  return len(source)<=300 or 'ui'in row.get('kinds',[]) or source not in sources or any(re.search(r'(?:name|label|title|colour|color|variant|seo)',origin,re.I)for origin in row.get('origins',[]))
 ui={source:target for source,target in payload['translations'].items()if is_ui(source)}
 catalogue={source:target for source,target in payload['translations'].items()if source not in ui}
 report['files'][lang]={}
 for kind,strings in [('ui',ui),('catalogue',catalogue)]:
  part={**payload,'kind':kind,'translations':strings};name=lang+(''if kind=='ui'else'.catalogue')+'.json'
  body=(json.dumps(part,ensure_ascii=False,separators=(',',':'))+'\n').encode();(out/name).write_bytes(body);report['files'][lang][kind]=hashlib.sha256(body).hexdigest()
 # Document IDs, versions and source audit fields retain their original values.
 if not any(m['locale']==lang and any(o.startswith('legal/')for o in sources[m['source']]['origins'])for m in missing):
  source=json.loads((R/'data/legal/site-documents.en.json').read_bytes())
  def local(value,key=''):
   if isinstance(value,list):return[local(v,key)for v in value]
   if isinstance(value,dict):return{k:local(v,k)for k,v in value.items()}
   if isinstance(value,str)and key in ['title','summary','paragraphs']:return payload['translations'].get(value,value)if not re.search('[A-Za-z]',value)else payload['translations'][value]
   return value
  result=local(source);result['locale']=lang
  (R/('data/legal/site-documents.'+lang+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for folder,pattern in [('web','*.js'),('hosting','*.php')]:
 for path in sorted((R/folder).glob(pattern)):
  if not path.name.startswith('admin'):report['sourceFiles'][path.relative_to(R).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
for folder,pattern in [('data/localization','*.json'),('data/legal','*.en.json')]:
 for path in sorted((R/folder).glob(pattern)):report['sourceFiles'][path.relative_to(R).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
for name in ['lib/target_locale_templates.py','scripts/inventory-target-locales.mjs','scripts/compile-target-locales.py']:
 report['sourceFiles'][name]=hashlib.sha256((R/name).read_bytes()).hexdigest()
(O/'coverage.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'compiled':True,'complete':report['complete'],'missing':len(missing),'sources':len(sources)}))
