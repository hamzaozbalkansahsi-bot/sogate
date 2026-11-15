"""Bind reviewed native copy to the exact protected English source templates."""
from pathlib import Path
import sys,json,re,sqlite3,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from lib.target_locale_templates import protected_template,interface_source
O=R/'artifacts/target-locales-20261111';inv=json.loads((O/'inventory.json').read_bytes());rows={r['source']:r for r in inv['entries']};langs=inv['languages']
overrides=json.loads((R/'data/localization/reviewed-overrides.json').read_bytes());cache=sqlite3.connect(O/'translations.sqlite',timeout=300);count=0
for source,values in overrides.items():
 if source not in rows:raise RuntimeError('Reviewed source is not inventoried: '+source[:50])
 row=rows[source];text,bindings=protected_template(source,tuple(inv['properNames']),interface_source(row));key=hashlib.sha256(text.encode()).hexdigest()
 for lang,target in zip(langs,values):
  if target is None:continue
  available={}
  for marker,value in bindings.items():available.setdefault(value,[]).append(marker)
  if available:
   pattern=re.compile('|'.join(re.escape(v)for v in sorted(available,key=len,reverse=True)))
   def bind(match):
    value=match[0]
    if not available[value]:raise RuntimeError('Extra protected fact in reviewed translation')
    return available[value].pop(0)
   target=pattern.sub(bind,target)
  if any(available.values())or sorted(re.findall(r'ZXQ\d+ZXQ',text))!=sorted(re.findall(r'ZXQ\d+ZXQ',target)):raise RuntimeError('Reviewed protected facts differ: '+lang+' '+source[:50])
  if not target.strip():raise RuntimeError('Reviewed translation empty')
  cache.execute('INSERT OR REPLACE INTO translations VALUES(?,?,?,?,?)',(lang,key,text,target,'reviewed-native-interface-and-legal-copy'));count+=1
cache.commit();print(json.dumps({'reviewedSourceEntries':count}))
