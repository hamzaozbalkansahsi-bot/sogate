"""Archive public paint offers with exact seller selection, without account access."""
from pathlib import Path
import concurrent.futures, gzip, hashlib, importlib.util, json, re, sys, time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import requests

R=Path(__file__).resolve().parents[1]; O=R/'artifacts/bianca-20261112'; P=O/'pages';P.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('paint',R/'lib/marketplace_paints.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def family(name,brand):
 text=name.casefold()
 if brand=='Bianca':
  for pat,key in [('silfex','silfex'),('diamond|dıamond','diamond'),('maximo|maxımo','maximo'),('mermer.*(?:efekt|sprey)|marble','marble'),('metalik|metal renk','metallic'),('ahşap renk|ahşap görün|ahsap renk|ahsap gorun','wood-effect'),('fırça|rulo|ipek|tava','tools'),('stella','acrylic')]:
   if re.search(pat,text):return key
 if brand=='Filli Boya':
  for pat,key in [('afilli.*(?:vernik|varnish)','afilli-varnish'),('afilli.*(?:sprey|spray)','afilli-spray'),('afilli.*(?:fırça|rulo|stencil|örtü)','afilli-tools'),('afilli.*(?:multisurface|akrilik|silk)','afilli'),('aqua.?reno.*mutfak','aqua-reno-kitchen'),('aqua.?reno.*banyo','aqua-reno-bath'),('aqua.?lux|aqualüx','aqualux')]:
   if re.search(pat,text):return key
 return None

def fetch(url):
 url=urljoin('https://www.trendyol.com',url);m.product_id(url)
 key=hashlib.sha256(url.encode()).hexdigest()[:24]; archive=P/(key+'.html.gz');receipt=P/(key+'.json')
 if archive.exists()and receipt.exists():
  r=json.loads(receipt.read_bytes());body=gzip.decompress(archive.read_bytes())
  if time.time()-r['at']<7200 and hashlib.sha256(body).hexdigest()==r['sha256']:return body,r
 pause=O/'source-rate-limit.json'
 if pause.exists()and json.loads(pause.read_bytes())['until']>time.time():raise ValueError('source_rate_limit_pending')
 response=requests.get(url,timeout=(10,35),allow_redirects=False,headers={'Accept-Language':'tr-TR,tr;q=0.9','User-Agent':'NODENO supplier catalogue research (+https://nodenohome.com)'})
 if response.status_code in [403,429]:
  pause.write_text(json.dumps({'at':int(time.time()),'until':int(time.time())+3600,'status':response.status_code}),encoding='utf-8')
  raise ValueError('source_rate_limit_pending')
 if response.status_code!=200:raise ValueError('http_'+str(response.status_code))
 body=response.content
 if len(body)>3000000:raise ValueError('document_too_large')
 r={'url':url,'at':int(time.time()),'sha256':hashlib.sha256(body).hexdigest(),'file':archive.relative_to(R).as_posix()}
 archive.write_bytes(gzip.compress(body));receipt.write_text(json.dumps(r),encoding='utf-8');return body,r

def one(url):
 try:
  url=urljoin('https://www.trendyol.com',url).split('?')[0];body,evidence=fetch(url);row=m.parse(body,url)
  group=family(row['title'],row['brand'])
  if not group:return {'held':True,'url':url,'reason':'outside_verified_paint_scope'}
  merchant=m.best_merchant(row);pinned=url+'?merchantId='+str(merchant['id'])
  if row['merchant']['id']!=merchant['id']:body,evidence=fetch(pinned)
  row=m.parse(body,pinned,merchant['id']);row.update(sourceUrl=pinned,sourceEvidence=evidence,family=group,status='verified',fetchedAt=datetime.now(timezone.utc).isoformat())
  if not row['images']:raise ValueError('missing_product_photo')
  # Missing package information is a review state, never an invented size.
  if not row['package']or row['package'].lower()in ['tek ebat','standart','tek boyut']:
   size=re.search(r'\b\d+(?:[.,]\d+)?\s*(?:ml|lt|litre|kg|gr|l)\b',row['title'],re.I)
   row['package']=size[0]if size else row['package']
  return row
 except Exception as e:return {'held':True,'url':url,'reason':str(e)if isinstance(e,ValueError)else type(e).__name__}

def main():
 seeds=json.loads((O/'store-links.json').read_bytes())+json.loads((O/'filli-links.json').read_bytes())
 seeds+=['/bianca/silfex-cok-amacli-silikon-sokucu-1-kg-p-841010197','/bianca/stella-su-bazli-saf-akrilik-yeni-nesil-donusum-boyasi-p-819338039','/filli-boya/afilli-multisurface-akrilik-metalik-120-ml-d-150-p-302125191','/filli-boya/afilli-multisurface-akrilik-parlak-250-ml-isilti-150-p-302110701','/filli-boya/afilli-multisurface-akrilik-ipeksi-mat-120-ml-cakilli-kum-p-302512429']
 pending=list(dict.fromkeys(urljoin('https://www.trendyol.com',u).split('?')[0]for u in seeds));seen=set();rows=[]
 for level in range(2):
  with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
   for i,row in enumerate(pool.map(one,pending),1):
    rows.append(row);seen.add(urljoin('https://www.trendyol.com',row.get('sourceUrl',row.get('url'))).split('?')[0])
    (O/'import-progress.json').write_text(json.dumps({'level':level,'done':i,'batch':len(pending),'verified':sum(not r.get('held')for r in rows),'held':sum(bool(r.get('held'))for r in rows)}),encoding='utf-8')
    if i%20==0:print(json.dumps({'level':level,'done':i,'batch':len(pending)}),flush=True)
  pending=list(dict.fromkeys(u for r in rows if not r.get('held')for u in r.get('variantUrls',[])if u not in seen))
  if len(pending)>800:raise RuntimeError('unexpected_variant_expansion')
  if not pending:break
 byid={r['sourceProductId']:r for r in rows if not r.get('held')};held=[r for r in rows if r.get('held')]
 report={'schema':1,'fetchedAt':datetime.now(timezone.utc).isoformat(),'products':list(byid.values()),'held':held,'variantDiscoveryRemaining':len([u for r in byid.values()for u in r['variantUrls']if u not in seen])}
 (O/'offers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'verified':len(byid),'held':len(held),'brands':{b:sum(r['brand']==b for r in byid.values())for b in ['Bianca','Filli Boya']},'variantDiscoveryRemaining':report['variantDiscoveryRemaining']}),flush=True)

if __name__=='__main__':main()
