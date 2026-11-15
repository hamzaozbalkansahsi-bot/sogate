"""Read-only final HTTP acceptance. No customer/admin authentication or mutation."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.error,urllib.parse,xml.etree.ElementTree as ET,concurrent.futures,datetime,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/blog-20261112'

def fetch(url):
 request=urllib.request.Request(url,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity'})
 try:
  with urllib.request.urlopen(request,timeout=40)as response:return response.status,response.read(20000001),response.url
 except urllib.error.HTTPError as error:return error.code,error.read(20000001),error.url

def main():
 proof=json.loads((E/'release.json').read_bytes());candidate=R/proof['release'];origin='https://nodenohome.com';status,body,_=fetch(origin+'/api/health');health=json.loads(body)
 assert status==200 and health['releaseHash']==proof['releaseHash']and health['mediaReady']and health['blogMediaReady']and health['products']==proof['publicProducts']and health['checkoutEnabled']==proof['expectedCheckoutEnabled'];assert health['blogPublished']==2
 checked=[]
 for name in proof['changedFiles']:
  if not name.startswith('public/')or name in['public/index.php','public/.htaccess','public/admin.html']:continue
  status,body,_=fetch(origin+'/'+name[7:]);expected=(candidate/name).read_bytes();assert status==200 and body==expected,name;checked.append({'file':name,'sha256':hashlib.sha256(body).hexdigest()})
 status,body,_=fetch(origin+'/sitemap.xml');assert status==200 and b'/sitemap-blog.xml'in body
 status,body,_=fetch(origin+'/sitemap-blog.xml');assert status==200;root=ET.fromstring(body);urls=[x.text for x in root.findall('{*}url/{*}loc')];assert len(urls)==12 and len(set(urls))==12
 status,body,_=fetch(origin+'/blog/feed.xml');assert status==200;items=ET.fromstring(body).findall('channel/item');assert len(items)==2;publications=[{'url':x.findtext('link'),'publishedAt':x.findtext('pubDate')}for x in items];assert all(x['publishedAt']for x in publications)
 aliases=[]
 def alias(host):
  status,body,url=fetch('https://'+host+'/blog');assert status==200 and urllib.parse.urlparse(url).hostname==host and b'blog-grid'in body,host;return {'host':host,'status':status,'visitorHostPreserved':True}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:aliases=list(pool.map(alias,['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']))
 report={'passed':True,'live':True,'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'releaseHash':proof['releaseHash'],'health':health,'publicBytesVerified':checked,'publishedArticles':publications,'sitemapUrls':urls,'rootSitemapIncludesBlog':True,'rssOnlyPublishedArticles':True,'aliases':aliases,'customerAdminRecordsModified':False,'authenticatedAdmin':'Verified locally with real HTTPS/PHP/SQLite; production auth not used.'}
 (E/'http-live.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'files':len(checked),'sitemapUrls':len(urls),'aliases':len(aliases),'products':health['products']}))
if __name__=='__main__':main()
