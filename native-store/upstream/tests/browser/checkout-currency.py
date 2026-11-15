"""Isolated checkout review and currency placement; no live customer writes."""
from pathlib import Path
import argparse,json,os,shutil,socket,subprocess,tempfile,time,mimetypes,ctypes,hashlib
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--release',default='artifacts/cpanel-release-suppliers-20261110');parser.add_argument('--source',action='store_true');parser.add_argument('--live',action='store_true');parser.add_argument('--output',default='artifacts/checkout-currency');parser.add_argument('--smoke',action='store_true');args=parser.parse_args();O=R/args.output;O.mkdir(parents=True,exist_ok=True)
base=R/args.release
files=['app.js','door-ui.js','door-commerce.css','styles.css','shop-i18n.js']
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
temp=server=proxy=log=None;origin='https://nodenohome.com';report={'passed':False,'checks':[],'live':args.live,'releaseHash':json.loads((base/'private/release.json').read_bytes())['releaseHash']}
try:
 if not args.live:
  temp=Path(tempfile.mkdtemp(prefix='nodeno-checkout-'));release=temp/'release';shutil.copytree(base,release,ignore=shutil.ignore_patterns('fronts','doors','cache'))
  if args.source:
   for f in files:shutil.copyfile(R/'web'/f,release/'public'/f)
   shutil.copyfile(R/'web/index.html',release/'private/index.html')
  store=temp/'data';store.mkdir();q=lambda p:"'"+p.as_posix().replace("'","\\'")+"'"
  media=R/'artifacts/media-preview-15f6d6545fba84ea'
  if os.name=='nt':
   buf=ctypes.create_unicode_buffer(4096);assert ctypes.windll.kernel32.GetShortPathNameW(str(media),buf,4096);media=Path(buf.value)
  (release/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(release/'private')+",'storageRoot'=>"+q(store)+",'mediaRoot'=>"+q(media)+"];",encoding='utf8')
  # Official archived bulletin, parsed by production PHP; no invented rates.
  raw=R/'artifacts/doors-r4/tcmb-09112026.xml';seed=temp/'fx.php'
  seed.write_text("<?php require "+q(R/'hosting/exchange-rates.php')+";$xml=file_get_contents("+q(raw)+");$fx=nodenoFxBuild(new DateTimeImmutable('now',new DateTimeZone('Europe/Istanbul')),static function($dates)use($xml){$r=[];foreach($dates as $d)$r[$d]=$d==='2026-11-09'?['status'=>200,'body'=>$xml]:['status'=>404];return $r;});file_put_contents("+q(store/'exchange-rates-v1.json')+",json_encode($fx));",encoding='utf8')
  subprocess.run([str(R/'artifacts/runtime-php/php.exe'),str(seed)],check=True,capture_output=True)
  upstream,tls=port(),port();origin='https://127.0.0.1:'+str(tls);log=(O/'server.log').open('w')
  server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-S','127.0.0.1:'+str(upstream),'-t',str(release/'public'),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  cert,key=temp/'cert.pem',temp/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  node=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
  proxy=subprocess.Popen([str(node),str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 with sync_playwright()as pw:
  engines=[('chromium',1440),('chromium',390)]
  wk=R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  if not args.live and wk.exists():engines.append(('webkit',390))
  if args.smoke:engines=[('chromium',1440)]
  for engine,width in engines:
   exe=Path.home()/'AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'if engine=='chromium'else wk
   browser=getattr(pw,engine).launch(executable_path=str(exe))
   for lang in (['tr']if args.smoke else['tr','en','ru','ar']):
    context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':width,'height':1000 if width>768 else 844},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:print('CONSOLE '+m.text,flush=True)if m.type=='error'else None)
    if not args.live:
     def assets(route):
      path=base/'public'/unquote(urlparse(route.request.url).path).lstrip('/')
      if path.is_file():route.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(str(path))[0]or'application/octet-stream')
      else:route.continue_()
     page.route('**/assets/**',assets)
     approved=json.loads((base/'private/media-approved.json').read_bytes());cleanup=json.loads((R/'artifacts/media-cleanup.json').read_bytes())
     def media_bytes(route):
      parts=urlparse(route.request.url).path.strip('/').split('/');key=approved['references'].get(parts[1]+':'+parts[2])
      if not key:route.continue_();return
      row=approved['images'][key];body=(R/cleanup['images'][key]['path']).read_bytes();assert hashlib.sha256(body).hexdigest()==row['outputSha'];route.fulfill(body=body,content_type=row['mime'])
     page.route('**/media/**',media_bytes)
    page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));if(!localStorage.getItem('nodeno.currency.v1'))localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'))")
    page.goto(origin+'/?lang='+lang,wait_until='networkidle');expect(page.locator('.home-page')).to_be_visible()
    necessary=page.locator('#insights-banner .insights-actions button').last
    if necessary.is_visible():necessary.click()
    if not page.locator('.home-page .product-shelf .section-heading [data-display-currency]').count():
     print(json.dumps({'errors':errors,'scripts':page.locator('script[src]').evaluate_all('(a)=>a.map(x=>x.src)'),'appHasHook':'doorUI?.toolbar();if(focus)'in context.request.get(origin+'/app.js').text(),'doorHasPicker':'data-currency-picker'in context.request.get(origin+'/door-ui.js').text(),'shelves':page.locator('.product-shelf .section-heading').count(),'pickers':page.locator('[data-display-currency]').evaluate_all('(a)=>a.map(x=>x.parentElement.outerHTML+" PARENT "+x.parentElement.parentElement.className)')},ensure_ascii=False),flush=True)
     page.screenshot(path=str(O/'diagnostic-home.png'))
    expect(page.locator('.home-page .product-shelf .section-heading [data-display-currency]')).to_have_count(1)
    expect(page.locator('#currency-toolbar,.exchange-explanation')).to_have_count(0)
    page.locator('[data-display-currency]').select_option('USD');expect(page.locator('[data-display-currency]')).to_have_value('USD');page.wait_for_load_state('networkidle')
    page.screenshot(path=str(O/f'{"live"if args.live else"local"}-{engine}-{width}-{lang}-home.png'))
    if lang=='tr':page.locator('.home-page .product-shelf').first.screenshot(path=str(O/f'{"live"if args.live else"local"}-{engine}-{width}-currency-shelf.png'))
    # Stay within the real SPA for product navigation; no parallel document reload.
    product=page.locator('.home-page .product-card h3 a').first;product.click();expect(page.locator('.product-price-block [data-display-currency]')).to_have_count(1);page.wait_for_load_state('networkidle')
    page.evaluate("localStorage.setItem('nodeno.cart.v1',JSON.stringify([{id:'2395',quantity:2},{id:'2393',quantity:1}]))")
    page.goto(origin+'/?lang='+lang+'&page=cart',wait_until='networkidle');expect(page.locator('.basket-summary [data-display-currency]')).to_have_count(1)
    page.locator('.basket-summary a[href*=checkout]').click();page.locator('[data-action=guest-start]').click();form=page.locator('#guest-checkout-form')
    for name,value in {'name':'Deniz Örnek','email':'deniz@example.test','phone':'+905551112233','city':'İzmir','district':'Buca','postalCode':'35040','line1':'Örnek Mahallesi Deneme Sokak 12'}.items():form.locator('[name="'+name+'"]').fill(value)
    form.locator('[name=country]').select_option('TR');form.locator('[type=submit]').click();expect(page.locator('.guest-review')).to_be_visible()
    if width>=1000:
     left=page.locator('.guest-review').bounding_box();right=page.locator('.checkout-page .basket-summary').bounding_box();assert abs(left['y']-right['y'])<=2,{'leftTop':left['y'],'summaryTop':right['y']}
    expect(page.locator('.review-address-card')).to_have_count(2);expect(page.locator('.checkout-product-photo img')).to_have_count(2);expect(page.locator('.checkout-items .product-code')).to_have_count(0)
    page.wait_for_function('Array.from(document.querySelectorAll(".checkout-product-photo img")).every(i=>i.complete&&i.naturalWidth>0)')
    before=page.locator('.summary-subtotal bdi').inner_text();page.locator('.basket-summary [data-display-currency]').select_option('EUR');after=page.locator('.summary-subtotal bdi').inner_text();assert before!=after
    expect(page.locator('.guest-review')).to_contain_text('deniz@example.test');expect(page.locator('[data-payment-gate]')).to_be_disabled()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(engine,width,lang)
    for img in page.locator('.checkout-product-photo img').all():img.scroll_into_view_if_needed();expect(img).to_be_visible()
    page.wait_for_function('Array.from(document.querySelectorAll(".checkout-product-photo img")).every(i=>i.complete&&i.naturalWidth>0)');page.evaluate('async()=>{window.scrollTo({top:0,left:0,behavior:"instant"});await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame)}')
    page.wait_for_function('scrollY===0')
    (O/f'geometry-{engine}-{width}-{lang}.json').write_text(json.dumps(page.evaluate('()=>({scrollY,headerTop:document.querySelector(".store-header").getBoundingClientRect().top,leftTop:document.querySelector(".guest-review").getBoundingClientRect().top,rightTop:document.querySelector(".checkout-page .basket-summary").getBoundingClientRect().top})')))
    page.screenshot(path=str(O/f'{"live"if args.live else"local"}-{engine}-{width}-{lang}-review.png'),full_page=True)
    if lang=='tr':page.locator('.guest-review').screenshot(path=str(O/f'{"live"if args.live else"local"}-{engine}-{width}-address-cards.png'))
    page.locator('[data-action=guest-edit]').click();expect(page.locator('[name=email]')).to_have_value('deniz@example.test')
    page.locator('[name=sameBilling]').uncheck()
    for name,value in {'billing_name':'Fatura Alıcısı','billing_city':'Ankara','billing_line1':'Fatura Mahallesi Örnek Sokak 20'}.items():page.locator('[name="'+name+'"]').fill(value)
    page.locator('#guest-checkout-form [type=submit]').click();expect(page.locator('.review-billing')).to_contain_text('Ankara');expect(page.locator('.review-delivery')).to_contain_text('İzmir')
    assert not errors,errors;report['checks'].append({'engine':engine,'width':width,'locale':lang,'currencyPersists':True,'reviewDraftPreserved':True,'separateBilling':True,'noOverflow':True,'paymentDisabled':True});context.close()
   browser.close()
 report['passed']=True
finally:
 if proxy:proxy.terminate();proxy.wait(timeout=10)
 if server:server.terminate();server.wait(timeout=10)
 if log:log.close()
 (O/('live-browser.json'if args.live else'browser.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
