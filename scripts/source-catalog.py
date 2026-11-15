#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/source-catalog.py
# Açıklama   : Üç tedarikçinin açık kataloglarını hak/stok onayı vermeden inceleme için toplar.
import argparse,gzip,hashlib,html,http.client,ipaddress,json,re,socket,ssl,time,urllib.error,urllib.parse,urllib.request,urllib.robotparser
from http.cookiejar import CookieJar
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
from bs4 import BeautifulSoup

HOSTS={'liona':{'www.liona.com.tr','liona.com.tr'},'sistina':{'sistinaicgiyim.com.tr','www.sistinaicgiyim.com.tr'},'xshopum':{'www.xshopum.com','xshopum.com'}}
BASE={'liona':'https://www.liona.com.tr','sistina':'https://sistinaicgiyim.com.tr','xshopum':'https://www.xshopum.com'}
AGENT='SEXOGATE-Catalog-Review/1.0'
NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9','i':'http://www.google.com/schemas/sitemap-image/1.1'}

def canonical(url,vendor):
    u=urllib.parse.urlsplit(url)
    if u.scheme not in ['http','https'] or u.hostname not in HOSTS[vendor] or u.username or u.password or u.port not in [None,80,443] or any(ord(c)<32 for c in url):raise ValueError('SOURCE_URL_REJECTED')
    if u.port==80 and u.scheme=='https':raise ValueError('SOURCE_PORT_REJECTED')
    path=urllib.parse.quote(u.path or '/',safe="/%:@!$&'()*+,;=-._~")
    query=urllib.parse.quote(u.query,safe="%/?@:!$&'()*+,;=-._~")
    return urllib.parse.urlunsplit(('https',u.hostname,path,query,''))

def xml_root(raw):
    if len(raw)>12000000 or re.search(br'<!\s*(?:DOCTYPE|ENTITY)',raw,re.I):raise ValueError('UNSAFE_XML')
    return ET.fromstring(raw)

def sitemap_rows(raw):
    root=xml_root(raw);out=[]
    for row in root.findall('s:url',NS):
        title=row.findtext('i:image/i:title',None,NS)
        if title:title=re.sub(r'\s+(?:Main )?Image$','',html.unescape(title)).strip()
        out.append({'url':row.findtext('s:loc','',NS),'title':title,'images':[n.text for n in row.findall('i:image/i:loc',NS) if n.text],'sourceLastModified':row.findtext('s:lastmod',None,NS)})
    return out

def nodes(value):
    if isinstance(value,list):
        for v in value:yield from nodes(v)
    elif isinstance(value,dict):
        yield value
        for k,v in value.items():
            if isinstance(v,(dict,list)):yield from nodes(v)

