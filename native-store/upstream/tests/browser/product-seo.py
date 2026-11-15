"""Exact-package SEO checks: crawler HTML, four locales, SPA pagination and real variants."""
from pathlib import Path
import os,json,subprocess,socket,time,shutil,mimetypes
from urllib.parse import urlparse,unquote
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/seo-products';proof=json.loads((E/'release.json').read_bytes());release=R/proof['release'];out=E/'browser';out.mkdir(exist_ok=True);local=out/'runtime';(local/'public').mkdir(parents=True,exist_ok=True);(local/'storage').mkdir(exist_ok=True)
for f in(release/'public').iterdir():
 if f.is_file():shutil.copyfile(f,local/'public'/f.name)
q=lambda p:"'"+p.as_posix().replace("'","\\'")+"'"; (local/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(release/'private')+",'storageRoot'=>"+q(local/'storage')+"];",encoding='utf8')
with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
origin='http://127.0.0.1:'+str(port);log=(out/'server.log').open('w');server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-S','127.0.0.1:'+str(port),'-t',str(local/'public'),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(local/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);checks=[]
try:
 time.sleep(1)
 with sync_playwright()as pw:
  api=pw.request.new_context();catalog=api.get(origin+'/api/catalog').json();assert len(catalog['products'])==3602
  maps=[]
  for lang in ['tr','en','ru','ar']:
   raw=api.get(origin+'/sitemap-products-'+lang+'.xml');assert raw.status==200;xml=ET.fromstring(raw.body());ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9','i':'http://www.google.com/schemas/sitemap-image/1.1'};assert len(xml.findall('s:url',ns))==3602;maps.append({'lang':lang,'products':3602,'images':len(xml.findall('.//i:loc',ns))})
  assert 'noindex'in api.get(origin+'/api/catalog').headers.get('x-robots-tag','');assert 'Disallow: /api/'in api.get(origin+'/robots.txt').text()
  for engine,width,langs in [('chromium',1440,['tr','en','ru','ar']),('webkit',390,['tr','ar'])]:
   executable=Path.home()/'AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe';browser=getattr(pw,engine).launch(executable_path=str(executable),headless=True)
   for lang in langs:
    for js in ([False,True]if engine=='chromium'else[True]):
     ctx=browser.new_context(viewport={'width':width,'height':900},java_script_enabled=js,is_mobile=width<768,has_touch=width<768);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     def asset(route):
      f=release/'public'/unquote(urlparse(route.request.url).path).lstrip('/')
      if f.is_file():route.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0]or'application/octet-stream')
      else:route.continue_()
     page.route('**/assets/**',asset);page.route('**/media/**',lambda route:route.abort());page.add_init_script("localStorage.setItem('nodeno.analytics.consent.v1','false');localStorage.setItem('nodeno.international-welcome.hidden','1')")
     url=origin+'/?lang='+lang+'&page=catalog&category=ahsap-mobilya-malzemeleri&pg=2';response=page.goto(url,wait_until='networkidle');assert response.status==200;assert page.locator('link[rel=canonical]').get_attribute('href').endswith('&pg=2');assert page.locator('link[hreflang]').count()==5;assert page.locator('.product-grid>.product-card').count()==24
     assert page.locator('.catalog-pagination a[href*="pg=3"]').count()or page.locator('nav a[href*="pg=3"]').count();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
     if js:
      nextlink=page.locator('.catalog-pagination a[href*="pg=3"]').first;nextlink.click();expect(page.locator('link[rel=canonical]')).to_have_attribute('href','https://nodenohome.com/?lang='+lang+'&page=catalog&category=ahsap-mobilya-malzemeleri&pg=3');assert page.locator('.product-grid>.product-card').count()==24
      page.goto(origin+'/?lang='+lang+'&product=alka-181cc5ebc3',wait_until='networkidle');expect(page.locator('#product-title')).to_have_text(next(p for p in catalog['products']if p['id']=='alka-181cc5ebc3')['modelName'][lang]);assert page.locator('html').get_attribute('dir')==('rtl'if lang=='ar'else'ltr');assert 'فواتير'not in page.title()and'Invoice'not in page.title();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
      if lang in ['tr','ar']:page.screenshot(path=str(out/f'{engine}-{width}-{lang}.png'))
     assert not errors,errors;checks.append({'engine':engine,'width':width,'lang':lang,'javascript':js,'passed':True});ctx.close()
   browser.close()
  assert api.get(origin+'/?page=catalog&pg=999999').status==404
  api.dispose()
 report={'passed':True,'live':False,'releaseHash':proof['releaseHash'],'checks':checks,'sitemaps':maps};(E/'browser.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'sitemapProductUrls':14408,'releaseHash':proof['releaseHash']}))
finally:server.terminate();server.wait(timeout=10);log.close()
