"""Real PHP + browser tests. Live mode never writes an inquiry or account."""
from pathlib import Path
import argparse,json,os,shutil,socket,subprocess,tempfile,time
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];OUT=R/'artifacts/measurement-orders';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
release=R/'artifacts/cpanel-release-measurements-20261110';manifest=json.loads((release/'private/release.json').read_bytes());catalog=json.loads((release/'private/catalog.json').read_bytes())
front=next(p for p in catalog['products']if p.get('productType')=='cabinet-front'and p['code']=='308'and p.get('salePriceMinor'))
door=next(p for p in catalog['products']if p['id']=='door-nd683-p3');glass=next(p for p in catalog['products']if p['id']=='door-nd683-glass-1')
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def quote(path):return "'"+path.as_posix().replace("'","\\'")+"'"
temp=server=proxy=log=None;origin='https://nodenohome.com';checks=[]
try:
 if not args.live:
  # Dynamic TLS ports, isolated account storage and a validated offline bulletin
  # require the same custom PHP harness as the project-commerce acceptance.
  temp=Path(tempfile.mkdtemp(prefix='nodeno-measurements-'));local=temp/'release';shutil.copytree(release,local);storage=temp/'data';storage.mkdir();(local/'private/cache').mkdir(exist_ok=True)
  (local/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+quote(local/'private')+",'storageRoot'=>"+quote(storage)+",'mediaRoot'=>"+quote(R/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf8')
  raw=(R/'artifacts/doors-r4/tcmb-09112026.xml').read_text(encoding='utf8');(temp/'bulletin.xml').write_text(raw,encoding='utf8')
  fixture=temp/'seed.php';fixture.write_text("<?php require "+quote(R/'hosting/exchange-rates.php')+"; $xml=file_get_contents("+quote(temp/'bulletin.xml')+");$fx=nodenoFxBuild(new DateTimeImmutable('now',new DateTimeZone('Europe/Istanbul')),static function($dates)use($xml){$r=[];foreach($dates as $d)$r[$d]=$d==='2026-11-09'?['status'=>200,'body'=>$xml]:['status'=>404];return $r;});file_put_contents("+quote(storage/'exchange-rates-v1.json')+",json_encode($fx));",encoding='utf8');subprocess.run([str(R/'artifacts/runtime-php/php.exe'),str(fixture)],check=True,capture_output=True)
  upstream,tls=port(),port();origin='https://127.0.0.1:'+str(tls);log=open(OUT/'browser-server.log','w',encoding='utf8');env={**os.environ,'NODENO_TEST_PUBLIC':str(local/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'}
  server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(local/'public'),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  cert,key=temp/'cert.pem',temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);time.sleep(1)
 with sync_playwright()as pw:
  for engine,width in ([('chromium',1440)]if args.smoke else[('chromium',1440),('chromium',390),('webkit',390)]):
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe';browser=getattr(pw,engine).launch(executable_path=str(executable))
   try:
    for lang in (['tr']if args.smoke else['tr','en','ru','ar']):
     context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':width,'height':1000 if width>768 else 844},is_mobile=width<768,has_touch=width<768,reduced_motion='reduce');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'))")
     cart=lambda:page.evaluate("JSON.parse(localStorage.getItem('nodeno.cart.v1')||'[]')")
     page.goto(origin+'/?lang='+lang+'&product='+front['id'],wait_until='networkidle');expect(page.locator('.measurement-configurator')).to_be_visible(timeout=15000)
     necessary=page.locator('#insights-banner .insights-actions button').last
     if necessary.is_visible():necessary.click()
     expect(page.locator('#detail-quantity')).to_have_count(0)
     if args.smoke:page.screenshot(path=str(OUT/'smoke-initial.png'),full_page=True)
     page.locator('.product-buy-actions [data-detail-add]').click();assert cart()==[];expect(page.locator('.measurement-status')).not_to_be_empty()
     def front_row(index,height,width_,quantity,application):
      r=page.locator('.measurement-row').nth(index)
      for key,value in [('heightMm',height),('widthMm',width_),('quantity',quantity)]:
       el=r.locator('[data-measure-field='+key+']');el.fill(str(value));assert el.evaluate('(e)=>document.activeElement===e')
      r.locator('[data-measure-field=application]').select_option(application)
     front_row(0,1975,225,2,'solid');page.locator('[data-measure-add]').click();front_row(1,1914,255,2,'glazed');page.locator('[data-measure-add]').click();front_row(2,247,597,3,'drawer')
     page.locator('.measurement-row').last.locator('[data-measure-copy]').click();expect(page.locator('.measurement-row')).to_have_count(4);page.locator('.measurement-row').last.locator('[data-measure-remove]').click();expect(page.locator('.measurement-row')).to_have_count(3)
     if engine=='chromium'and width==1440 and lang=='tr':
      page.emulate_media(reduced_motion='no-preference');page.locator('[data-measure-demo]').click();page.wait_for_timeout(4300)
      assert '2 / 4'in page.locator('.measurement-demo-counter').inner_text();page.locator('[data-demo-action=play]').click();paused=page.locator('.measurement-demo-counter').inner_text();page.wait_for_timeout(4200);assert page.locator('.measurement-demo-counter').inner_text()==paused;page.locator('[data-demo-action=close]').click();page.emulate_media(reduced_motion='reduce')
     page.locator('[data-measure-demo]').click();expect(page.locator('#measurement-demo')).to_be_visible();assert cart()==[]
     for _ in range(3):page.locator('[data-demo-action=next]').click()
     expect(page.locator('.measurement-demo-example')).to_have_count(3);expect(page.locator('#measurement-demo .measurement-totals')).to_be_visible()
     page.screenshot(path=str(OUT/('live-'if args.live else'local-')/(engine+'-'+str(width)+'-'+lang+'-front-demo.png')))
     page.keyboard.press('Escape');expect(page.locator('#measurement-demo')).not_to_be_visible();expect(page.locator('[data-measure-demo]')).to_be_focused();assert page.locator('.measurement-row').first.locator('[data-measure-field=heightMm]').input_value()=='1975'
     # Watch/close did not alter the draft; applying the example is explicit.
     page.locator('.measurement-row').first.locator('[data-measure-field=quantity]').fill('9');page.locator('[data-measure-demo]').click();page.locator('[data-demo-action=apply]').click();assert page.locator('.measurement-row').first.locator('[data-measure-field=quantity]').input_value()=='2';assert cart()==[]
     page.locator('.measurement-row').first.locator('[data-measure-field=quantity]').fill('9')
     expect(page.locator('#toast.visible')).to_have_count(0,timeout=5000)
     page.locator('.measurement-configurator').screenshot(path=str(OUT/('live-'if args.live else'local-')/(engine+'-'+str(width)+'-'+lang+'-front-list.png')))
     page.locator('.product-buy-actions [data-detail-add]').click();assert len(cart())==3
     assert [r['options']['application']for r in cart()]==['solid','glazed','drawer']
     page.goto(origin+'/?lang='+lang+'&page=cart',wait_until='networkidle');expect(page.locator('.basket-item')).to_have_count(3);page.reload(wait_until='networkidle');expect(page.locator('.basket-item')).to_have_count(3)
     page.locator('[data-door-country]').select_option('DE');expect(page.locator('.basket-summary a[href*=checkout]')).to_have_count(0);page.locator('[data-door-country]').select_option('TR')
     page.goto(origin+'/?lang='+lang+'&product='+door['id'],wait_until='networkidle');expect(page.locator('.measurement-row')).to_have_count(1)
     def door_row(index,width_,frame,quantity):
      r=page.locator('.measurement-row').nth(index);r.locator('[data-measure-field=heightMm]').fill('2070');r.locator('[data-measure-field=leafWidthMm]').select_option(str(width_));r.locator('[data-measure-field=frameWidthMm]').select_option(str(frame));r.locator('[data-measure-field=quantity]').fill(str(quantity))
     assert page.locator('[data-measure-field=frameWidthMm] option').evaluate_all('(els)=>els.map(e=>Number(e.value))')==[95,115,145,165,185,215]
     door_row(0,770,165,2);page.locator('[data-measure-add]').click();door_row(1,870,145,2);page.locator('[data-measure-add]').click();door_row(2,870,115,1)
     page.locator('.measurement-row').last.locator('[data-measure-field=glazed]').check();page.locator('.product-buy-actions [data-detail-add]').click();assert len(cart())==3 # no partial addition with missing glass model
     page.locator('.measurement-row').last.locator('[data-measure-field=glassModelId]').select_option(glass['id'])
     expect(page.locator('.measurement-glass-preview img')).to_be_visible()
     if width<768:assert '35.815'in page.locator('.mobile-purchase>span').inner_text()if lang=='tr'else page.locator('.mobile-purchase>span strong').inner_text()!='—'
     page.locator('[data-measure-demo]').click()
     for _ in range(3):page.locator('[data-demo-action=next]').click()
     expect(page.locator('.measurement-demo-example')).to_have_count(3);page.screenshot(path=str(OUT/('live-'if args.live else'local-')/(engine+'-'+str(width)+'-'+lang+'-door-demo.png')));page.locator('[data-demo-action=close]').click()
     page.locator('.measurement-configurator').screenshot(path=str(OUT/('live-'if args.live else'local-')/(engine+'-'+str(width)+'-'+lang+'-door-list.png')))
     assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),(engine,width,lang,'overflow')
     page.locator('.product-buy-actions [data-detail-add]').click();assert len(cart())==6
     lines=cart();door_lines=[r for r in lines if r['id']==door['id']];assert len(door_lines)==3 and sum(r['quantity']for r in door_lines)==5
     data=context.request.get(origin+'/api/catalog').json();body={'items':door_lines,'country':'TR','currency':'TRY','priceRevision':data.get('meta',{}).get('controlRevision')or 0}
     q=context.request.post(origin+'/api/commerce/quote',data=body,headers={'Origin':origin});assert q.ok,q.text();quote_=q.json();assert quote_['subtotalTryMinor']==door['salePriceMinor']*5+door['door']['charges']['glazing'];assert quote_['minimumEligible']and not quote_['checkoutEnabled']
     body['items']=lines;full=context.request.post(origin+'/api/commerce/quote',data=body,headers={'Origin':origin});assert full.ok,full.text();assert full.json()['frontAreaMm2']==5417892 and full.json()['requiresQuote']and full.json()['minimumEligible']
     body['items']=[{**door_lines[2],'options':{**door_lines[2]['options'],'glassModelId':'unknown'}}];bad=context.request.post(origin+'/api/commerce/quote',data=body,headers={'Origin':origin});assert bad.status==422
     page.goto(origin+'/?lang='+lang+'&page=cart',wait_until='networkidle');expect(page.locator('.basket-item')).to_have_count(6);page.reload(wait_until='networkidle');expect(page.locator('.basket-item')).to_have_count(6)
     if engine=='chromium'and width==1440 and lang=='tr':
      page.goto(origin+'/?lang=tr&product='+glass['id'],wait_until='networkidle');expect(page.locator('.measurement-row')).to_have_count(1);page.locator('[data-measure-finish]').select_option('door-nd683-p39')
      assert '10.560'in page.locator('.detail-price').inner_text();page.locator('[data-measure-demo]').click();page.locator('[data-demo-action=apply]').click();expect(page.locator('.measurement-row')).to_have_count(3)
      page.locator('.product-buy-actions [data-detail-add]').click();lake=[r for r in cart()if r['id']=='door-nd683-p39'];assert len(lake)==3
      body={'items':lake,'country':'TR','currency':'TRY','priceRevision':data.get('meta',{}).get('controlRevision')or 0};response=context.request.post(origin+'/api/commerce/quote',data=body,headers={'Origin':origin});assert response.ok,response.text();assert response.json()['subtotalTryMinor']==1056000*5+132000
     assert not errors,(engine,width,lang,errors)
     checks.append({'engine':engine,'width':width,'locale':lang,'frontRows':3,'doorRows':3,'frameOptions':[95,115,145,165,185,215],'atomicAddition':True,'exactServerPrices':True,'realGlassChoice':True,'demosIsolated':True,'demoApplyExplicit':True,'reload':True,'minimums':True,'horizontalOverflow':False});context.close()
   finally:browser.close()
 report={'passed':True,'live':args.live,'smoke':args.smoke,'releaseHash':manifest['releaseHash'],'scenarios':len(checks),'checks':checks,'physicalPhoneTested':False,'checkoutEnabled':False};(OUT/('live-acceptance.json'if args.live else'local-smoke.json'if args.smoke else'local-acceptance.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
finally:
 if proxy:proxy.terminate();proxy.wait(timeout=10)
 if server:server.terminate();server.wait(timeout=10)
 if log:log.close()
 if temp:
  assert temp.resolve().parent==Path(tempfile.gettempdir()).resolve()and temp.name.startswith('nodeno-measurements-');shutil.rmtree(temp)
