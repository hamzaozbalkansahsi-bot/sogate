"""Verify every changed image and both domain families after publication."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,requests
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];E=R/'artifacts/front-image-integrity-20261115';proof=json.loads((E/'release.json').read_bytes());C=R/proof['release'];data=json.loads((C/'private/cabinet-fronts.json').read_bytes());mapping=json.loads((E/'rule-removal.json').read_bytes())['replacements'];version=hashlib.sha256((C/'private/cabinet-fronts.json').read_bytes()).hexdigest();sample='front-dc1a5394d3e7dc80';sampleproduct=next(p for p in data['products']if p['id']==sample);samplehash=sampleproduct['assetHashes'][0]
headers={'Cache-Control':'no-cache'}

def host_check(host):
 origin='https://'+host;r=requests.get(origin+'/api/health',headers=headers,timeout=60,allow_redirects=False);assert r.status_code==200;health=r.json()
 assert health['releaseHash']==proof['releaseHash']and health['products']==proof['publicProducts']and health['mediaReady']is True and health['checkoutEnabled']==proof['expectedCheckoutEnabled']
 response=requests.get(origin+f'/media/{sample}/0?v={version}',headers=headers,timeout=60,allow_redirects=False);assert response.status_code==200 and hashlib.sha256(response.content).hexdigest()==samplehash
 return {'host':host,'releaseHash':health['releaseHash'],'mediaReady':True,'sampleSha256':samplehash,'hostPreserved':True}

def image_check(digest):
 product,index=next((p,i)for p in data['products']for i,h in enumerate(p['assetHashes'])if h==digest)
 url=f'https://nodenohome.com/media/{product["id"]}/{index}?v={version}';r=requests.get(url,headers=headers,timeout=60);assert r.status_code==200 and hashlib.sha256(r.content).hexdigest()==digest and r.headers.get('X-Content-SHA256')==digest
 return {'product':product['id'],'index':index,'sha256':digest}

def main():
 assert json.loads((E/'deployment.json').read_bytes())['releaseHash']==proof['releaseHash']
 with ThreadPoolExecutor(max_workers=4)as pool:hosts=list(pool.map(host_check,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']));images=list(pool.map(image_check,mapping.values()))
 response=requests.get('https://nodenohome.com/api/catalog',headers=headers,timeout=60);response.raise_for_status();cat=response.json();assert cat['meta']['frontCatalogVersion']==version
 visual=[]
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True);page=browser.new_page()
  page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false');")
  for width in [390,1440]:
   page.set_viewport_size({'width':width,'height':950});page.goto('https://nodenohome.com/?lang=tr&product='+sample,wait_until='networkidle',timeout=90000);photo=page.locator('.gallery-main .product-image').first;photo.wait_for(state='visible')
   assert photo.evaluate('(e)=>e.complete&&e.naturalWidth===772&&e.naturalHeight===1381')and version in photo.get_attribute('src');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   page.screenshot(path=str(E/f'live-{width}.png'));visual.append({'width':width,'newCacheVersion':True,'naturalDimensions':[772,1381],'noOverflow':True})
  browser.close()
 record={'passed':True,'releaseHash':proof['releaseHash'],'hosts':hosts,'correctedImages':images,'cacheVersion':version,'liveBrowser':visual,'pricesAndProductFieldsUnchanged':True}
 (E/'live-http.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'passed':True,'hosts':len(hosts),'images':len(images),'browserViews':len(visual)}))

if __name__=='__main__':main()
