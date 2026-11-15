"""Translate unresolved catalogue phrases with explicit furniture context.

The context is removed only at a labelled NODENO prefix. All factual-token,
numeric and native-script checks from the main translator still apply.
"""
from pathlib import Path
import ast,json,re,sys,time,os
R=Path(__file__).resolve().parents[1]
tree=ast.parse((R/'scripts/translate-target-locales.py').read_text(encoding='utf8'))
nodes=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='held' for t in node.targets):break
 nodes.append(node)
namespace={'__file__':str(R/'scripts/translate-target-locales.py'),'__name__':'native_segment_rescue'}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(R/'scripts/translate-target-locales.py'),'exec'),namespace)
O=namespace['O'];db=namespace['cache'];remember=namespace['remember_segment'];validate=namespace['validate'];raw=namespace['raw_translate'];langs=namespace['langs']
needs=json.loads((O/'segment-needs.json').read_bytes());tasks=[];seen=set()
for row in needs:
 source=row['source'].strip()
 for lang in row['locales']:
  key=(lang,source)
  if key in seen:continue
  seen.add(key);tasks.append(key)
print(json.dumps({'rescueSegments':len(tasks)}),flush=True)
held=[];saved=0;start=time.time()
for offset in range(0,len(tasks),48):
 batch=tasks[offset:offset+48]
 prefix=os.environ.get('NODENO_TRANSLATION_PREFIX','NODENO product information: ')
 outputs=raw([prefix+source for lang,source in batch],[lang for lang,source in batch])
 for (lang,source),output in zip(batch,outputs):
  # Never strip an arbitrary sentence from an unlabelled result.
  match=re.match(r'^\s*[^:：\n]{0,160}[:：]\s*',output)
  if match and not re.search(r'NODENO|Нодено|نودنو|نودینو',match[0],re.I):match=None
  if not match:held.append({'locale':lang,'source':source,'reason':'context_prefix_missing','candidate':output});continue
  target=output[match.end():].strip()
  try:validate(source,target,lang)
  except ValueError as e:held.append({'locale':lang,'source':source,'reason':str(e),'candidate':target});continue
  if remember(lang,source,target,'model-furniture-context'):
   db.execute('INSERT OR REPLACE INTO fragments VALUES(?,?,?)',(lang,source,target));saved+=1
 db.commit()
 (O/'context-rescue-held.json').write_text(json.dumps(held,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'processed':min(offset+48,len(tasks)),'total':len(tasks),'saved':saved,'held':len(held),'seconds':round(time.time()-start)}),flush=True)
