"""Verify exact seller identity against manually reviewed manufacturer sales-point evidence."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,importlib.util,json,re
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[1];E=R/'artifacts/paint-alternatives-20261112';P=E/'product-checks'
def module(n,f):
 s=importlib.util.spec_from_file_location(n,R/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('verified_alternative_reader','scripts/continue-paint-import.py');r.E=P;m=r.p
def independent(merchant,brand,registry):
 e=registry.get(str(merchant['id']))
 return bool(brand=='Filli Boya'and e and e.get('reviewed')is True and e.get('nameAndAddressMatched')is True and e['issuer']=='Filli Boya'and e['merchantId']==str(merchant['id'])and isinstance(merchant.get('score'),(int,float))and merchant['score']>=9)
def main():
 registry=json.loads((E/'trusted-merchants.json').read_bytes())
 for e in registry.values():
  proof=e['manufacturerEvidence'];u=urlsplit(proof['url']);assert u.scheme=='https'and u.hostname=='www.filliboya.com'and u.path.startswith('/iletisim/satis-noktalari/');assert hashlib.sha256((R/proof['file']).read_bytes()).hexdigest()==proof['sha256']
 old=json.loads((R/'artifacts/paint-resolution-20261112/checks.json').read_bytes())['checked'];held=json.loads((R/'artifacts/paint-resolution-20261112/review-list.json').read_bytes());ids={h['sourceProductId']for h in held};path=E/'verified-alternatives.json';rows=json.loads(path.read_bytes())if path.exists()else[];done={p['sourceProductId']for p in rows}
 for q in old:
  p=q.get('offer');pid=q['sourceProductId']
  if pid not in ids or pid in done or not p:continue
  candidates=[v for v in [p['merchant']]+p['alternatives']if isinstance(v.get('score'),(int,float))and v['score']>=9 and(v['authorized']or independent(v,p['brand'],registry))]
  if not candidates:rows.append({'sourceProductId':pid,'held':True,'reason':'no_verified_alternative_merchant'});r.save(path,rows);continue
  merchant=sorted(candidates,key=lambda a:(-a['score'],a['id']))[0];url=p['sourceUrl'].split('?')[0]+'?merchantId='+str(merchant['id'])
  try:
   body,evidence=r.fetch(url);v=m.parse(body,url,merchant['id']);proof=registry.get(str(merchant['id']))if not v['merchant']['authorized']else None
   if proof:
    full=m.states(body)['__envoy__SHARED_PROPS']['product']['merchantListing']['merchant'];assert independent(v['merchant'],v['brand'],registry)
    assert all(full[k]==proof[k]for k in ['officialName','cityName','address']),'merchant_legal_identity_changed'
   v.update(sourceUrl=url,sourceEvidence=evidence,merchantVerification=proof,family=r.imp.family(v['title'],v['brand']),fetchedAt=datetime.fromtimestamp(evidence['at'],timezone.utc).isoformat())
   if not m.package_value(v['package']):
    matches=re.findall(r'\b\d+(?:[.,]\d+)?\s*(?:ml|lt|litre|kg|gr|l)\b',v['title']+' '+v['color'],re.I)
    if len(set(matches))==1:v['package']=matches[0]
   rows.append(v);r.save(path,rows);print(json.dumps({'id':pid,'seller':v['merchant']['name'],'score':v['merchant']['score'],'badge':v['merchant']['authorized'],'manufacturerMatched':bool(proof),'package':v['package'],'color':v['color']},ensure_ascii=True),flush=True)
  except ValueError as ex:
   if str(ex)=='source_rate_limit_pending':break
   rows.append({'sourceProductId':pid,'held':True,'reason':str(ex)});r.save(path,rows)
 print(json.dumps({'checked':len(rows),'offers':sum(not r.get('held')for r in rows)}))
if __name__=='__main__':main()
