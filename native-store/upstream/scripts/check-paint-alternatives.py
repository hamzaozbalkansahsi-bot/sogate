"""Check discovered alternative product offers without retrying restricted search pages."""
from pathlib import Path
import importlib.util,json
R=Path(__file__).resolve().parents[1];E=R/'artifacts/paint-alternatives-20261112';P=E/'product-checks';P.mkdir(exist_ok=True);(P/'pages').mkdir(exist_ok=True)
def module(n,f):
 s=importlib.util.spec_from_file_location(n,R/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('alternative_reader','scripts/continue-paint-import.py');r.E=P;r.imp.fetch=r.fetch
def main():
 urls=json.loads((E/'candidate-urls.json').read_bytes());path=E/'alternative-offers.json';rows=json.loads(path.read_bytes())if path.exists()else[];seen={r.p.product_id(p.get('sourceUrl',p.get('url')))for p in rows}
 for url in urls:
  if r.p.product_id(url)in seen:continue
  row=r.imp.one(url)
  if row.get('reason')=='source_rate_limit_pending':print(json.dumps({'paused':True,'reason':'product_page_access_limited'}));break
  rows.append(row);seen.add(r.p.product_id(url));r.save(path,rows);print(json.dumps({'id':r.p.product_id(url),'verified':not row.get('held'),'reason':row.get('reason'),'merchant':row.get('merchant'),'package':row.get('package'),'color':row.get('color')},ensure_ascii=True),flush=True)
if __name__=='__main__':main()
