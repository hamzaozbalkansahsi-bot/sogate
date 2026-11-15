#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native-catalog-assets.py
# Açıklama   : İzin beyanlı kaynak fotoğraflarını değiştirmeden, güvenli ve içerik adresli özel önbelleğe alır.
import concurrent.futures,hashlib,importlib.util,io,json,os,re,threading,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('source_catalog',ROOT/'scripts/source-catalog.py');source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
HOME=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-catalog-20261115');HOME.mkdir(exist_ok=True)
ASSETS=HOME/'media';ASSETS.mkdir(exist_ok=True);REPORT=HOME/'images.json';ALLOWED={'www.xshopum.com','www.liona.com.tr','cdn.myikas.com'}
locks={host:threading.Semaphore(2)for host in ALLOWED};write_lock=threading.Lock()
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  validate(newurl)
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def validate(url):
 parsed=urllib.parse.urlsplit(url)
 if parsed.scheme!='https'or parsed.hostname not in ALLOWED or parsed.username or parsed.password or parsed.port not in [None,443]or any(ord(c)<32 for c in url):raise ValueError('IMAGE_URL_REJECTED')
 return parsed.hostname
def download(url):
 host=validate(url);failure=None
 for attempt in range(3):
  try:
   with locks[host]:
    request=urllib.request.Request(url,headers={'User-Agent':'SEXOGATE-Catalog-Review/1.0','Accept':'image/avif,image/webp,image/png,image/jpeg'})
    with urllib.request.build_opener(source.PinnedHandler(),Redirect()).open(request,timeout=30)as response:
     if int(response.headers.get('Content-Length','0'))>12000000:raise ValueError('IMAGE_TOO_LARGE')
     raw=response.read(12000001)
    time.sleep(.08)
   if not raw or len(raw)>12000000:raise ValueError('IMAGE_SIZE_INVALID')
   with Image.open(io.BytesIO(raw))as image:
    fmt=image.format;w,h=image.size
    if fmt not in ['JPEG','PNG','WEBP']or w<32 or h<32 or w*h>40000000:raise ValueError('IMAGE_FORMAT_OR_DIMENSIONS_INVALID')
    image.verify()
   ext={'JPEG':'jpg','PNG':'png','WEBP':'webp'}[fmt];sha=hashlib.sha256(raw).hexdigest();target=ASSETS/(sha+'.'+ext)
   with write_lock:
    if not target.exists():target.write_bytes(raw)
    elif hashlib.sha256(target.read_bytes()).hexdigest()!=sha:raise ValueError('IMAGE_CACHE_CHANGED')
   return url,{'sha256':sha,'file':target.name,'bytes':len(raw),'width':w,'height':h,'mime':'image/'+('jpeg'if ext=='jpg'else ext),'rightsBasis':'user_declaration_2026-11-15','modified':False}
  except urllib.error.HTTPError as error:
   failure='HTTP_'+str(error.code)
   if error.code not in [429,500,502,503,504]:break
  except (OSError,ValueError,TimeoutError)as error:failure=type(error).__name__
  if attempt<2:time.sleep(1+attempt)
 return url,{'error':failure}
def main():
 base=Path('D:/sexogate-local-artifacts-20261114/private-installs');paths=[base/'supplier-api-live-20261115/xshopum/xshopum.ndjson',*[base/'supplier-catalog'/v/(v+'.ndjson')for v in ['liona','sistina']]]
 rows=[json.loads(line)for path in paths for line in path.read_text('utf8').splitlines()];covers=[];gallery=[]
 for row in rows:
  if row['kind']!='product':continue
  images=row.get('images',[])
  if images:covers.append(images[0]);gallery.extend(images[1:])
 urls=list(dict.fromkeys(covers+gallery));results=json.loads(REPORT.read_text('utf8'))if REPORT.exists()else{}
 for url,row in list(results.items()):
  if 'error'in row:del results[url]
  elif not(ASSETS/row['file']).is_file()or hashlib.sha256((ASSETS/row['file']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('IMAGE_CACHE_CHANGED')
 pending=[url for url in urls if url not in results];print(json.dumps({'references':len(urls),'cached':len(results),'pending':len(pending),'originalBytesOnly':True}),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6)as executor:
  for index,(url,row)in enumerate(executor.map(download,pending),1):
   results[url]=row
   if index%50==0 or index==len(pending):
    temporary=REPORT.with_suffix('.tmp');temporary.write_text(json.dumps(results,ensure_ascii=False),encoding='utf8');os.replace(temporary,REPORT)
    print(json.dumps({'completed':len(results),'total':len(urls),'failed':sum('error'in row for row in results.values()),'uniqueFiles':len({row.get('file')for row in results.values()if'file'in row})}),flush=True)
if __name__=='__main__':main()
