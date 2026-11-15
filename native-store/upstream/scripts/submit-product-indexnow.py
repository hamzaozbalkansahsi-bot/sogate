"""Notify participating engines about public canonical sitemap URLs, never private/query-filter URLs."""
from pathlib import Path
from datetime import datetime,timezone
import json,requests,hashlib,xml.etree.ElementTree as ET
from urllib.parse import urlparse,parse_qs
R=Path(__file__).resolve().parents[1];E=R/'artifacts/seo-products';proof=json.loads((E/'release.json').read_bytes());deployment=json.loads((E/'deployment.json').read_bytes());assert deployment['passed']and deployment['releaseHash']==proof['releaseHash'];keydata=json.loads((R/'data/seo-indexnow.json').read_bytes());session=requests.Session();check=session.get(keydata['keyLocation'],timeout=40);check.raise_for_status();assert check.text.strip()==keydata['key']
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'};urls=[]
for lang in ['tr','en','ru','ar']:
 for kind in ['products','pages']:
  response=session.get('https://nodenohome.com/sitemap-'+kind+'-'+lang+'.xml',timeout=60);response.raise_for_status();root=ET.fromstring(response.content)
  for entry in root.findall('s:url/s:loc',ns):
   url=entry.text;p=urlparse(url);q=parse_qs(p.query);assert p.scheme=='https'and p.netloc=='nodenohome.com'and p.path=='/'and set(q)<=set(['lang','page','category','product','set','pg']);assert q.get('lang',[''])[0]in ['tr','en','ru','ar'];assert q.get('page',['home'])[0]in ['home','catalog','categories','help','shipping','wholesale','sets'];urls.append(url)
urls=list(dict.fromkeys(urls));receipts=[];ledger=E/'indexnow-submission.json';previous=json.loads(ledger.read_bytes())if ledger.exists()else{'batches':[]}
if previous.get('releaseHash')!=proof['releaseHash']:previous={'batches':[]}
for start in range(0,len(urls),10000):
 batch=urls[start:start+10000];digest=hashlib.sha256('\n'.join(batch).encode()).hexdigest();existing=next((r for r in previous['batches']if r['urlSha256']==digest and r['httpStatus']in [200,202]),None)
 if existing:receipts.append(existing);continue
 endpoint=keydata.get('endpoint','https://yandex.com/indexnow');assert endpoint in {'https://api.indexnow.org/indexnow','https://yandex.com/indexnow'};response=session.post(endpoint,json={'host':'nodenohome.com','key':keydata['key'],'keyLocation':keydata['keyLocation'],'urlList':batch},timeout=60,allow_redirects=False)
 item={'submittedAt':datetime.now(timezone.utc).isoformat(),'urlCount':len(batch),'urlSha256':digest,'httpStatus':response.status_code,'accepted':response.status_code in [200,202],'response':response.text[:250].replace(keydata['key'],'[redacted]')};receipts.append(item);ledger.write_text(json.dumps({'releaseHash':proof['releaseHash'],'ownershipFileVerified':True,'totalUrls':len(urls),'batches':receipts,'indexationOrRankingGuaranteed':False},indent=2)+'\n');print(json.dumps({k:v for k,v in item.items()if k!='response'}),flush=True)
 if response.status_code not in [200,202]:raise SystemExit('IndexNow did not accept this batch; no speculative success recorded')
print(json.dumps({'notifiedCanonicalUrls':len(urls),'acceptedBatches':len(receipts),'googleSearchConsoleVerified':False}),flush=True)
