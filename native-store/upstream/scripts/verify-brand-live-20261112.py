"""Read-only acceptance of revised identity across all four production hosts."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,importlib.util,json,time
import requests
R=Path(__file__).resolve().parents[1];E=R/'artifacts/brand-refresh-20261112'

def main():
    proof=json.loads((E/'release.json').read_bytes());C=R/proof['release'];expected=proof['releaseHash']
    paths=[n[7:]for n in proof['changedFiles']if n.startswith('public/')]
    def verify(host):
        origin='https://'+host;s=requests.Session();h=s.get(origin+'/api/health',timeout=45);h.raise_for_status();data=h.json()
        assert data['releaseHash']==expected and data['products']==3602 and data['mediaReady']is True and data['checkoutEnabled']is True
        for path in paths:
            response=s.get(origin+'/'+path+'?v=brand-20261112-v2',timeout=45);assert response.status_code==200,path
            assert hashlib.sha256(response.content).digest()==hashlib.sha256((C/'public'/path).read_bytes()).digest(),path
        home=s.get(origin+'/?lang=tr',timeout=45);assert home.status_code==200 and '/assets/brand/logo-horizontal.svg?v=brand-20261112-v2' in home.text
        legal=s.get(origin+'/legal?lang=tr',timeout=45);assert legal.status_code==200 and '/assets/brand/logo-horizontal.svg?v=brand-20261112-v2' in legal.text
        return {'host':host,'status':200,'releaseHash':expected,'assetsVerified':len(paths),'products':data['products'],'checkoutPreserved':True,'headerAndLegalVersioned':True}
    with ThreadPoolExecutor(max_workers=4)as pool:domains=list(pool.map(verify,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']))
    boundaries={}
    for path,statuses in [('/api/admin/social/overview',[401]),('/.env.local',[403,404]),('/nodeno-runtime.php',[403,404])]:
        response=requests.get('https://nodenohome.com'+path,timeout=35);assert response.status_code in statuses;boundaries[path]=response.status_code
    s=importlib.util.spec_from_file_location('brand_live_backend',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d);b=d.CpanelBackend(allow_writes=False)
    heartbeat=json.loads(d.text_content(b,d.HOME+'/nodeno-social','heartbeat.json'))
    assert heartbeat.get('releaseHash')==expected and heartbeat.get('paidEnabled')is False
    assert heartbeat.get('heartbeat',{}).get('status')=='ok' and heartbeat['heartbeat']['finishedAt']>time.time()-300
    assert heartbeat.get('creativeVersion')=='home-living-reference-20261112-v4'and set(heartbeat.get('activeAutomaticSegments',{}))=={'finished'}
    record={'passed':True,'releaseHash':expected,'domains':domains,'unauthenticatedBoundaries':boundaries,'workerVersion':heartbeat['creativeVersion'],'paidEnabled':False,'socialProfilesUploaded':False,'liveVerification':'HTTPS response and SHA256 readback; desktop/mobile visual checks recorded separately in browser-local.json'}
    (E/'live-acceptance.json').write_text(json.dumps(record,indent=2)+'\n');(E/'heartbeat-live.json').write_text(json.dumps(heartbeat,indent=2)+'\n');print(json.dumps(record))

if __name__=='__main__':main()
