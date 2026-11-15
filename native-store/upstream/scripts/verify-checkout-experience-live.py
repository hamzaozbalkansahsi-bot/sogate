"""Read-only commerce acceptance. Quotes only; never creates a payment or an order."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,requests,hashlib
R=Path(__file__).resolve().parents[1];E=R/'artifacts/checkout-experience-20261112';proof=json.loads((E/'build.json').read_bytes());before=json.loads((E/'live-before-catalog.json').read_bytes());hosts=['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']
def inspect(host):
 s=requests.Session();url='https://'+host;r=s.get(url+'/api/health',timeout=50);r.raise_for_status();assert r.url.startswith(url+'/');h=r.json();assert h['releaseHash']==proof['releaseHash']and h['mediaReady']and h['checkoutEnabled']and h['products']==len(before['products'])
 status=s.get(url+'/api/payments/status',timeout=40).json();assert status['enabled']is True and status['test']is False;assert status['freight']=={'kind':'included','includedInCharge':True,'feeMinor':0};assert status['seller']['termsVersion'].endswith('-shipping-20261112');return {'host':host,'releaseHash':h['releaseHash'],'hostPreserved':True,'checkoutEnabled':True,'liveModePreserved':True,'domesticShippingIncluded':True}
with ThreadPoolExecutor(max_workers=4)as pool:domains=list(pool.map(inspect,hosts))
url='https://nodenohome.com';s=requests.Session();r=s.get(url+'/api/catalog',timeout=60);r.raise_for_status();catalog=r.json();old={p['id']:p for p in before['products']};assert set(old)=={p['id']for p in catalog['products']};counts={'markedUp':0,'unchanged':0,'unpriced':0}
for p in catalog['products']:
 b=old[p['id']];assert p['domesticFreightIncluded']is True
 for key in ['salePriceMinor','previousPriceMinor']:
  v=b.get(key);expected=(v*120+50)//100 if isinstance(v,int)and v>0 and b.get('productType')in ['door','door-profile','cabinet-front','cabinet-profile']else v;assert p.get(key)==expected,(p['id'],key)
 if p.get('salePriceMinor')is None:counts['unpriced']+=1
 elif p['salePriceMinor']!=b.get('salePriceMinor'):counts['markedUp']+=1
 else:counts['unchanged']+=1
 if b.get('door',{}).get('charges'):
  for k,v in b['door']['charges'].items():
   expected={a:(n*120+50)//100 if isinstance(n,int)and n>0 else n for a,n in v.items()}if isinstance(v,dict)else((v*120+50)//100 if isinstance(v,int)and v>0 else v);assert p['door']['charges'][k]==expected
status=s.get(url+'/api/payments/status',timeout=40).json();headers={'Origin':url,'X-CSRF-Token':status['csrfToken']};quotes=[]
def quote(item,country='TR'):
 r=s.post(url+'/api/payments/quote',json={'items':[item],'country':country},headers=headers,timeout=40);return r
for kind,quantity in [('furniture',2),('door',5),('cabinet-front',5)]:
 p=next(p for p in catalog['products']if p.get('productType','furniture')==kind and isinstance(p.get('salePriceMinor'),int)and 0<p['salePriceMinor']<5_000_000 and not p.get('stockKnown')and(kind!='door'or p.get('door',{}).get('finishGroup')!='veneer'))
 item={'id':p['id'],'quantity':quantity}
 if kind=='cabinet-front':item['options']={'widthMm':1000,'heightMm':1000,'application':'solid'}
 r=quote(item);r.raise_for_status();q=r.json();net=p['salePriceMinor']*quantity;tax=(net*(10 if kind=='furniture'else 20)+50)//100;assert q['netMinor']==net and q['vatMinor']==tax and q['totalMinor']==net+tax;assert q['freight']['feeMinor']==0;quotes.append({'type':kind,'id':p['id'],'netMinor':net,'vatMinor':tax,'totalMinor':q['totalMinor'],'shippingMinor':0})
r=quote({'id':catalog['products'][0]['id'],'quantity':10},'DE');assert r.status_code==422 and r.json()['error']=='payment_country_not_supported'
legal=[]
for lang in ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']:
 r=s.get(url+'/legal/sales',params={'lang':lang},timeout=40);r.raise_for_status();assert 'Content-Disposition'not in r.headers;assert '<html lang="'+lang+'"'in r.text;legal.append(lang)
record={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'domains':domains,'pricesCompared':len(old),'priceChanges':counts,'quoteChecks':quotes,'foreignFreightCustomsQuoteOnly':True,'legalLocales':legal,'ordersCreated':0,'chargesCreated':0};(E/'live-commerce.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
