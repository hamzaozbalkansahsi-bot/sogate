#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_marketplaces.py
# Açıklama   : İzinli kamu sayfalarını kod çalıştırmadan okur; asıl kod, varyant ve indirimsiz fiyat kanıtını korur.
import hashlib,html,json,re,time,unicodedata
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from urllib.parse import urlsplit,urljoin
import requests
from bs4 import BeautifulSoup

AGENT='SEXOGATE-Catalog-Research/1.0 (+https://sexogate.com)'
HOSTS={'www.trendyol.com','apigw.trendyol.com','cdn.dsmcdn.com','www.hepsiburada.com','productimages.hepsiburada.net'}
def safe_url(url,hosts=HOSTS):
 p=urlsplit(url)
 if p.scheme!='https'or p.hostname not in hosts or p.username or p.password or p.port not in [None,443]:raise ValueError('SOURCE_URL_REJECTED')
 return url
def fetch(url,limit=5000000):
 safe_url(url)
 for attempt in range(3):
  try:
   with requests.get(url,headers={'User-Agent':AGENT,'Accept':'text/html,application/json'},timeout=(12,35),stream=True,allow_redirects=False)as response:
    if response.status_code in [401,403,429]:raise PermissionError('SOURCE_ACCESS_'+str(response.status_code))
    if response.is_redirect:raise ValueError('SOURCE_REDIRECT_REVIEW_REQUIRED')
    response.raise_for_status();data=bytearray()
    for part in response.iter_content(65536):
     data.extend(part)
     if len(data)>limit:raise ValueError('SOURCE_BODY_TOO_LARGE')
    return bytes(data)
  except (requests.ConnectionError,requests.Timeout):
   if attempt==2:raise
   time.sleep(attempt+1)
 raise RuntimeError('SOURCE_REQUEST_FAILED')
def props(document,name):
 soup=BeautifulSoup(document,'html.parser');prefix='window['+json.dumps(name)+']'
 for tag in soup.find_all('script'):
  content=tag.string or tag.get_text()
  if content.strip().startswith(prefix+'='):
   value=json.JSONDecoder().raw_decode(content.split('=',1)[1])[0]
   if not isinstance(value,dict):raise ValueError('SOURCE_JSON_SHAPE')
   return value
 raise ValueError('SOURCE_PUBLIC_DATA_UNAVAILABLE')