def product_data(raw,url,kind='product'):
    soup=BeautifulSoup(raw,'html.parser')
    if soup.select_one('input[name="age_confirm"]') or soup.title and 'Yaş Doğrulama' in soup.title.get_text():return {'metadataState':'access_required','accessReason':'adult_entry_notice'}
    structured=[]
    for tag in soup.select('script[type="application/ld+json"]'):
        try:structured.extend(nodes(json.loads(tag.string or tag.get_text(),parse_float=Decimal)))
        except (ValueError,TypeError):pass
    product=next((n for n in structured if 'Product' in ([n.get('@type')] if isinstance(n.get('@type'),str) else n.get('@type',[]))),{})
    if kind=='category':product={}
    h1=soup.select_one('h1');title=product.get('name') or (h1.get_text(' ',strip=True) if h1 else None)
    out={'title':html.unescape(title).strip() if isinstance(title,str) else None,'sku':product.get('sku'),'brand':product.get('brand',{}).get('name') if isinstance(product.get('brand'),dict) else product.get('brand'),'description':BeautifulSoup(str(product.get('description','')),'html.parser').get_text(' ',strip=True)[:10000],'supplierQuantity':None,'publicInStock':None,'quotedRetailMinor':None,'quotedCurrency':None,'images':[],'breadcrumbs':[],'metadataState':'parsed' if title else 'indexed'}
    offer=product.get('offers',{});offer=offer[0] if isinstance(offer,list) and offer else offer
    if isinstance(offer,dict):
        currency=offer.get('priceCurrency');price=offer.get('price')
        if currency in ['TRY','EUR','USD','GBP'] and price is not None:
            try:
                minor=Decimal(str(price))*100
                if minor==minor.to_integral_value() and 0<minor<=9000000000000:out.update({'quotedRetailMinor':int(minor),'quotedCurrency':currency})
            except InvalidOperation:pass
        availability=str(offer.get('availability','')).rstrip('/').rsplit('/',1)[-1]
        if availability in ['InStock','OutOfStock']:out['publicInStock']=availability=='InStock'
    images=product.get('image',[]);images=[images] if isinstance(images,(str,dict)) else images
    if isinstance(images,list):
        for image in images:
            image=image.get('url') if isinstance(image,dict) else image
            if isinstance(image,str) and image.startswith(('https://','http://')):out['images'].append(image)
    for n in structured:
        if n.get('@type')=='BreadcrumbList':
            for crumb in n.get('itemListElement',[]):
                item=crumb.get('item');link=item.get('@id') or item.get('url') if isinstance(item,dict) else item;name=crumb.get('name') or (item.get('name') if isinstance(item,dict) else None)
                if isinstance(link,str) and isinstance(name,str):out['breadcrumbs'].append({'url':urllib.parse.urljoin(url,link),'name':name})
    if not out['breadcrumbs']:
        for a in soup.select('.breadcrumb a,.breadcrumbs a,[itemtype$="BreadcrumbList"] a'):
            if a.get('href'):out['breadcrumbs'].append({'url':urllib.parse.urljoin(url,a['href']),'name':a.get_text(' ',strip=True)})
    for field in ['sku','brand']:
        if out[field] is not None:out[field]=str(out[field])[:300]
    return out

class PinnedHTTPS(http.client.HTTPSConnection):
    def connect(self):
        addresses=list(dict.fromkeys(r[4][0] for r in socket.getaddrinfo(self.host,self.port,type=socket.SOCK_STREAM)))
        if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):raise ValueError('PRIVATE_NETWORK_REJECTED')
        sock=socket.create_connection((addresses[0],self.port),self.timeout)
        self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
class PinnedHandler(urllib.request.HTTPSHandler):
    def https_open(self,request):return self.do_open(PinnedHTTPS,request,context=ssl.create_default_context())
class SourceRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self,vendor):self.vendor=vendor
    def redirect_request(self,request,fp,code,msg,headers,newurl):return super().redirect_request(request,fp,code,msg,headers,canonical(newurl,self.vendor))

class Fetcher:
    def __init__(self,vendor,folder):
        self.vendor=vendor;self.folder=folder;folder.mkdir(parents=True,exist_ok=True);self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),PinnedHandler(),SourceRedirect(vendor));self.last=0;self.robot=urllib.robotparser.RobotFileParser();self.robot.parse(self.get(BASE[vendor]+'/robots.txt',robots=False).decode('utf8','replace').splitlines());self.requests=0
        if vendor=='xshopum':
            self.opener=urllib.request.build_opener(SourceRedirect(vendor),urllib.request.HTTPCookieProcessor(CookieJar()))
            base=BASE[vendor];raw=self.get(base+'/',force=True);form=BeautifulSoup(raw,'html.parser').select_one('form[action="/yas-dogrulama-onay"]')
            if form:
                fields={x.get('name'):x.get('value','') for x in form.select('input[name]')};fields['age_confirm']='yes'
                request=urllib.request.Request(base+'/yas-dogrulama-onay',data=urllib.parse.urlencode(fields).encode(),headers={'User-Agent':AGENT,'Origin':base,'Referer':base+'/','Content-Type':'application/x-www-form-urlencoded'})
                with self.opener.open(request,timeout=25) as response:response.read(12000000)
    def get(self,url,robots=True,force=False):
        url=canonical(url,self.vendor)
        if robots and not self.robot.can_fetch(AGENT,url):raise ValueError('ROBOTS_DISALLOWED')
        file=self.folder/(hashlib.sha256(url.encode()).hexdigest()+'.body')
        if file.exists() and not force:return file.read_bytes()
        delay=max(.75,self.robot.crawl_delay(AGENT) or 0) if robots else .75
        time.sleep(max(0,delay-(time.monotonic()-self.last)));self.last=time.monotonic()
        if self.vendor=='xshopum':
            host=urllib.parse.urlsplit(url).hostname;addresses=[r[4][0] for r in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)]
            if any(not ipaddress.ip_address(a).is_global for a in addresses):raise ValueError('PRIVATE_NETWORK_REJECTED')
        request=urllib.request.Request(url,headers={'User-Agent':AGENT})
        with self.opener.open(request,timeout=25) as response:
            raw=response.read(12000001)
            if len(raw)>12000000:raise ValueError('SOURCE_TOO_LARGE')
        file.write_bytes(raw);self.requests=getattr(self,'requests',0)+1;return raw

