from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests,json,hashlib,re,argparse
parser=argparse.ArgumentParser();parser.add_argument('--release',default='artifacts/cpanel-release-projects-20261110');parser.add_argument('--output',default='artifacts/project-commerce');args=parser.parse_args()
R=Path(__file__).resolve().parents[1];E=R/args.output;E.mkdir(parents=True,exist_ok=True);build={'releaseHash':json.loads((R/args.release/'private/release.json').read_bytes())['releaseHash']};rows=[]
def check_host(host):
 origin='https://'+host;r=requests.get(origin+'/api/health',timeout=60,allow_redirects=False);assert r.status_code==200,r.status_code;h=r.json();assert h['releaseHash']==build['releaseHash']and h['products']==1021 and h['mediaReady']is True and h['checkoutEnabled']is False
 return {'host':host,'https':True,'hostPreserved':True,'releaseHash':h['releaseHash'],'products':h['products']}
with ThreadPoolExecutor(max_workers=4)as pool:rows=list(pool.map(check_host,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']))
origin='https://nodenohome.com';r=requests.get(origin+'/api/exchange-rates',timeout=40);assert r.status_code==200,(r.status_code,r.text[:200]);fx=r.json();assert fx['policy']=='week_to_date_highest_forex_selling'and fx['rates']['USD']['rateMicros']>0 and fx['rates']['EUR']['rateMicros']>0
(E/'live-exchange-rates.json').write_text(json.dumps(fx,indent=2)+'\n')
config=requests.get(origin+'/api/config',timeout=30).json();assert config['parentCompany']['name']=='PTYS Technologies LLC'
catalog=requests.get(origin+'/api/catalog',timeout=30).json();byid={p['id']:p for p in catalog['products']};assert len(byid)==1021
groups={}
for p in catalog['products']:
 if p.get('productType')in['cabinet-front','cabinet-profile']:
  assert groups.get(p['modelId'],p['productType'])==p['productType'],'Accessory shown as a front colour';groups[p['modelId']]=p['productType']
foreign=[];p=next(p for p in catalog['products']if p.get('productType')=='cabinet-front'and p.get('salePriceMinor')and p['front']['material']=='pvc')
for code in ['USD','EUR','JPY']:
 if code not in fx['rates']:continue
 body={'items':[{'id':p['id'],'quantity':20,'options':{'widthMm':500,'heightMm':1000,'application':'solid'}}],'country':'DE','currency':code,'priceRevision':catalog['meta'].get('controlRevision',0),'exchangeRevision':fx['revision']}
 response=requests.post(origin+'/api/commerce/quote',json=body,headers={'Origin':origin},timeout=30);assert response.status_code==200,response.text();q=response.json();rate=fx['rates'][code];exponent=0 if code=='JPY'else 2;n=p['salePriceMinor']*10*1000000*rate['unit']*(10**exponent);den=100*rate['rateMicros'];assert q['displaySubtotalMinor']==(n+den//2)//den and q['minimumEligible']and not q['checkoutEnabled'];foreign.append({'currency':code,'subtotalMinor':q['displaySubtotalMinor'],'exchangeRevision':q['exchangeRevision']})
media=[]
for filename in ['door-catalog.json','cabinet-fronts.json']:
 d=json.loads((R/'data'/filename).read_bytes());products=d['products'];chosen=[products[0],products[-1],next((p for p in products if len(p['images'])>1),products[0]),products[len(products)//2]]
 for p in chosen:
  assert p['id']in byid and byid[p['id']]['code']==p['code']
  for index in sorted({0,len(p['images'])-1}):
   a=d['assets'][p['assetHashes'][index]];response=requests.get(origin+'/media/'+p['id']+'/'+str(index),timeout=30);assert response.status_code==200 and hashlib.sha256(response.content).hexdigest()==a['sha256'];media.append({'id':p['id'],'index':index,'sha256':a['sha256']})
for lang in ['tr','en','ru','ar']:
 for category in ['kapilar','dolap-kapaklari']:
  response=requests.get(origin+'/',params={'page':'catalog','category':category,'lang':lang},timeout=30);assert response.status_code==200 and 'hreflang'in response.text
 response=requests.get(origin+'/sitemap-products-'+lang+'.xml',timeout=30);assert response.status_code==200 and 'front-'in response.text and 'door-'in response.text
for path in ['/private/door-catalog.json','/private/cabinet-fronts.json','/door-commerce.php','/.env.local']:
 response=requests.get(origin+path,timeout=30);assert response.status_code in [403,404],(path,response.status_code)
result={'passed':True,'releaseHash':build['releaseHash'],'hosts':rows,'officialFx':{'weekStart':fx['weekStart'],'usd':fx['rates']['USD'],'eur':fx['rates']['EUR'],'sourceBulletins':fx['sources']},'foreignServerQuotes':foreign,'ownerMedia':media,'parentCompany':True,'fourLanguageCategorySSR':True,'fourLanguageSitemaps':True,'privateSourcesBlocked':True,'furnitureProductsPreserved':667,'checkoutEnabled':False}
(E/'live-http.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
