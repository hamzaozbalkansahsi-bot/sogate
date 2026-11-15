"""Archive public supplier catalogues; never writes accounts, carts or orders.

Source records and unreviewed media stay private. Resumable caches retain exact
response hashes, timestamps, SKU, sales unit and variant options. No guessed price.
"""
from __future__ import annotations
import argparse, concurrent.futures, gzip, hashlib, html, json, re, threading, time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/supplier-expansion'
HOSTS={'alkaahsap.com','www.altinisagac.com'}
STATE=threading.local()
def now():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def read_archive(file):
    body=Path(file).read_bytes()
    return gzip.decompress(body)if body.startswith(b'\x1f\x8b')else body
def text(v):return BeautifulSoup(html.unescape(str(v or '')),'lxml').get_text(' ',strip=True)
def markup(minor,percent):
    if not isinstance(minor,int) or minor<=0 or percent not in (20,30):raise ValueError('price_invalid')
    return (minor*(100+percent)+50)//100
def money(value,decimal=','):
    raw=re.sub(r'[^0-9,.\-]','',str(value))
    if decimal==',':raw=raw.replace('.','').replace(',','.')
    else:raw=raw.replace(',','')
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?',raw):raise ValueError('price_invalid')
    n=int((Decimal(raw)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    if n<=0:raise ValueError('price_invalid')
    return n
def identity(supplier,sku,url):
    digest=sha(url.encode())[:10];tag={'alka':'ALK','altinis':'ALT'}[supplier]
    stem=re.sub('[^A-Za-z0-9_-]+','-',str(sku)).strip('-')[:65] or digest
    return f'{supplier}-{digest}',f'ND-{tag}-{stem}-{digest[:6].upper()}'
def base(supplier,sku,url,title):
    pid,code=identity(supplier,sku,url)
    return {'id':pid,'code':code,'supplierId':supplier,'sourceCode':sku,'sourceUrl':url,
      'title':text(title),'currency':'TRY','markupPercent':20,'sourcePriceMinor':None,'salePriceMinor':None,
      'priceStatus':'unverified','images':[],'categories':[],'specs':[],'variants':[],
      'publicationReady':False,'reviewRequired':['media','translations','sales_unit'],'fetchedAt':now()}
def parse_alka(row):
    p=base('alka',text(row.get('sku')),row['permalink'],row['name'])
    p['sourcePageId']=str(row['id']);p['description']=text(row.get('description') or row.get('short_description'))
    p['images']=[i['src']for i in row.get('images',[])];p['categories']=[text(c['name'])for c in row.get('categories',[])]
    p['variants']=row.get('variations',[]);p['attributes']=row.get('attributes',[])
    pricehtml=BeautifulSoup(row.get('price_html',''),'lxml');unit=pricehtml.select_one('.wd-price-unit')
    p['salesUnit']=unit.get_text(' ',strip=True)if unit else None
    p['availability']='in_stock'if row.get('is_in_stock')else 'out_of_stock'
    prices=row.get('prices',{});n=prices.get('price','0')
    if n.isdigit()and int(n)>0 and prices.get('currency_code')=='TRY'and prices.get('currency_minor_unit')==2:
        p['sourcePriceMinor']=int(n);p['taxBasis']='public_store_display'
        if row.get('variations')or prices.get('price_range'):p['priceStatus']='variant_selection_required'
        else:p['salePriceMinor']=markup(int(n),20);p['priceStatus']='verified'
    for a in row.get('attributes',[]):p['specs'].append({'label':text(a['name']),'value':', '.join(text(t['name'])for t in a.get('terms',[]))})
    return p
def parse_altinis(body,url):
    s=BeautifulSoup(body,'lxml');heading=s.select_one('h1');sku=None
    for row in s.select('.product-list-row'):
        t=row.get_text(' ',strip=True)
        if t.startswith('Stok Kodu'):sku=t[len('Stok Kodu'):].strip()
    if not heading or not sku:raise ValueError('product_identity_missing')
    p=base('altinis',sku,url,heading.get_text(' ',strip=True))
    structured=s.select_one('[itemscope][style] [itemprop="offers"]')
    if not structured:structured=s.select_one('[itemprop="offers"]')
    price=structured.select_one('[itemprop="price"]')if structured else None
    currency=structured.select_one('[itemprop="priceCurrency"]')if structured else None
    visible=s.select_one('.product-price-new')or s.select_one('.product-price')
    if price and currency and currency.get('content')=='TRY'and visible:
        try:
            n=money(price.get('content',price.get_text()),'.');shown=visible.get_text(' ',strip=True)
            amounts=re.findall(r'\d[\d.]*,\d{2}',shown)
            if n not in [money(v)for v in amounts if not re.fullmatch(r'0[,\.]00',v)]:raise ValueError('visible_price_mismatch')
            p.update(sourcePriceMinor=n,salePriceMinor=markup(n,20),priceStatus='verified',taxBasis='vat_included_public_offer')
        except ValueError as e:p['priceVerificationReason']=str(e)
    detail=s.select_one('.product-detail');p['description']=detail.get_text('\n',strip=True)if detail else ''
    cat=s.select_one('.product-categories');p['categories']=[a.get_text(' ',strip=True)for a in cat.select('a')]if cat else []
    if not p['categories']:
        c=s.select_one('[itemprop="category"]');p['categories']=[c.get('content')or c.get_text(' ',strip=True)]if c else []
    for table in (detail.select('tr')if detail else []):
        cells=table.select('td,th')
        if len(cells)==2:p['specs'].append({'label':cells[0].get_text(' ',strip=True),'value':cells[1].get_text(' ',strip=True)})
    # Only gallery images belonging to this product, never recommendation cards.
    images=[]
    for node in s.select('[data-zoom-image], [itemprop="image"], .thumb-image img, .product-thumb img'):
        src=node.get('data-zoom-image')or node.get('content')or node.get('src')
        if src and '/products/'in src:
            src=urljoin(url,src).replace('_min.','.')
            if src not in images:images.append(src)
    p['images']=images;p['salesUnit']='Adet'
    unit=s.select_one('.product-unit');
    if unit:p['salesUnit']=unit.get_text(' ',strip=True)
    # Public quantity controls are retained for unit review; never infer a metre from a title.
    p['unitEvidence']=[x.get_text(' ',strip=True)for x in s.select('.product-quantity,.product-unit,.product-list-row')][:12]
    p['sourcePageId']=url.rstrip('/').rsplit('-',1)[-1]
    availability=structured.select_one('[itemprop="availability"]')if structured else None
    p['availability']=(availability.get('href','').rsplit('/',1)[-1]if availability else 'unknown')
    return p
def alka_visible_offer(body):
    s=BeautifulSoup(body,'lxml');price=s.select_one('.summary .price,.summary-inner .price,.product-summary .price')
    out={'status':'unverified','sourcePriceMinor':None,'salesUnit':None}
    if not price:return out
    unit=price.select_one('.wd-price-unit');out['salesUnit']=unit.get_text(' ',strip=True)if unit else None
    if price.select_one('.alka-fiyat-sorunuz'):
        out['status']='quote_required';return out
    values=[]
    for node in price.select('ins .woocommerce-Price-amount')or price.select('.woocommerce-Price-amount'):
        if node.find_parent('del'):continue
        try:values.append(money(node.get_text(' ',strip=True),'.'))
        except ValueError:pass
    if len(set(values))==1:out.update(status='verified',sourcePriceMinor=values[0])
    elif values:out.update(status='variant_selection_required',sourcePriceMinor=min(values))
    return out
def session():
    if not hasattr(STATE,'s'):
        STATE.s=requests.Session();STATE.s.headers['User-Agent']='NODENO-SupplierCatalog/1.0 (+https://nodenohome.com)'
    return STATE.s
def fetch(url,folder,extension='html'):
    if urlparse(url).hostname not in HOSTS or urlparse(url).scheme!='https':raise ValueError('untrusted_source')
    folder.mkdir(parents=True,exist_ok=True);key=sha(url.encode());file=folder/(key+'.'+extension);receipt=folder/(key+'.receipt.json')
    if file.exists()and receipt.exists():
        try:
            evidence=json.loads(receipt.read_bytes());cached=read_archive(file)
            if evidence['sha256']==sha(cached):return cached,{**evidence,'cacheHit':True}
        except (ValueError,OSError,EOFError):pass
    response=session().get(url,timeout=(10,45),allow_redirects=True)
    if response.status_code in (403,429):raise RuntimeError('supplier_access_limited')
    response.raise_for_status()
    if urlparse(response.url).hostname not in HOSTS:raise ValueError('untrusted_redirect')
    file.write_bytes(response.content)
    evidence={'url':url,'finalUrl':response.url,'fetchedAt':now(),'sha256':sha(response.content),'file':file.relative_to(ROOT).as_posix(),'status':response.status_code}
    receipt.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8');return response.content,evidence
def download_images(products):
    urls=sorted({u for p in products for u in p['images']});assets={};errors=[]
    def one(url):
        try:
            data,e=fetch(url,OUT/'media','bin')
            from PIL import Image
            import io
            image=Image.open(io.BytesIO(data));image.verify()
            return url,{**e,'width':image.width,'height':image.height},None
        except Exception as ex:return url,None,type(ex).__name__
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for i,(url,asset,error)in enumerate(pool.map(one,urls),1):
            if asset:assets[url]=asset
            else:errors.append({'url':url,'error':error})
            if i%100==0:print(json.dumps({'mediaDownloaded':i,'total':len(urls)}),flush=True)
    return assets,errors
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--supplier',choices=['alka','altinis','all'],default='all');parser.add_argument('--limit',type=int);parser.add_argument('--images',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);products=[];errors=[];expected={}
    if args.supplier in ('alka','all'):
        for page in range(1,20):
            url=f'https://alkaahsap.com/wp-json/wc/store/v1/products?per_page=100&page={page}'
            body,evidence=fetch(url,OUT/'alka-api','json');rows=json.loads(body)
            if not isinstance(rows,list):raise ValueError('invalid_store_response')
            for row in rows:
                p=parse_alka(row);p['evidence']=evidence;products.append(p)
            print(json.dumps({'supplier':'alka','page':page,'products':len(products)}),flush=True)
            if len(rows)<100:break
            time.sleep(.5)
        expected['alka']=len(products)
    if args.supplier in ('altinis','all'):
        urls=sorted(set(json.loads((OUT/'altinis-urls.json').read_bytes())));expected['altinis']=len(urls)
        if args.limit:urls=urls[:args.limit]
        def one(url):
            try:
                body,e=fetch(url,OUT/'altinis-pages');p=parse_altinis(body,url);p['evidence']=e
                if not e.get('cacheHit'):time.sleep(.8)
                return p,None
            except Exception as ex:return None,{'url':url,'reason':str(ex)[:120]}
        # Small, bounded public reads; no login, cart or security challenge bypass.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
            for i,(p,error)in enumerate(pool.map(one,urls),1):
                if p:products.append(p)
                else:errors.append(error)
                if i%25==0:
                    (OUT/'progress.json').write_text(json.dumps({'processed':i,'total':len(urls),'errors':len(errors),'at':now()}),encoding='utf8')
                    print(json.dumps({'supplier':'altinis','processed':i,'total':len(urls),'errors':len(errors)}),flush=True)
    assets,mediaErrors=download_images(products)if args.images else ({},[])
    ids=[p['id']for p in products];codes=[p['code']for p in products]
    if len(ids)!=len(set(ids))or len(codes)!=len(set(codes)):raise ValueError('product_collision')
    result={'schema':1,'generatedAt':now(),'publicationReady':False,'products':products,'assets':assets,'errors':errors,'mediaErrors':mediaErrors,'expected':expected,'counts':dict(Counter(p['supplierId']for p in products)),'priceCounts':dict(Counter(p['priceStatus']for p in products))}
    file=OUT/(args.supplier+'-catalog.json');file.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'output':str(file),'counts':result['counts'],'prices':result['priceCounts'],'errors':len(errors),'mediaErrors':len(mediaErrors)}),flush=True)
if __name__=='__main__':main()
