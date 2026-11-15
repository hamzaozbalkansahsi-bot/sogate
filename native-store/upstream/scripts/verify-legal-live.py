"""Read-only published legal acceptance: no customer registrations, orders or charges."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,secrets,time,urllib.request,urllib.error
R=Path(__file__).resolve().parents[1];E=R/'artifacts/legal-20261110';proof=json.loads((E/'release-preparation.json').read_bytes());release=R/proof['release']
def get(host,path):
 url='https://'+host+path+('&'if'?'in path else'?')+'legal_acceptance='+secrets.token_hex(6)
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache'}),timeout=20)as response:
    assert response.url.split('/')[2]==host;return response.read(),dict(response.headers)
  except (urllib.error.URLError,TimeoutError):
   if attempt==2:raise
   time.sleep(attempt+1)
def domain(host):
 health=json.loads(get(host,'/api/health')[0]);status=json.loads(get(host,'/api/payments/status')[0]);config=json.loads(get(host,'/api/config')[0])
 assert health['releaseHash']==proof['releaseHash']and health['mediaReady']and health['checkoutEnabled']and status['enabled']and not status['test']and config['checkoutEnabled']
 assert status['seller']['termsVersion']=='2026-11-10.3'
 for locale in ['tr','en','ru','ar']:
  source=json.loads((R/'data/legal'/('payment-documents.'+locale+'.json')).read_bytes())
  assert status['seller']['terms'][locale]=='\n\n'.join(source['terms'])and status['seller']['returns'][locale]=='\n\n'.join(source['returns'])
 assert b'/legal/kvkk'in get(host,'/legal?lang=tr')[0]
 for name in ['app.js','payments.js','legal.js','legal-links.js','legal.css','privacy-preferences.js','store-insights.js']:
  assert get(host,'/'+name)[0]==(release/'public'/name).read_bytes(),name
 return {'host':host,'releaseHash':health['releaseHash'],'hostPreserved':True,'liveCheckoutEnabled':True,'termsVersion':'2026-11-10.3','saleTextsMatchSource':True,'publicModulesMatch':True,'mediaReady':True}
with ThreadPoolExecutor(max_workers=2)as pool:domains=list(pool.map(domain,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']))
pages=[]
for locale in ['tr','en','ru','ar']:
 corpus=json.loads((release/'private'/('site-documents.'+locale+'.json')).read_bytes());doc=next(x for x in corpus['documents']if x['id']=='membership');snapshot=json.dumps({'version':corpus['version'],'locale':locale,'document':doc},ensure_ascii=False,separators=(',',':')).encode();membership=json.loads(get('nodenohome.com','/api/account/membership-terms?lang='+locale)[0]);assert membership['hash']==hashlib.sha256(snapshot).hexdigest()
 for name in ['kvkk','privacy','cookies','membership','data-request','wholesale','pre-information','sales','returns','seller']:
  html,headers=get('nodenohome.com','/legal/'+name+'?lang='+locale);assert ('lang="'+locale+'"').encode()in html and b'2026-11-10.3'in html
 html,headers=get('nodenohome.com','/legal/kvkk?lang='+locale+'&download=1');assert 'attachment'in headers.get('Content-Disposition','')and b'<style>'in html and b'<script'not in html
 pages.append({'locale':locale,'documentsChecked':10,'downloadSelfContained':True,'membershipHashMatches':True})
record={'passed':True,'checkedAt':datetime.now(timezone.utc).isoformat(),'releaseHash':proof['releaseHash'],'domains':domains,'documentChecks':pages,'realCharges':0,'productionOrdersCreated':0,'productionUsersCreated':0};(E/'live-acceptance.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'passed':True,'domains':len(domains),'documents':40,'realCharges':0,'releaseHash':proof['releaseHash']}))
