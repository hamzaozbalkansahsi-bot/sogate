"""Fresh, sequential checks of each held offer; original publication evidence is immutable."""
from pathlib import Path
import importlib.util,json,time
import requests
R=Path(__file__).resolve().parents[1];E=R/'artifacts/paint-resolution-20261112';E.mkdir(exist_ok=True);(E/'pages').mkdir(exist_ok=True)
def module(n,f):
 s=importlib.util.spec_from_file_location(n,R/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('resolution_source','scripts/continue-paint-import.py');r.E=E
def save(v):r.save(E/'checks.json',v)
def main():
 before=requests.get('https://nodenohome.com/api/health',timeout=30);before.raise_for_status();r.save(E/'live-before.json',before.json())
 rows=json.loads((R/'artifacts/paint-completion-20261112/review-list.json').read_bytes());state=json.loads((E/'checks.json').read_bytes())if(E/'checks.json').exists()else{'checked':[]};seen={v['sourceProductId']for v in state['checked']};pending=[p for p in rows if p['sourceProductId']not in seen]
 for p in pending:
  result={'sourceProductId':p['sourceProductId'],'previousReason':p['reason'],'original':p,'checkedAt':int(time.time())}
  try:
   body,receipt=r.fetch(p['sourceUrl']);raw=r.p.parse(body,p['sourceUrl']);raw.update(sourceUrl=p['sourceUrl'],sourceEvidence=receipt,family=r.imp.family(raw['title'],raw['brand']))
   result.update(offer=raw,reviewReason=r.p.offer_review(raw),qualified=raw['merchant']['authorized']and isinstance(raw['merchant']['score'],(int,float))and raw['merchant']['score']>=9)
  except ValueError as error:
   if str(error)=='source_rate_limit_pending':state['pausedUntil']=json.loads((E/'source-rate-limit.json').read_bytes())['until'];save(state);break
   result['error']=str(error)
  except requests.RequestException as error:result['error']=type(error).__name__
  state['checked'].append(result);save(state)
  if len(state['checked'])%10==0:print(json.dumps({'checked':len(state['checked']),'total':len(rows)}),flush=True)
 state['remaining']=len(rows)-len(state['checked']);save(state);print(json.dumps({'checked':len(state['checked']),'remaining':state['remaining']}),flush=True)
if __name__=='__main__':main()
