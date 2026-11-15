"""One controlled IndexNow retry after Turhost confirmed bot access was enabled.

Reads the current public sitemap index, preserves existing keys and receipts,
and stops on any rejection or uncertain delivery. No hosting changes occur.
"""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs
import argparse, hashlib, json, re, time
import xml.etree.ElementTree as ET
import requests

R = Path(__file__).resolve().parents[1]
E = R / 'artifacts/indexnow-turhost-recheck-20261112'
ORIGIN = 'https://nodenohome.com'
ENDPOINT = 'https://yandex.com/indexnow'
LOCALES = {'tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'}
ALLOWED_PAGES = {'home','catalog','categories','help','shipping','wholesale','sets'}


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, record):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def health():
    response = requests.get(ORIGIN+'/api/health', timeout=40)
    response.raise_for_status()
    result = response.json()
    assert result['status']=='ok' and result['mediaReady'] is True
    return {k:result[k] for k in ['status','releaseHash','products','categories','mediaReady','checkoutEnabled']}


def get_map(url):
    parsed=urlparse(url)
    assert parsed.scheme=='https' and parsed.netloc=='nodenohome.com'
    assert re.fullmatch(r'/sitemap-(?:(?:products|pages)-[a-z]{2}|blog)\.xml',parsed.path)
    response=requests.get(url,timeout=60)
    response.raise_for_status()
    root=ET.fromstring(response.content)
    assert root.tag.endswith('}urlset')
    urls=[]
    for entry in root.findall('{*}url/{*}loc'):
        value=entry.text
        parsed=urlparse(value);query=parse_qs(parsed.query)
        assert parsed.scheme=='https' and parsed.netloc=='nodenohome.com' and not parsed.fragment
        if parsed.path=='/':
            assert set(query)<= {'lang','page','category','product','set','pg'}
            assert query.get('lang',[''])[0] in LOCALES
            assert query.get('page',['home'])[0] in ALLOWED_PAGES
        else:
            assert re.fullmatch(r'/blog(?:/[a-z0-9]+(?:-[a-z0-9]+)*)?',parsed.path)
            assert set(query)<= {'lang'} and query.get('lang',['tr'])[0] in {'tr','en','ru','ar'}
        assert all(len(v)==1 for v in query.values())
        urls.append(value)
    return {'url':url,'urls':urls,'httpStatus':response.status_code,'sha256':hashlib.sha256(response.content).hexdigest()}