def minor(value):
 try:
  if isinstance(value,bool):return None
  n=Decimal(str(value));amount=int((n*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
  return amount if n.is_finite()and 0<amount<=10000000000 else None
 except (InvalidOperation,ValueError,OverflowError,TypeError):return None
def markup_15(amount):return (amount*115+50)//100 if type(amount)is int and 0<amount<=10000000000 else None
def plain(value):
 text=str(value or '')
 if '<'not in text and '>'not in text:return re.sub(r'\s+',' ',html.unescape(text)).strip()
 soup=BeautifulSoup(str(value or ''),'html.parser')
 for tag in soup.select('script,style,iframe,object'):tag.decompose()
 return re.sub(r'\s+',' ',soup.get_text(' ',strip=True)).strip()
def adult_item(p):
 title=' '.join([str(p.get('name','')),str((p.get('category')or{}).get('name',''))]);title=unicodedata.normalize('NFKD',title.casefold().replace('ı','i'));title=''.join(x for x in title if not unicodedata.combining(x))
 if re.search(r'\b(cocuk|bebek|kids|child|baby|teen|ergen)\b',title):return False
 return bool(p.get('isSexualContent'))or bool(re.search(r'\b(fantezi|fantazi|erotik|seksi|cinsel|vibrator|vibrasyon|masturbator|anal|jartiyer|kamasutra|gecelik|kondom|prezervatif|kayganlastirici)\b',title))
def marketplace_group(title,categories):
 text=unicodedata.normalize('NFKD',title.casefold().replace('ı','i'));text=''.join(c for c in text if not unicodedata.combining(c))
 ids={str(c.get('id'))for c in categories}
 if '3098'in ids:return 'accessories'
 if ids.intersection({'3096','3097'})or re.search(r'\b(?:boxer|bustiyer|jockstrap|gecelik|jartiyer|sutyen|kulot|corap|kostum)\w*',text):return 'lingerie'
 if re.search(r'\b(?:zar|kamasutra|kart|tombala)\w*|denge oyunu',text):return 'couples'
 if re.search(r'\bhediye seti\b|\bhediye kutusu\b',text):return 'gifts'
 if ids.intersection({'5234','5235','5092','5094','5095','5097','5242','5243'}):return 'couples'if re.search(r'uzaktan kumanda|telefon kontrol|partnerli',text)else'toys'
 if re.search(r'\b(?:maske|kelepce|kirbac|baglama|kiskac|kafes|harness|kayis)\w*',text):return 'accessories'
 if re.search(r'\b(?:kayganlastirici|temizleyici|bakim|krem|kondom|prezervatif|sprey)\w*|masaj (?:yagi|jeli)',text):return 'care'
 return 'toys'

def marketplace_claim_review(title):
 text=unicodedata.normalize('NFKD',title.casefold().replace('ı','i'));text=''.join(c for c in text if not unicodedata.combining(c))
 return bool(re.search(r'\b(?:medikal|tedavi|ilac|hap|tablet|kapsul|viagra|cialis|sertles|buyut|kalinlastir|dikles|geciktir|ereksiyon|afrodizyak)\w*|\bsu gecirmez\b|erken (?:bosalma|onleyici)|iliskiyi uzat|sure(?:yi)? uzat',text))

def search_page(document):
 data=props(document,'__single-search-result__PROPS')['data'];products=data.get('products')
 if not isinstance(products,list):raise ValueError('SOURCE_PRODUCTS_MISSING')
 selected=[]
 for p in products:
  if not adult_item(p):continue
  safe_url('https://www.trendyol.com'+p['url'],{'www.trendyol.com'});selected.append({'id':str(p['id']),'url':'https://www.trendyol.com'+p['url'],'title':p['name'],'category':p.get('category',{}),'priceEvidence':{k:v for k,v in (p.get('price')or{}).items()if k in ['current','originalPrice','discountedPrice','currency']}})
 return {'products':selected,'rawIds':[str(p['id'])for p in products],'reportedTotal':data.get('total'),'roughTotal':data.get('roughTotal'),'page':data.get('pageIndex')}
def detail_page(document,url):
 safe_url(url,{'www.trendyol.com'});shared=props(document,'__envoy__SHARED_PROPS')['product'];soup=BeautifulSoup(document,'html.parser');ld={}
 for tag in soup.select('script[type="application/ld+json"]'):
  try:
   candidate=json.loads(tag.get_text())
   if isinstance(candidate,dict)and candidate.get('@type')in ['Product','ProductGroup']:ld=candidate;break
  except json.JSONDecodeError:continue
 variant=(shared.get('merchantListing')or{}).get('winnerVariant')or{};price=variant.get('price')or{};base=minor((price.get('sellingPrice')or{}).get('value'));currency=price.get('currency')
 if currency!='TRY':base=None
 code=str(shared.get('productCode')or ld.get('sku')or'').strip();code=code if re.fullmatch(r'[^\x00-\x1f\x7f<>]{1,120}',code)else None
 images=[safe_url(v,{'cdn.dsmcdn.com'})for v in shared.get('images',[])if isinstance(v,str)][:20]
 attributes=[{'name':plain(v.get('key',{}).get('name')),'value':plain(v.get('value',{}).get('name'))}for v in shared.get('attributes',[])if isinstance(v,dict)]
 variants=[]
 for v in shared.get('variants',[]):
  if not isinstance(v,dict):continue
  variants.append({'sourceVariantId':str(v.get('itemNumber')or''),'size':plain(v.get('value')),'barcode':v.get('barcode'),'sourceInStock':v.get('inStock')is True,'observedPriceMinor':minor((v.get('price')or{}).get('value'))})
 missing=[k for k,valid in {'sourceCode':code,'undiscountedPrice':base,'description':plain(ld.get('description')),'images':images,'variants':variants}.items()if not valid]
 return {'platform':'trendyol','sourceId':str(shared['id']),'sourceUrl':url,'sourceCode':code,'sku':'seo-'+code if code else None,'title':plain(shared['name']),'brand':plain((shared.get('brand')or{}).get('name')),'category':shared.get('category',{}),'categoryTree':[{'id':v.get('id'),'name':v.get('name')}for v in shared.get('categoryTree',[])if isinstance(v,dict)],'sourceDescription':plain(ld.get('description')),'attributes':attributes,'variants':variants,'sourceImages':images,'currency':currency,'undiscountedPriceMinor':base,'salePriceMinor':markup_15(base),'priceBasis':'merchantListing.winnerVariant.price.sellingPrice.value','priceEvidence':{k:price.get(k)for k in ['sellingPrice','originalPrice','discountedPrice']},'publicInStock':shared.get('inStock')is True,'stockKnown':False,'stockQuantity':None,'observedAt':int(time.time()),'sourceSha256':hashlib.sha256(document if isinstance(document,bytes)else document.encode()).hexdigest(),'missingFields':missing,'imageReview':'pending','rightsBasis':'16 Kasım 2026 kullanıcı izin beyanı; sözleşme/hesap sahipliği iddia edilmez'}
