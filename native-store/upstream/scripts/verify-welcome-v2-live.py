"""Read-only HTTPS byte and entry-point acceptance across the four public hosts."""
from pathlib import Path
import hashlib,json,time,urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/welcome-poster-v2'
release=ROOT/'artifacts/cpanel-release-welcome-v2-20261103'
manifest=json.loads((release/'private/release.json').read_bytes())
expected=manifest['releaseHash'];checks=[]
for host in ['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr']:
 for path in ['api/health','/?lang=tr','app.js','welcome-poster.js','welcome-poster.css','welcome-country-map.js','welcome-map-data.js','assets/brand/logo-horizontal.svg']:
  separator='&'if '?'in path else '?'
  url='https://'+host+'/'+path.lstrip('/')+separator+'welcome_acceptance='+str(time.time_ns())
  request=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'NODENO-release-acceptance/2'})
  with urllib.request.urlopen(request,timeout=45)as response:
   assert response.status==200,(host,path,response.status)
   assert response.url.startswith('https://'+host+'/'),(host,path,response.url)
   body=response.read(3_000_001);assert len(body)<=3_000_000
  if path=='api/health':
   health=json.loads(body)
   assert health['status']=='ok'and health['releaseHash']==expected and health['checkoutEnabled']is False,health
   checks.append({'host':host,'path':path,'releaseHash':expected,'checkoutRemainsDisabled':True})
  elif path.startswith('/'):
   html=body.decode('utf8')
   assert 'welcome-poster.css?v=nodeno-welcome-20261103-r2'in html
   assert 'app.js?v=nodeno-welcome-20261103-r2'in html
   checks.append({'host':host,'path':path,'posterAssetsLinked':True})
  else:
   digest=hashlib.sha256(body).hexdigest()
   assert digest==manifest['files']['public/'+path],(host,path,digest)
   checks.append({'host':host,'path':path,'sha256':digest,'bytes':len(body)})
result={'passed':True,'releaseHash':expected,'checks':checks}
(OUT/'live-https.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'releaseHash':expected,'httpsChecks':len(checks)}))
