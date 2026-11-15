"""Quarantine observable model corruption; never publish or patch guessed facts."""
from pathlib import Path
import sys,json,sqlite3,collections
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from lib.target_locale_templates import translation_quality_errors
O=R/'artifacts/target-locales-20261111';db=sqlite3.connect(O/'translations.sqlite',timeout=300)
backup=O/'translations-before-quality-audit.sqlite'
if not backup.exists():
 with sqlite3.connect(backup)as target:db.backup(target)
blocked=[]
for table,columns in [('translations','language,key,source,target,method'),('fragments','language,source,target'),('segments','language,source,target,method')]:
 for row in list(db.execute('SELECT '+columns+' FROM '+table)):
  if table=='translations':lang,key,source,target,method=row
  elif table=='fragments':lang,source,target=row;key=source;method='model-fragment'
  else:lang,source,target,method=row;key=source
  issues=translation_quality_errors(source,target,lang,reviewed=method.startswith(('reviewed','source-fact-composition')))
  if not issues:continue
  blocked.append({'table':table,'locale':lang,'source':source,'target':target,'method':method,'issues':issues})
  db.execute('DELETE FROM '+table+' WHERE language=? AND '+('key'if table=='translations'else'source')+'=?',(lang,key))
db.commit()
(O/'quarantined-translations.json').write_text(json.dumps(blocked,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'quarantined':len(blocked),'tables':dict(collections.Counter(r['table']for r in blocked)),'issues':dict(collections.Counter(v for r in blocked for v in r['issues']))}))
