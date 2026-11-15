"""Apply explicit native-language corrections to inventoried factual templates."""
from pathlib import Path
import hashlib,json,sqlite3,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from lib.target_locale_templates import protected_template,interface_source,translation_quality_errors
O=R/'artifacts/target-locales-20261111';inv=json.loads((O/'inventory.json').read_bytes());templates={protected_template(r['source'],tuple(inv['properNames']),interface_source(r))[0]for r in inv['entries']};db=sqlite3.connect(O/'translations.sqlite',timeout=300)
rows=json.loads((R/'data/localization/reviewed-template-fixes.json').read_bytes())['fixes']
for row in rows:
 source,locale,target=row['source'],row['locale'],row['target']
 if source not in templates or locale not in inv['languages']:raise RuntimeError('unbound_reviewed_template')
 if translation_quality_errors(source,target,locale,reviewed=True):raise RuntimeError('invalid_reviewed_template:'+locale+' '+source[:50])
 key=hashlib.sha256(source.encode()).hexdigest();db.execute('INSERT OR REPLACE INTO translations VALUES(?,?,?,?,?)',(locale,key,source,target,'reviewed-native-template-fix'))
db.commit();print(json.dumps({'reviewedTemplateFixes':len(rows)}))