def main():
    global E
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--output-dir',type=Path,default=E)
    parser.add_argument('--max-batches',type=int,default=0,help='Stop after this many batches; zero sends all only while accepted')
    args=parser.parse_args()
    E=args.output_dir.resolve()
    assert E.is_relative_to((R/'artifacts').resolve()),'Receipt directory must remain inside artifacts'
    assert args.max_batches>=0
    E.mkdir(exist_ok=True)
    before=health()
    key_data=json.loads((R/'data/seo-indexnow.json').read_bytes())
    key=key_data['key'];location=key_data['keyLocation']
    assert re.fullmatch('[A-Za-z0-9-]{8,128}',key)
    assert location==ORIGIN+'/'+key+'.txt'
    ownership=[]
    for name,agent in [('standard','NODENO-IndexNow-Verification/1.0'),('bingbot','Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)'),('yandexbot','Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)')]:
        response=requests.get(location,headers={'User-Agent':agent,'Cache-Control':'no-cache'},timeout=40,allow_redirects=False)
        matches=response.content==key.encode('ascii')
        ownership.append({'agent':name,'httpStatus':response.status_code,'exactBytesMatch':matches,'redirect':response.is_redirect,'bytes':len(response.content),'contentType':response.headers.get('Content-Type')})
        assert response.status_code==200 and matches and not response.is_redirect
    index=requests.get(ORIGIN+'/sitemap.xml',timeout=45)
    index.raise_for_status();root=ET.fromstring(index.content)
    assert root.tag.endswith('}sitemapindex')
    locations=[n.text for n in root.findall('{*}sitemap/{*}loc')]
    assert len(locations)==len(set(locations)) and locations
    with ThreadPoolExecutor(max_workers=4)as pool:maps=list(pool.map(get_map,locations))
    urls=list(dict.fromkeys(url for record in maps for url in record['urls']))
    digest=hashlib.sha256('\n'.join(urls).encode()).hexdigest()
    after=health();assert after['releaseHash']==before['releaseHash'],'Live release changed during preflight; retry separately after publication settles'
    preflight={'checkedAt':now(),'health':before,'ownership':ownership,'realSearchEngineIpAccessProvenBySpoofedUserAgent':False,'sitemaps':[{k:v for k,v in m.items()if k!='urls'}|{'urlCount':len(m['urls'])}for m in maps],'sitemapCount':len(maps),'totalCanonicalUrls':len(urls),'urlListSha256':digest,'sourceSupportTicket':'BDC-161-38545','supportReplyAtTurkeyTime':'2026-11-11 13:44:49','supportSaidBotAccessEnabled':True,'keyChanged':False,'hostingChanged':False}
    save(E/'preflight.json',preflight)
    (E/'canonical-urls.txt').write_text('\n'.join(urls)+'\n',encoding='utf-8')
    print(json.dumps({'stage':'preflight_verified','releaseHash':before['releaseHash'],'products':before['products'],'sitemaps':len(maps),'urls':len(urls),'apply':args.apply}),flush=True)
    if not args.apply:return
    ledger=E/'submission.json'
    prior=json.loads(ledger.read_bytes())if ledger.exists()else{}
    if prior.get('urlListSha256')==digest and prior.get('bulkSubmissionComplete'):
        print(json.dumps({'stage':'already_accepted','urls':len(urls)}));return
    if prior.get('batches'):
        raise RuntimeError('This controlled attempt already has receipts; do not resend blindly')
    receipt={'startedAt':now(),'releaseHashBefore':before['releaseHash'],'urlListSha256':digest,'endpoint':ENDPOINT,'ownershipFileExactBytesVerified':True,'totalUrls':len(urls),'batches':[],'bulkSubmissionComplete':False,'indexedOrRankingGuaranteed':False,'hostingChanged':False,'keyChanged':False,'protocolSource':'https://www.indexnow.org/documentation'}
    for start in range(0,len(urls),10000):
        assert health()['releaseHash']==before['releaseHash'],'Live release changed before submission'
        batch=urls[start:start+10000];item={'attemptedAt':now(),'offset':start,'urlCount':len(batch),'urlSha256':hashlib.sha256('\n'.join(batch).encode()).hexdigest()}
        try:
            response=requests.post(ENDPOINT,json={'host':'nodenohome.com','key':key,'keyLocation':location,'urlList':batch},headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'NODENO-IndexNow/1.0'},timeout=60,allow_redirects=False)
            item.update(httpStatus=response.status_code,accepted=response.status_code in [200,202],ownershipValidationPending=response.status_code==202,retryAfter=response.headers.get('Retry-After'),response=response.text[:1200].replace(key,'[redacted]'),responseDate=response.headers.get('Date'))
        except requests.RequestException as error:
            item.update(httpStatus=None,accepted=False,deliveryUncertain=True,errorClass=type(error).__name__)
        receipt['batches'].append(item)
        receipt['acceptedBulkUrls']=sum(b['urlCount']for b in receipt['batches']if b['accepted'])
        receipt['unsubmittedUrls']=len(urls)-sum(b['urlCount']for b in receipt['batches'])
        receipt['rejectedOrUncertainUrls']=sum(b['urlCount']for b in receipt['batches']if not b['accepted'])
        receipt['recordedAt']=now()
        save(ledger,receipt)
        print(json.dumps({k:v for k,v in item.items()if k!='response'}),flush=True)
        if not item['accepted'] or (args.max_batches and len(receipt['batches'])>=args.max_batches):break
    receipt['bulkSubmissionComplete']=receipt.get('acceptedBulkUrls',0)==len(urls) and all(b.get('httpStatus')==200 for b in receipt['batches']) and all(b.get('httpStatus')==200 for b in receipt['batches'])
    receipt['ownershipValidationPending']=any(b.get('ownershipValidationPending')for b in receipt['batches'])
    receipt['releaseHashAfter']=health()['releaseHash']
    receipt['releaseChangedDuringSubmission']=receipt['releaseHashAfter']!=before['releaseHash']
    receipt['finishedAt']=now()
    save(ledger,receipt)
    print(json.dumps({'stage':'finished','complete':receipt['bulkSubmissionComplete'],'acceptedUrls':receipt.get('acceptedBulkUrls',0),'remainingUnsubmitted':receipt.get('unsubmittedUrls',len(urls)),'validationPending':receipt['ownershipValidationPending']}),flush=True)


if __name__=='__main__':main()
