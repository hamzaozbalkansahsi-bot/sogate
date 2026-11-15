"""Reuse verified native phrases around unchanged factual identifiers."""
from pathlib import Path
import sys,ast,hashlib,json,re,sqlite3
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from lib.target_locale_templates import protected_template,interface_source,translation_quality_errors
O=R/'artifacts/target-locales-20261111';inv=json.loads((O/'inventory.json').read_bytes());db=sqlite3.connect(O/'translations.sqlite',timeout=300);token=re.compile(r'ZXQ\d+ZXQ')
known={(l,k):(s,t,m)for l,k,s,t,m in db.execute('SELECT language,key,source,target,method FROM translations')};phrases={(l,s):t for l,s,t in db.execute('SELECT language,source,target FROM fragments')if not translation_quality_errors(s,t,l)}
for (l,k),(s,t,m)in known.items():
 if not token.search(s)and not translation_quality_errors(s,t,l,reviewed=m.startswith(('reviewed','source-fact-composition'))):phrases[(l,s)]=t
tree=ast.parse((R/'scripts/review-target-locale-terms.py').read_text(encoding='utf8'));terms=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='terms'for x in n.targets)))
terms.update(json.loads((R/'data/localization/terminology.json').read_bytes()));terms.update(json.loads((R/'data/localization/catalogue-terminology.json').read_bytes()))
for source,values in terms.items():
 for lang,target in zip(inv['languages'],values):phrases[(lang,source)]=target
for source,target in json.loads((R/'data/localization/terminology.de.json').read_bytes()).items():phrases[('de',source)]=target
folded={(l,s.casefold()):t for(l,s),t in phrases.items()}
lexical={lang:re.compile(r'(?<![A-Za-z])(?:'+'|'.join(re.escape(s)for s in sorted(terms,key=len,reverse=True))+r')(?![A-Za-z])',re.I)for lang in inv['languages']}
termFold={s.casefold():v for s,v in terms.items()}
opaque={'B','C','P','X','S','M','L','XL','XXL','ALT','AOP','MKC','CM','MM','KG','Mdf','Pvc','DDP','EXW','FOB','CIF','CFR','TGIF','Luk','Lik','Lık','luk'}
def phrase(source,lang):
 if(lang,source)in phrases:return phrases[(lang,source)]
 if(lang,source.casefold())in folded:return folded[(lang,source.casefold())]
 if source in opaque:return source
 match=re.fullmatch(r'([^\w]*)(.*?)([^\w]*)',source)
 if match and match[2]!=source:
  value=phrase(match[2],lang)
  if value is not None:return match[1]+value+match[3]
 pattern=lexical[lang]
 if pattern.search(source)and not re.search(r'[A-Za-z]',pattern.sub('',source)):
  return pattern.sub(lambda m:termFold[m[0].casefold()][inv['languages'].index(lang)],source)
 return None
jobs={}
for row in inv['entries']:
 source,_=protected_template(row['source'],tuple(inv['properNames']),interface_source(row));jobs[hashlib.sha256(source.encode()).hexdigest()]=source
saved=0;needs={}
for key,source in jobs.items():
 for lang in inv['languages']:
  if(lang,key)in known:continue
  pieces=re.split(r'(ZXQ\d+ZXQ)',source);result=[];missing=False
  for piece in pieces:
   if not re.search('[A-Za-z]',token.sub('',piece)):result.append(piece);continue
   text=piece.strip();target=phrase(text,lang)
   if target is None:
    needs.setdefault(text,set()).add(lang);missing=True;break
   leading=piece[:len(piece)-len(piece.lstrip())];trailing=piece[len(piece.rstrip()):];result.append(leading+target+trailing)
  if missing:continue
  target=''.join(result)
  if sorted(token.findall(source))!=sorted(token.findall(target)):raise RuntimeError('composed_fact_count_changed')
  if translation_quality_errors(source,target,lang,reviewed=True):continue
  db.execute('INSERT OR IGNORE INTO translations VALUES(?,?,?,?,?)',(lang,key,source,target,'source-fact-composition'));saved+=1
db.commit();(O/'composition-needs.json').write_text(json.dumps([{'source':s,'locales':sorted(ls)}for s,ls in sorted(needs.items(),key=lambda x:(len(x[0]),x[0]))],ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'composed':saved,'unresolvedPhrases':len(needs)}))
