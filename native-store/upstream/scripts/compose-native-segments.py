"""Reassemble complete descriptions from validated sentence translations."""
from pathlib import Path
import ast,collections,hashlib,json,re,sqlite3,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from lib.target_locale_templates import protected_template,interface_source,canonical_segment,rebind_segment,translation_quality_errors,terminology_key
O=R/'artifacts/target-locales-20261111';inv=json.loads((O/'inventory.json').read_bytes());db=sqlite3.connect(O/'translations.sqlite',timeout=300)
tree=ast.parse((R/'scripts/translate-target-locales.py').read_text(encoding='utf8'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='split');namespace={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'<source-split>','exec'),namespace);split=namespace['split']
segments={};terms=ast.literal_eval(next(n.value for n in ast.parse((R/'scripts/review-target-locale-terms.py').read_text(encoding='utf8')).body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='terms'for x in n.targets)));terms.update(json.loads((R/'data/localization/terminology.json').read_bytes()));terms.update(json.loads((R/'data/localization/catalogue-terminology.json').read_bytes()))
for lang,source,target,method in db.execute('SELECT language,source,target,method FROM segments'):
 if not translation_quality_errors(source,target,lang,reviewed=method.startswith('reviewed')):segments[(lang,source.strip())]=(target,method)
def remember(lang,source,target,method):
 if translation_quality_errors(source,target,lang,reviewed=method.startswith(('reviewed','source-fact-composition'))):return
 canonical,inverse=canonical_segment(source.strip());forward={v:k for k,v in inverse.items()}
 try:converted=rebind_segment(target,forward)
 except ValueError:return
 segments[(lang,canonical)]=(converted,method)
records={(l,k):(s,t,m)for l,k,s,t,m in db.execute('SELECT language,key,source,target,method FROM translations')}
for (lang,key),(source,target,method)in records.items():
 if len(source)<700:remember(lang,source,target,method)
 a,b=source.split('\n'),target.split('\n')
 if len(a)==len(b):
  for x,y in zip(a,b):
   if x.strip()and y.strip()and len(x)<700:remember(lang,x.strip(),y.strip(),method)
for source,values in terms.items():
 for lang,target in zip(inv['languages'],values):remember(lang,source,target,'reviewed-terminology')
for source,target in json.loads((R/'data/localization/terminology.de.json').read_bytes()).items():remember('de',source,target,'reviewed-terminology')
reviewed=json.loads((R/'data/localization/reviewed-segments.json').read_bytes())
if reviewed['languages']!=inv['languages']:raise RuntimeError('reviewed_segment_language_order_changed')
for group in reviewed['groups']:
 for source in group['sources']:
  for lang,target in zip(inv['languages'],group['translations']):
   if translation_quality_errors(source,target,lang,reviewed=True):raise RuntimeError('invalid_reviewed_segment:'+source[:60])
   remember(lang,source,target,'reviewed-native-segment')
   db.execute('INSERT OR REPLACE INTO segments VALUES(?,?,?,?)',(lang,source,target,'reviewed-native-segment'))
for row in json.loads((R/'data/localization/reviewed-segment-fixes.json').read_bytes())['fixes']:
 lang,source,target=row['locale'],row['source'],row['target']
 if lang not in inv['languages'] or translation_quality_errors(source,target,lang,reviewed=True):raise RuntimeError('invalid_reviewed_segment_fix')
 remember(lang,source,target,'reviewed-native-segment-fix')
 db.execute('INSERT OR REPLACE INTO segments VALUES(?,?,?,?)',(lang,source,target,'reviewed-native-segment-fix'))
folded={(lang,source.casefold()):row for (lang,source),row in segments.items()}
termPattern=re.compile(r'(?<![A-Za-z])(?:'+'|'.join(re.escape(s) for s in sorted(terms,key=len,reverse=True))+r')(?![A-Za-z])',re.I)
termFold={terminology_key(s):v for s,v in terms.items()}
trusted=('reviewed-native-segment','reviewed-terminology','reviewed-native-template-fix','reviewed-native-interface-and-legal-copy','reviewed-interface-or-compound-terminology')
def literal(source,lang,depth=0,review_only=False):
 if not re.search('[A-Za-z]',re.sub(r'ZXQ\d+ZXQ','',source)):return source
 canonical,mapping=canonical_segment(source.strip());row=segments.get((lang,canonical)) or folded.get((lang,canonical.casefold()))
 if row and (not review_only or row[1].startswith(trusted)):
  try:return rebind_segment(row[0],mapping)
  except ValueError:return None
 # Compound technical labels use only reviewed terminology. A partially known
 # phrase is never emitted with untranslated English words left between terms.
 if termPattern.search(source) and not re.search('[A-Za-z]',termPattern.sub('',source)):
  return termPattern.sub(lambda m:termFold[terminology_key(m[0])][inv['languages'].index(lang)],source)
 if depth<3:
  match=re.fullmatch(r'([^\w]*)(.*?)([^\w]*)',source,re.S)
  if match and match[2] and match[2]!=source:
   value=literal(match[2],lang,depth+1,review_only)
   if value is not None:return match[1]+value+match[3]
  pieces=re.split(r'(\n+|\s*[|;:]\s*|(?<=[.!?])\s+)',source)
  if len(pieces)>1:
   values=[]
   for i,piece in enumerate(pieces):
    value=piece if i%2 else literal(piece,lang,depth+1,review_only)
    if value is None:break
    values.append(value)
   else:return ''.join(values)
 return None
def part(source,lang,review_only=False):
 value=literal(source,lang,review_only=review_only)
 if value is not None:return value
 values=[]
 for piece in re.split(r'(ZXQ\d+ZXQ)',source):
  text=piece.strip();value=literal(text,lang,review_only=review_only)
  if value is None:return None
  leading=piece[:len(piece)-len(piece.lstrip())];trailing=piece[len(piece.rstrip()):]if text else'';values.append(leading+value+trailing)
 return ''.join(values)
jobs={}
for row in inv['entries']:
 source,_=protected_template(row['source'],tuple(inv['properNames']),interface_source(row));jobs[hashlib.sha256(source.encode()).hexdigest()]=source
saved=0;missing=collections.defaultdict(lambda:{'count':0,'locales':set()})
for key,source in jobs.items():
 for lang in inv['languages']:
  existing=records.get((lang,key));review_only=existing is not None
  if existing and existing[2].startswith(('reviewed-native-template-fix','reviewed-native-interface-and-legal-copy')):continue
  values=[];failed=False
  for piece in split(source):
   value=part(piece,lang,review_only)
   if value is None:
    failed=True
    if not review_only:
     canonical,_=canonical_segment(piece);missing[canonical]['count']+=1;missing[canonical]['locales'].add(lang)
   values.append(value or'')
  if failed:continue
  target=' '.join(values).replace(' \n ','\n')
  if translation_quality_errors(source,target,lang,reviewed=True):continue
  db.execute('INSERT OR REPLACE INTO translations VALUES(?,?,?,?,?)',(lang,key,source,target,'reviewed-native-segment-composition'if review_only else'reviewed-segment-composition'));saved+=1
db.commit();needs=[{'source':source,'count':v['count'],'locales':sorted(v['locales'])}for source,v in sorted(missing.items(),key=lambda x:(-x[1]['count'],len(x[0])))]
(O/'segment-needs.json').write_text(json.dumps(needs,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'composed':saved,'missingSegments':len(needs),'missingOccurrences':sum(v['count']for v in needs)}))
