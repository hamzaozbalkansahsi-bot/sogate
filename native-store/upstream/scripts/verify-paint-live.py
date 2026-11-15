"""Read-only live acceptance, plus a private timer heartbeat check."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,importlib.util,json,time
import requests
from lxml import html
R=Path(__file__).resolve().parents[1];E=R/'artifacts/bianca-20261112'
def main():
 global E
 a=argparse.ArgumentParser();a.add_argument('--heartbeat',action='store_true');a.add_argument('--evidence-dir',default='artifacts/bianca-20261112',choices=['artifacts/bianca-20261112','artifacts/paint-completion-20261112','artifacts/paint-resolution-20261112','artifacts/paint-alternatives-20261112']);args=a.parse_args();E=R/args.evidence_dir;proof=json.loads((E/'deployment.json').read_bytes());expected=proof['releaseHash'];prepared=json.loads((E/'catalogue-prepared.json').read_bytes())
 if args.heartbeat:
  s=importlib.util.spec_from_file_location('paint_live_backend',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d);b=d.CpanelBackend(allow_writes=False);rows=d.listing(b,d.HOME+'/nodeno-price-watch')
  if 'paint-price-watch-heartbeat.json'not in rows:print(json.dumps({'pending':True,'reason':'waiting_for_first_scheduled_tick'}));return
  h=json.loads(d.text_content(b,d.HOME+'/nodeno-price-watch','paint-price-watch-heartbeat.json'));assert h.get('releaseHash')==expected and h.get('at',0)>time.time()-900 and h.get('status')!='failed';record={'passed':True,'releaseHash':expected,'serverHeartbeat':h,'localComputerRequired':False};(E/'heartbeat-live.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));return
 def health(host):
  r=requests.get('https://'+host+'/api/health',timeout=40);r.raise_for_status();h=r.json();assert h['releaseHash']==expected and h['products']==proof['publicProducts']and h['mediaReady']and h['checkoutEnabled'];assert requests.utils.urlparse(r.url).hostname==host;return {'host':host,'status':r.status_code,'products':h['products'],'releaseHash':h['releaseHash']}
 with ThreadPoolExecutor(4)as pool:domains=list(pool.map(health,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']))
 response=requests.get('https://nodenohome.com/api/catalog',timeout=45);response.raise_for_status();catalog=response.json();byid={p['id']:p for p in catalog['products']};verified=[]
 for p in prepared['products']:
  live=byid[p['id']];assert live['salePriceMinor']==p['salePriceMinor']and live['modelId']==p['modelId']and live['productBrand']==p['productBrand'];assert set(['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'])<=set(live['name']);verified.append(p['id'])
 sample=next((p for p in prepared['products']if p['productBrand']=='Filli Boya'),prepared['products'][0]);r=requests.get('https://nodenohome.com/?lang=tr&product='+sample['id'],timeout=45);tree=html.fromstring(r.content);assert r.status_code==200 and sample['name']['tr']in [''.join(h.itertext())for h in tree.xpath('//h1')]and tree.xpath('//script[@type="application/ld+json"]')
 for p in [prepared['products'][0],sample]:
  r=requests.get('https://nodenohome.com/api/supplier-products/'+p['id'],timeout=30);r.raise_for_status();d=r.json();assert all(d['description'].get(l)for l in ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'])
 for path,row in list(prepared['assets'].items())[:3]:
  r=requests.get('https://nodenohome.com'+path,timeout=30);r.raise_for_status();assert hashlib.sha256(r.content).hexdigest()==row['sha256']
 boundary=requests.get('https://nodenohome.com/api/admin/suppliers/overview',timeout=30);assert boundary.status_code==401
 record={'passed':True,'releaseHash':expected,'domains':domains,'verifiedProductIds':verified,'paintCount':len(verified),'filliCount':sum(p['productBrand']=='Filli Boya'for p in prepared['products']),'rawWoodMatches':sum(p.get('finishState')=='unpainted'and p.get('paintSurface')=='wood'for p in catalog['products']),'nativeDescriptions':True,'mediaHashesVerified':min(3,len(prepared['assets'])),'unauthenticatedAdminStatus':401,'ordersCreated':0,'chargesCreated':0};(E/'live-acceptance.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
if __name__=='__main__':main()
