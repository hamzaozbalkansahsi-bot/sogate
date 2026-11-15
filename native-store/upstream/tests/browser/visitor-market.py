"""Real PHP country lookup + responsive browser acceptance; no production writes.

The IP fixture is a private temporary file read only by an unshipped test router.
Production has no country query/header override.
"""
from pathlib import Path
import argparse,ipaddress,json,os,shutil,socket,subprocess,tempfile,time
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/visitor-market';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--visual-only',action='store_true');args=parser.parse_args()
def port():
 s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close();return p
def quote(p):return "'"+p.as_posix().replace("'","\\'")+"'"
countries=['TR','DE','GB','RU','KZ','IQ','SY','AZ','TM','IR'];ips={}
data=(ROOT/'data/geo/geo-v4.bin').read_bytes()
for offset in range(0,len(data),10):
 row=data[offset:offset+10];country=row[8:].decode();address=ipaddress.ip_address(row[:4])
 if country in countries and country not in ips and address.is_global:ips[country]=str(address)
assert len(ips)==len(countries)
ips['unknown']='127.0.0.1';server=proxy=None;log=None;temp=None;origin='https://nodenohome.com';checks=[]
try:
 if not args.live:
  temp=Path(tempfile.mkdtemp(prefix='nodeno-market-',dir='D:/NODENO_QA_TEMP'));release=temp/'release';shutil.copytree(ROOT/'artifacts/cpanel-release',release);storage=temp/'data';storage.mkdir();peer=temp/'peer.txt';peer.write_text(ips['TR'])
  (release/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+quote(release/'private')+",'storageRoot'=>"+quote(storage)+",'mediaRoot'=>"+quote(ROOT/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf-8')
  router=temp/'router.php';router.write_text("<?php $_SERVER['HTTPS']='on';$_SERVER['REMOTE_ADDR']=trim(file_get_contents("+quote(peer)+"));return require "+quote(ROOT/'hosting/dev-router.php')+";",encoding='utf-8')
  upstream=port();tls=port();origin='https://127.0.0.1:'+str(tls);log=open(OUT/'browser-server.log','w',encoding='utf-8');env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public')}
  server=subprocess.Popen([str(ROOT/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(release/'public'),str(router)],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  cert=temp/'cert.pem';key=temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  proxy=subprocess.Popen(['node',str(ROOT/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);time.sleep(1)
 with sync_playwright() as p:
  for engine,width in [('chromium',390),('chromium',1440),('webkit',390)]:
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(p,engine).launch(executable_path=str(executable))
   try:
    for country in (['live'] if args.live else ['TR','DE','IQ'] if args.visual_only else [*countries,'unknown']):
     if not args.live:peer.write_text(ips[country])
     context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':width,'height':900},is_mobile=width<768,has_touch=width<768,locale='ar-IQ');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     if args.live:
      health=context.request.get(origin+'/api/health');assert health.ok;assert health.json()['releaseHash']==json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text())['releaseHash']
     actual=context.request.get(origin+'/api/visitor-context');assert actual.ok,(actual.status,actual.text());visitor=actual.json();international=visitor['international'];expected=visitor['suggestedLocale'];cc=visitor['country']
     assert actual.headers['cache-control']=='private, no-store'
     if not args.live:
      assert cc==(None if country=='unknown' else country)
      assert international==(country not in ['TR','unknown'])
      assert expected==('tr' if country in ['TR','unknown'] else 'ru' if country in ['RU','KZ'] else 'ar' if country in ['IQ','SY'] else 'en')
     response=page.goto(origin+'/?product=4907',wait_until='networkidle');assert response.ok
     expect(page.locator('.product-purchase')).to_be_visible();expect(page.locator('html')).to_have_attribute('lang',expected)
     assert page.locator('.product-purchase > [data-wholesale-only]').count()==int(international)
     navs=page.locator('[data-wholesale-nav]').evaluate_all("els=>els.map(el=>({text:el.textContent,hidden:el.hidden,marker:el.hasAttribute('data-wholesale-only'),display:getComputedStyle(el).display,rect:el.getBoundingClientRect().toJSON(),market:document.documentElement.dataset.market}))")
     assert (page.locator('[data-wholesale-nav]:visible').count()>0 if international else page.locator('[data-wholesale-nav]:visible').count()==0),(engine,width,country,visitor,navs)
     # Retail set building survives the removal of the similarly styled B2B callout.
     expect(page.locator('.product-set-entry')).to_have_count(1)
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(engine,width,country,'horizontal overflow')
     canonical=page.locator('link[rel=canonical]').get_attribute('href');assert 'lang='+expected in canonical
     if country in ['TR','DE','IQ','live']:
      page.screenshot(path=str(OUT/(('live-' if args.live else '')+engine+'-'+str(width)+'-'+country+'-automatic.png')),full_page=False)
      page.locator('.product-purchase').screenshot(path=str(OUT/(('live-' if args.live else '')+engine+'-'+str(width)+'-'+country+'-purchase.png')))
     page.locator('#language').select_option('ar' if expected!='ar' else 'en');manual='ar' if expected!='ar' else 'en'
     expect(page.locator('html')).to_have_attribute('lang',manual)
     assert page.locator('.product-purchase > [data-wholesale-only]').count()==int(international)
     # Reload a root URL with no lang parameter: both SSR and hydrated UI respect manual choice.
     html=context.request.get(origin+'/?product=4907').text();assert 'lang="'+manual+'"' in html[:500]
     page.goto(origin+'/?product=4907',wait_until='networkidle');expect(page.locator('html')).to_have_attribute('lang',manual)
     # An explicit supported URL wins over the saved choice.
     page.goto(origin+'/?product=4907&lang=ru',wait_until='networkidle');expect(page.locator('html')).to_have_attribute('lang','ru')
     page.goto(origin+'/?page=sets&set=bohera-bedroom',wait_until='networkidle');expect(page.locator('.furniture-page')).to_be_visible()
     assert page.locator('.furniture-mode [data-wholesale-only]:visible').count()==int(international)
     assert not errors,(engine,width,country,errors)
     checks.append({'engine':engine,'width':width,'country':cc,'automaticLocale':expected,'international':international,'manualAndURLOverride':True,'retailSetPreserved':True});context.close()
   finally:browser.close()
 result={'passed':True,'live':args.live,'checks':checks,'releaseHash':json.loads((ROOT/'artifacts/cpanel-release/private/release.json').read_text())['releaseHash']}
 (OUT/('live-report.json' if args.live else 'visual-report.json' if args.visual_only else 'browser-report.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':True,'live':args.live,'scenarios':len(checks)}))
finally:
 for process in [proxy,server]:
  if process:process.terminate();process.wait(timeout=10)
 if log:log.close()
 if temp and temp.parent==Path('D:/NODENO_QA_TEMP') and temp.name.startswith('nodeno-market-'):shutil.rmtree(temp)