def api_url(resource,page):
    if resource not in ['products','products/categories'] or not isinstance(page,int) or not 1<=page<=200:raise ValueError('API_REQUEST_REJECTED')
    params={'per_page':100,'page':page,'orderby':'id' if resource=='products' else 'name','order':'asc'}
    if resource=='products':params['stock_status']='instock,outofstock,onbackorder'
    else:params['hide_empty']='false'
    return BASE['xshopum']+'/wp-json/wc/store/v1/'+resource+'?'+urllib.parse.urlencode(params)

def collect(vendor,folder,index_only=False,api_only=False):
    if api_only and (vendor!='xshopum' or index_only):raise ValueError('API_NOT_DOCUMENTED')
    folder.mkdir(parents=True,exist_ok=True);fetch=Fetcher(vendor,folder/'cache');records=[];base=BASE[vendor];sources=[]
    if api_only:maps=[]
    elif vendor=='sistina':maps=[(base+'/products.xml','product'),(base+'/collections.xml','category')]
    else:
        index=xml_root(fetch.get(base+('/sitemap.xml' if vendor=='xshopum' else '/sitemap_index.xml')));maps=[]
        for item in index.findall('s:sitemap/s:loc',NS):
            u=item.text or ''
            if vendor=='liona' and ('product_sitemap' in u or 'category_sitemap' in u):maps.append((u,'category' if 'category_sitemap' in u else 'product'))
            elif vendor=='xshopum' and re.search(r'/product-sitemap\d*\.xml$',u):maps.append((u,'product'))
    for url,kind in maps:
        raw=fetch.get(url);sources.append({'url':url,'sha256':hashlib.sha256(raw).hexdigest()})
        for row in sitemap_rows(raw):
            u=canonical(row['url'],vendor)
            if vendor=='xshopum' and urllib.parse.urlsplit(u).path.rstrip('/')=='/magaza':continue
            records.append({'kind':kind,'sourceUrl':u,'title':row['title'],'images':row['images'],'sourceLastModified':row['sourceLastModified'],'metadataState':'indexed','supplierQuantity':None,'quotedRetailMinor':None,'quotedCurrency':None,'publicInStock':None})
    unique={r['sourceUrl']:r for r in records};api_records={}
    if vendor=='xshopum' and not index_only:
        for resource,kind in [('products','product'),('products/categories','category')]:
            page=1
            while page<=1000:
                endpoint=api_url(resource,page);raw=fetch.get(endpoint);data=json.loads(raw);sources.append({'url':endpoint,'sha256':hashlib.sha256(raw).hexdigest()})
                if not isinstance(data,list):raise ValueError('PUBLIC_API_FORMAT')
                for p in data:
                    url=canonical(p['permalink'],vendor);prices=p.get('prices',{});price=prices.get('price');currency=prices.get('currency_code');minor=int(price) if isinstance(price,str) and price.isdigit() and int(price)>0 and currency in ['TRY','EUR','USD','GBP'] and prices.get('currency_minor_unit')==2 else None
                    row={'kind':kind,'sourceUrl':url,'title':html.unescape(p['name']),'sourceApiId':p['id'],'sourceMethod':'woocommerce-public-store-api','metadataState':'parsed','images':[i['src'] for i in p.get('images',[]) if isinstance(i,dict) and i.get('src')],'supplierQuantity':None,'sku':p.get('sku'),'description':BeautifulSoup(p.get('description',''),'html.parser').get_text(' ',strip=True)[:10000],'quotedRetailMinor':minor,'quotedCurrency':currency if minor is not None else None,'publicInStock':p.get('is_in_stock'),'categories':p.get('categories',[]),'variants':p.get('variations',[]),'attributes':p.get('attributes',[]),'parentSourceId':p.get('parent'),'observedAt':datetime.now(timezone.utc).isoformat()}
                    if kind=='category':row['quotedRetailMinor']=None;row['quotedCurrency']=None
                    unique[url]=row;api_records[url]=True
                print(json.dumps({'vendor':vendor,'publicApi':resource,'page':page,'items':len(data)}),flush=True)
                if len(data)<100:break
                page+=1
    records=list(unique.values());report={'vendor':vendor,'productUrls':sum(r['kind']=='product' for r in records),'categoryUrls':sum(r['kind']=='category' for r in records),'publicApiRecords':len(api_records),'parsed':0,'accessRequired':0,'errors':0,'sources':sources,'complete':False};output=folder/(vendor+'.ndjson');deep_blocked=False
    for n,row in enumerate(records):
        if row['sourceUrl'] in api_records:pass
        elif not index_only and not deep_blocked:
            try:
                raw=fetch.get(row['sourceUrl']);data=product_data(raw,row['sourceUrl'],row['kind']);old_images=row['images'];row.update({k:v for k,v in data.items() if v is not None});row['images']=data.get('images') or old_images;row['sourceHtmlSha256']=hashlib.sha256(raw).hexdigest()
                if row['metadataState']=='access_required':deep_blocked=True
            except urllib.error.HTTPError as e:
                row['metadataState']='access_required' if e.code in [401,403,429] else 'error';row['sourceStatus']=e.code;deep_blocked=e.code in [401,403,429]
            except (ValueError,TimeoutError,OSError) as e:row['metadataState']='error';row['errorType']=type(e).__name__
        elif deep_blocked:row['metadataState']='access_required'
        row['vendor']=vendor;row['observedAt']=datetime.now(timezone.utc).isoformat();row['images']=list(dict.fromkeys(row.get('images',[])))[:30]
        report['parsed']+=row['metadataState']=='parsed';report['accessRequired']+=row['metadataState']=='access_required';report['errors']+=row['metadataState']=='error'
        if (n+1)%20==0:print(json.dumps({'vendor':vendor,'processed':n+1,'total':len(records),'parsed':report['parsed'],'accessRequired':report['accessRequired']}),flush=True)
    output.write_text(''.join(json.dumps(r,ensure_ascii=False,default=str)+'\n' for r in records),encoding='utf8');output.with_suffix('.ndjson.gz').write_bytes(gzip.compress(output.read_bytes(),mtime=0));report.update({'complete':True,'allMetadataParsed':report['parsed']==len(records),'records':len(records),'output':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'finishedAt':datetime.now(timezone.utc).isoformat()});(folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report),flush=True);return report

def run_vendor(vendor,folder,index_only=False,api_only=False):
    try:return collect(vendor,folder,index_only,api_only)
    except (urllib.error.HTTPError,ValueError,OSError) as e:
        folder.mkdir(parents=True,exist_ok=True);report={'vendor':vendor,'complete':False,'errorType':type(e).__name__,'sourceStatus':getattr(e,'code',None)};(folder/'failure.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--vendor',choices=list(HOSTS)+['all'],default='all');parser.add_argument('--output-root',type=Path,required=True);parser.add_argument('--index-only',action='store_true');parser.add_argument('--api-only',action='store_true');args=parser.parse_args();vendors=list(HOSTS) if args.vendor=='all' else [args.vendor]
    with ThreadPoolExecutor(max_workers=len(vendors)) as pool:
        results=list(pool.map(lambda v:run_vendor(v,args.output_root/v,args.index_only,args.api_only),vendors))
    (args.output_root/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
