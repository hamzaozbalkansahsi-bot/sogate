"""Private TCMB cache producer for hosts whose PHP TLS client cannot reach TCMB.

Uses Python's verified TLS client; no dependencies, web route or third party feed.
The cache format and exact weekly selection match exchange-rates.php.
"""
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal
from pathlib import Path
import argparse,hashlib,json,os,re,secrets,ssl,urllib.request,urllib.error
import xml.etree.ElementTree as ET

IST=ZoneInfo('Europe/Istanbul')
POLICY='week_to_date_highest_forex_selling'
def url(day):return 'https://www.tcmb.gov.tr/kurlar/'+day.strftime('%Y%m/%d%m%Y')+'.xml'
def parse(body,day):
 if len(body)>150000 or b'\x00'in body or re.search(br'<!DOCTYPE|<!ENTITY',body,re.I):raise ValueError('fx_source_invalid')
 root=ET.fromstring(body)
 if root.tag!='Tarih_Date' or root.attrib.get('Tarih')!=day.strftime('%d.%m.%Y'):raise ValueError('fx_source_date_invalid')
 rates={}
 for row in root.findall('Currency'):
  amount=(row.findtext('ForexSelling')or'').strip()
  if not amount:continue
  code=row.attrib.get('CurrencyCode','');unit=row.findtext('Unit')or''
  if not re.fullmatch(r'[A-Z]{3}',code)or code in rates or not re.fullmatch(r'\d{1,7}(?:\.\d{1,6})?',amount)or not re.fullmatch(r'[1-9]\d{0,3}',unit):raise ValueError('fx_source_rate_invalid')
  micros=int(Decimal(amount)*1000000)
  if micros<=0:raise ValueError('fx_source_rate_invalid')
  rates[code]={'rateMicros':micros,'unit':int(unit),'date':day.isoformat()}
 if not {'USD','EUR'}<=rates.keys():raise ValueError('fx_source_incomplete')
 return {'date':day.isoformat(),'rates':rates,'sha256':hashlib.sha256(body).hexdigest()}

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('fx_redirect_rejected')

def fetch(day):
 context=ssl.create_default_context();context.minimum_version=ssl.TLSVersion.TLSv1_2
 opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=context),NoRedirect())
 request=urllib.request.Request(url(day),headers={'User-Agent':'NODENO-FX/1.0','Accept':'application/xml'})
 # TCMB's verified TLS handshake can exceed eight seconds on this host.
 # Retry bounded transport/temporary HTTP failures, without accepting another
 # host, an unverified certificate, a stale cache or an unpublished bulletin.
 for attempt in range(3):
  try:
   with opener.open(request,timeout=20)as response:
    if response.status!=200 or response.geturl()!=url(day):raise ValueError('fx_source_unavailable')
    return parse(response.read(150001),day)
  except urllib.error.HTTPError as error:
   if error.code==404:return None
   if error.code!=429 and error.code<500:raise ValueError('fx_source_unavailable')from None
  except (urllib.error.URLError,TimeoutError,OSError):pass
  if attempt==2:raise ValueError('fx_source_unavailable')from None

def build(now,fetcher=fetch):
 now=now.astimezone(IST);today=now.date();week=today-timedelta(days=today.weekday());days=[];day=week
 while day<=today:
  if day.weekday()<5:
   bulletin=fetcher(day)
   if bulletin:days.append(bulletin)
  day+=timedelta(days=1)
 carry=not days
 if carry:
  for back in range(1,11):
   day=today-timedelta(days=back)
   if day.weekday()>4 or day>=week:continue
   bulletin=fetcher(day)
   if bulletin:days.append(bulletin);break
 if not days:raise ValueError('fx_source_unavailable')
 rates={};sources=[]
 for bulletin in days:
  sources.append({'date':bulletin['date'],'url':url(datetime.strptime(bulletin['date'],'%Y-%m-%d').date()),'sha256':bulletin['sha256']})
  for code,rate in bulletin['rates'].items():
   old=rates.get(code)
   if old is None or rate['rateMicros']*old['unit']>old['rateMicros']*rate['unit']:rates[code]=rate
 data={'schema':1,'base':'TRY','policy':POLICY,'timezone':'Europe/Istanbul','weekStart':week.isoformat(),'asOf':today.isoformat(),'carriedForward':carry,'rates':dict(sorted(rates.items())),'sources':sources}
 data['revision']=hashlib.sha256(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();data['verifiedAt']=int(now.timestamp());data['validUntil']=int(now.timestamp())+1800
 return data

def atomic(root,name,data):
 target=root/name
 if target.is_symlink():raise ValueError('fx_storage_invalid')
 temporary=root/(name+'.'+secrets.token_hex(8));fd=os.open(str(temporary),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:
  with os.fdopen(fd,'w',encoding='utf8')as stream:json.dump(data,stream,separators=(',',':'));stream.flush();os.fsync(stream.fileno())
  os.replace(str(temporary),str(target))
 finally:
  if temporary.exists():temporary.unlink()

def main():
 import fcntl
 parser=argparse.ArgumentParser();parser.add_argument('--storage',required=True);parser.add_argument('--refresh-seconds',type=int,default=300);parser.add_argument('--force',action='store_true');args=parser.parse_args()
 if not 60<=args.refresh_seconds<=900:raise ValueError('fx_refresh_invalid')
 requested=Path(args.storage)
 if requested.is_symlink():raise ValueError('fx_storage_invalid')
 root=requested.resolve(strict=True)
 if not root.is_dir():raise ValueError('fx_storage_invalid')
 os.umask(0o077);lock=root/'exchange-rates.lock'
 if lock.is_symlink():raise ValueError('fx_storage_invalid')
 with lock.open('a')as handle:
  os.chmod(str(lock),0o600)
  try:fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return
  now=datetime.now(IST);old=None;cache=root/'exchange-rates-v1.json'
  if cache.is_symlink():raise ValueError('fx_storage_invalid')
  if cache.exists():
   try:old=json.loads(cache.read_text(encoding='utf8'))
   except (ValueError,OSError):pass
  week=(now.date()-timedelta(days=now.weekday())).isoformat()
  published_today=isinstance(old,dict)and any(s.get('date')==now.date().isoformat()for s in old.get('sources',[]))
  publication_due=now.weekday()<5 and (now.hour,now.minute)>=(15,30)and not published_today
  if not args.force and not publication_due and isinstance(old,dict)and old.get('weekStart')==week and old.get('asOf')==now.date().isoformat()and 0<=int(now.timestamp())-old.get('verifiedAt',0)<args.refresh_seconds and old.get('validUntil',0)>int(now.timestamp()):return
  try:
   snapshot=build(now);atomic(root,'exchange-rates-v1.json',snapshot);atomic(root,'exchange-rates-refresh-status.json',{'status':'ok','verifiedAt':snapshot['verifiedAt'],'revision':snapshot['revision'],'weekStart':snapshot['weekStart'],'sourceDates':[s['date']for s in snapshot['sources']]})
  except Exception as error:
   atomic(root,'exchange-rates-refresh-status.json',{'status':'error','attemptAt':int(now.timestamp()),'code':type(error).__name__});raise

if __name__=='__main__':main()
