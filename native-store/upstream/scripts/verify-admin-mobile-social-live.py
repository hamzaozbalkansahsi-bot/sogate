"""Read-only public acceptance and private worker heartbeat verification."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse,importlib.util,json,time
import requests
R=Path(__file__).resolve().parents[1];E=R/'artifacts/admin-mobile-social-20261112'

def main():
 p=argparse.ArgumentParser();p.add_argument('--heartbeat',action='store_true');args=p.parse_args()
 spec=importlib.util.spec_from_file_location('social_live_backend',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
 proof=json.loads((E/'deployment.json').read_bytes());expected=proof['releaseHash'];b=d.CpanelBackend(allow_writes=False)
 if args.heartbeat:
  receipt=json.loads(d.text_content(b,d.HOME+'/nodeno-social','heartbeat.json'))
  assert receipt.get('releaseHash')==expected and receipt.get('paidEnabled')is False and receipt.get('paidReservations')==0,'worker_receipt_invalid'
  assert receipt.get('heartbeat',{}).get('status')=='ok' and receipt['heartbeat'].get('finishedAt',0)>time.time()-300,'worker_not_recent_and_complete'
  assert receipt.get('result',{}).get('published')==0,'unexpected_publication'
  record={'passed':True,'releaseHash':expected,'serverHeartbeat':receipt,'localComputerRequired':False};(E/'heartbeat-live.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));return
 def health(host):
  r=requests.get('https://'+host+'/api/health',timeout=40);r.raise_for_status();h=r.json();assert h['releaseHash']==expected and h['mediaReady']and h['checkoutEnabled']and h['products']==3602
  assert requests.utils.urlparse(r.url).hostname==host
  return {'host':host,'status':r.status_code,'releaseHash':h['releaseHash'],'products':h['products'],'checkoutEnabled':h['checkoutEnabled'],'mediaReady':h['mediaReady']}
 with ThreadPoolExecutor(max_workers=4)as pool:hosts=list(pool.map(health,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']))
 checks={}
 for path,statuses in [('/api/admin/social/overview',[401]),('/social-media/'+'0'*64+'.png',[404]),('/nodeno-runtime.php',[403,404]),('/.env.local',[403,404])]:
  r=requests.get('https://nodenohome.com'+path,timeout=40);assert r.status_code in statuses,'public_boundary_failed';checks[path]=r.status_code
 record={'passed':True,'releaseHash':expected,'domains':hosts,'unauthenticatedBoundaries':checks,'ordersCreated':0,'chargesCreated':0};(E/'live-acceptance.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
