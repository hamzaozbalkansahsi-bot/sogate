"""Resumable, sequential public source checks. Stop immediately on rate limiting."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin
import argparse,gzip,hashlib,importlib.util,json,time
import requests
R=Path(__file__).resolve().parents[1];OLD=R/'artifacts/bianca-20261112';E=R/'artifacts/paint-completion-20261112';E.mkdir(exist_ok=True);(E/'pages').mkdir(exist_ok=True)
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
imp=module('paint_resume_import','scripts/import-marketplace-paints.py');p=imp.m
def save(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)
session=requests.Session();session.headers.update({'Accept-Language':'tr-TR,tr;q=0.9','User-Agent':'NODENO supplier catalogue research (+https://nodenohome.com)'})
last=0;requests_count=0
class Limited(ValueError):pass
def fetch(url):
 global last,requests_count
 p.product_id(url);key=hashlib.sha256(url.encode()).hexdigest()[:24];receipt=E/'pages'/(key+'.json');file=E/'pages'/(key+'.html.gz')
 if receipt.exists()and file.exists():
  row=json.loads(receipt.read_bytes());body=gzip.decompress(file.read_bytes())
  if time.time()-row['at']<7200 and hashlib.sha256(body).hexdigest()==row['sha256']:return body,row
 pause=E/'source-rate-limit.json'
 if pause.exists()and json.loads(pause.read_bytes())['until']>time.time():raise Limited('source_rate_limit_pending')
 current=url
 for hop in range(3):
  time.sleep(max(0,2.5-(time.monotonic()-last)));last=time.monotonic();requests_count+=1
  response=session.get(current,timeout=(8,25),allow_redirects=False)
  if response.status_code in [403,429]:
   retry=response.headers.get('Retry-After','');delay=max(3600,int(retry))if retry.isdigit()else 3600;save(pause,{'at':int(time.time()),'until':int(time.time())+delay,'status':response.status_code});raise Limited('source_rate_limit_pending')
  if response.status_code in [301,302,307,308]:current=p.source_redirect(url,current,response.headers.get('Location',''));continue
  if response.status_code!=200:raise ValueError('http_'+str(response.status_code))
  body=response.content
  if len(body)>3000000:raise ValueError('document_too_large')
  row={'url':url,'finalUrl':current,'at':int(time.time()),'sha256':hashlib.sha256(body).hexdigest(),'file':file.relative_to(R).as_posix()};file.write_bytes(gzip.compress(body));save(receipt,row);return body,row
 raise ValueError('redirect_limit')
def main():
 a=argparse.ArgumentParser();a.add_argument('--limit',type=int,default=250);args=a.parse_args();old=json.loads((OLD/'offers.json').read_bytes());reportfile=E/'source-checks.json';done=json.loads(reportfile.read_bytes())if reportfile.exists()else{'products':[],'held':[],'pending':[],'checkedUrls':[]}
 seeds=[r['url']for r in old['held']if r['reason']!='outside_verified_paint_scope']
 seeds += [r['url']for r in json.loads((OLD/'selected-offers.json').read_bytes())['held']]
 checked=set(done['checkedUrls']);checkedids={p.product_id(u)for u in checked};pending=[];queued=set()
 for u in done.get('pending',[])+seeds:
  key=p.product_id(u)
  if key not in checkedids and key not in queued:pending.append(u);queued.add(key)
 imp.fetch=fetch;byid={r['sourceProductId']:r for r in done['products']};holds={r['url']:r for r in done['held']};completed=0
 while pending and completed<args.limit:
  url=pending.pop(0);row=imp.one(url)
  if row.get('reason')=='source_rate_limit_pending':pending.insert(0,url);break
  checked.add(url);checkedids.add(p.product_id(url));completed+=1
  if row.get('held'):holds[url]=row
  else:
   byid[row['sourceProductId']]=row;holds.pop(url,None)
   for child in row.get('variantUrls',[]):
    key=p.product_id(child)
    if key not in checkedids and key not in queued:pending.append(child);queued.add(key)
   if len(pending)>1200:raise RuntimeError('unexpected_variant_expansion')
  done={'products':list(byid.values()),'held':list(holds.values()),'pending':pending,'checkedUrls':list(checked),'checkedAt':datetime.now(timezone.utc).isoformat(),'requestsThisRun':requests_count};save(reportfile,done)
  if completed%10==0:print(json.dumps({'checked':completed,'verified':len(byid),'held':len(holds),'pending':len(pending)}),flush=True)
 done={'products':list(byid.values()),'held':list(holds.values()),'pending':pending,'checkedUrls':list(checked),'checkedAt':datetime.now(timezone.utc).isoformat(),'requestsThisRun':requests_count};save(reportfile,done)
 print(json.dumps({'checkedThisRun':completed,'verified':len(byid),'held':len(holds),'pending':len(pending),'rateLimited':bool(pending and(E/'source-rate-limit.json').exists())}),flush=True)
if __name__=='__main__':main()
