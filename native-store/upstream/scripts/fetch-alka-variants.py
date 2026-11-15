"""Fetch exact public variation offers; parent minimum prices are not propagated."""
from pathlib import Path
import concurrent.futures,importlib.util,json,time
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('wood',R/'scripts/import-wood-suppliers.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
parents=[]
for f in (m.OUT/'alka-api').glob('*.json'):
 if f.name.endswith('.receipt.json'):continue
 d=json.loads(f.read_bytes())
 if isinstance(d,list):parents+=d
jobs=[(p,v)for p in parents for v in p.get('variations',[])]
def one(job):
 p,v=job
 try:
  body,e=m.fetch('https://alkaahsap.com/wp-json/wc/store/v1/products/'+str(v['id']),m.OUT/'alka-variant-api','json');raw=json.loads(body);r=m.parse_alka(raw)
  if raw.get('parent')!=p['id']:raise ValueError('variation_parent_mismatch')
  r['modelId']=m.identity('alka',m.text(p.get('sku')),p['permalink'])[0];r['parentSourcePageId']=str(p['id']);r['salesUnit']=m.parse_alka(p)['salesUnit'];r['categories']=m.parse_alka(p)['categories'];r['variantAttributes']=v['attributes'];r['evidence']=e
  time.sleep(.3);return r,None
 except Exception as ex:return None,{'parent':p['id'],'variation':v['id'],'error':str(ex)[:100]}
products=[];errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
 for i,(p,e)in enumerate(pool.map(one,jobs),1):
  if p:products.append(p)
  if e:errors.append(e)
  if i%50==0:print(json.dumps({'variants':i,'total':len(jobs),'errors':len(errors)}),flush=True)
(m.OUT/'alka-variants.json').write_text(json.dumps({'products':products,'errors':errors,'expected':len(jobs)},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'complete':True,'products':len(products),'errors':len(errors)}),flush=True)
