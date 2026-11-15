"""Check the actual visible page, including explicit quote requests."""
from pathlib import Path
import concurrent.futures,importlib.util,json,time
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('wood',R/'scripts/import-wood-suppliers.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
catalog=json.loads((m.OUT/'alka-catalog.json').read_bytes());products=catalog['products']
def one(p):
 try:
  body,e=m.fetch(p['sourceUrl'],m.OUT/'alka-visible-pages');v=m.alka_visible_offer(body);time.sleep(.3);return {'productId':p['id'],'sourceUrl':p['sourceUrl'],**v,'evidence':e}
 except Exception as ex:return {'productId':p['id'],'status':'unverified','error':str(ex)[:100]}
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
 for i,row in enumerate(pool.map(one,products),1):
  rows.append(row)
  if i%50==0:print(json.dumps({'visiblePagesVerified':i,'total':len(products)}),flush=True)
(m.OUT/'alka-visible-prices.json').write_text(json.dumps({'products':rows},ensure_ascii=False,indent=2),encoding='utf8')
from collections import Counter
print(json.dumps(dict(Counter(p['status']for p in rows))),flush=True)
