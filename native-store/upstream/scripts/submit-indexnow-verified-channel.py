"""Submit current canonical URLs once, stopping on pending verification or rejection."""
from pathlib import Path
from datetime import datetime,timezone
import argparse, hashlib, importlib.util,json,requests
R=Path(__file__).resolve().parents[1]
O=R/'artifacts/indexnow-live-diagnosis-20261112'
parser=argparse.ArgumentParser();parser.add_argument('--endpoint',choices=['global','yandex'],required=True);parser.add_argument('--fresh-key',action='store_true');args=parser.parse_args()
endpoint={'global':'https://api.indexnow.org/indexnow','yandex':'https://yandex.com/indexnow'}[args.endpoint]
key=json.loads((O/'renewed-key.json' if args.fresh_key else R/'data/seo-indexnow.json').read_bytes())
proof=json.loads((O/'preflight/preflight.json').read_bytes())
urls=(O/'preflight/canonical-urls.txt').read_text().splitlines()
assert hashlib.sha256('\n'.join(urls).encode()).hexdigest()==proof['urlListSha256']
P=O/(args.endpoint+('-fresh' if args.fresh_key else '')+'-bulk.json')
if P.exists():raise SystemExit('Receipt exists; refusing blind duplicate submission')
q=requests.get(key['keyLocation'],timeout=35,allow_redirects=False)
assert q.status_code==200 and q.content==key['key'].encode()
record={'startedAt':datetime.now(timezone.utc).isoformat(),'endpoint':endpoint,'urlListSha256':proof['urlListSha256'],'totalUrls':len(urls),'batches':[],'bulkSubmissionComplete':False,'ownershipVerified':False,'sourceRelease':proof['health']['releaseHash']}
for offset in range(0,len(urls),10000):
    h=requests.get('https://nodenohome.com/api/health',timeout=30);h.raise_for_status()
    assert h.json()['releaseHash']==record['sourceRelease'],'Live release changed; rebuild preflight before further submissions'
    batch=urls[offset:offset+10000]
    item={'at':datetime.now(timezone.utc).isoformat(),'offset':offset,'urlCount':len(batch),'urlSha256':hashlib.sha256('\n'.join(batch).encode()).hexdigest()}
    try:
        q=requests.post(endpoint,json={k:key[k]for k in ['host','key','keyLocation']}|{'urlList':batch},timeout=60,allow_redirects=False)
        item.update(httpStatus=q.status_code,response=q.text[:1600],retryAfter=q.headers.get('Retry-After'))
    except requests.RequestException as err:
        item.update(httpStatus=None,deliveryUncertain=True,errorClass=type(err).__name__)
    record['batches'].append(item)
    record['ownershipVerified']=any(x.get('httpStatus')==200 for x in record['batches'])
    record['confirmedAcceptedUrls']=sum(x['urlCount']for x in record['batches']if x.get('httpStatus')==200)
    record['bulkSubmissionComplete']=record['confirmedAcceptedUrls']==len(urls)
    P.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(item),flush=True)
    if item.get('httpStatus')!=200:break
print(json.dumps({'complete':record['bulkSubmissionComplete'],'ownershipVerified':record['ownershipVerified'],'confirmedAcceptedUrls':record.get('confirmedAcceptedUrls',0)}))
