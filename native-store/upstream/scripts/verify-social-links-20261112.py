"""Read-only HTTPS acceptance for the social-link publication."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import json
import urllib.request

R = Path(__file__).resolve().parents[1]
E = R/'artifacts/social-links-20261112'
proof = json.loads((E/'release.json').read_bytes())


def inspect(case):
    host, locale = case
    origin = 'https://'+host
    def get(path):
        request = urllib.request.Request(origin+path, headers={'Cache-Control':'no-cache'})
        with urllib.request.urlopen(request, timeout=45) as response:
            assert response.status == 200 and response.geturl().startswith(origin+'/'), 'host_changed'
            return response.read()
    health = json.loads(get('/api/health'))
    assert health['status'] == 'ok' and health['releaseHash'] == proof['releaseHash']
    assert health['products'] == 3602 and health['mediaReady'] is True and health['checkoutEnabled'] is True
    config = json.loads(get('/api/config'))
    assert config['socials'] == proof['socials']
    html = get('/?lang='+locale).decode()
    assert '<meta name="p:domain_verify" content="9d9b9982b35fcc574dc9032a9f47c691">' in html
    return {'host':host,'locale':locale,'sevenSocialUrlsCorrect':True,'pinterestTagPresent':True,
            'httpsAndHostPreserved':True,'checkoutAndMediaPreserved':True,'products':health['products']}


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(inspect, [('nodenohome.com','tr'),('www.nodenohome.com','en'),('nodenohome.com.tr','ru'),('www.nodenohome.com.tr','ar')]))
    record = {'passed':True,'checkedAt':datetime.now(timezone.utc).isoformat(),'releaseHash':proof['releaseHash'],
              'checks':checks,'ordersCreated':0,'chargesCreated':0}
    (E/'live-acceptance.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'domains':len(checks),'releaseHash':proof['releaseHash']}))
