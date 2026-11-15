"""Welcome acceptance on an isolated copy of the real PHP release, or read-only live."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,socket,subprocess,tempfile,time
from playwright.sync_api import sync_playwright,expect,Error as BrowserError

R=Path(__file__).resolve().parents[2];OUT=R/'artifacts/welcome-poster-v2';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def quote(p):return "'"+p.as_posix().replace("'","\\'")+"'"
def navigate(page,url):
 try:return page.goto(url,wait_until='networkidle')
 except BrowserError as error:
  if not any(code in str(error)for code in ['ERR_SOCKET_NOT_CONNECTED','ERR_CONNECTION_RESET','ERR_CONNECTION_CLOSED']):raise
  page.wait_for_timeout(500)
  return page.goto(url,wait_until='networkidle')
def catalogue_ready(page):
 try:expect(page.locator('.product-card').first).to_be_visible(timeout=10000)
 except AssertionError:
  retry=page.locator('[data-action="retry-catalog"]')
  if not retry.is_visible():raise
  # Exercise the site's visible recovery after a transient failed catalogue fetch.
  retry.click();expect(page.locator('.product-card').first).to_be_visible(timeout=10000)
release=R/'artifacts/cpanel-release-welcome-v2-20261103';expected=json.loads((release/'private/release.json').read_bytes())['releaseHash']
temp=server=proxy=log=None;origin='https://nodenohome.com';checks=[]
try:
 if not args.live:
  temp=Path(tempfile.mkdtemp(prefix='nodeno-welcome-'));local=temp/'release';shutil.copytree(release,local);storage=temp/'data';storage.mkdir()
  (local/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+quote(local/'private')+",'storageRoot'=>"+quote(storage)+",'mediaRoot'=>"+quote(R/'artifacts/media-preview-15f6d6545fba84ea')+"];",encoding='utf8')
  upstream,tls=port(),port();origin='https://127.0.0.1:'+str(tls);log=open(OUT/'browser-server.log','w',encoding='utf8')
  env={**os.environ,'NODENO_TEST_PUBLIC':str(local/'public'),'NODENO_TEST_HTTPS':'loopback-tls-only'}
  server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','display_errors=0','-S','127.0.0.1:'+str(upstream),'-t',str(local/'public'),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  cert,key=temp/'cert.pem',temp/'key.pem'
  subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);time.sleep(1)
 with sync_playwright()as p:
  if args.live:
   request=p.request.new_context();health=request.get(origin+'/api/health');assert health.ok and health.json()['status']=='ok' and health.json()['releaseHash']==expected;request.dispose()
  for engine,width,height in [('chromium',1440,1000),('chromium',390,844),('chromium',320,568),('webkit',390,844)]:
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(p,engine).launch(executable_path=str(executable))
   try:
    for lang in ['tr','en','ru','ar']:
     context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':width,'height':height},is_mobile=width<768,has_touch=width<768,reduced_motion='reduce');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     page.add_init_script("localStorage.setItem('nodeno.international-welcome.seen','1')")
     navigate(page,origin+'/?lang='+lang);poster=page.locator('#international-welcome');expect(poster).to_be_visible(timeout=10000)
     expect(poster.locator('[data-country]')).to_have_count(10);expect(poster).to_have_attribute('lang',lang);expect(poster).to_have_attribute('dir','rtl'if lang=='ar'else'ltr')
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
     layout=poster.evaluate("el=>{const r=el.getBoundingClientRect(),b=el.querySelector('.welcome-poster-close').getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,closeRight:b.right,closeTop:b.top,closeWidth:b.width,closeHeight:b.height,overflow:el.querySelector('.welcome-poster-scroll').scrollWidth>el.clientWidth}}")
     assert layout['left']>=0 and layout['right']<=width and layout['top']>=0 and layout['bottom']<=height,layout
     assert layout['closeWidth']>=44 and layout['closeHeight']>=44 and layout['right']-layout['closeRight']<=18,layout
     assert not layout['overflow'],layout
     assert poster.locator('img').evaluate_all('els=>els.every(e=>e.complete&&e.naturalWidth>0)')
     expect(poster.locator('.welcome-country-map [role=option]')).to_have_count(79)
     expect(poster.locator('#welcome-dont-show')).not_to_be_checked()
     file=OUT/(('live-'if args.live else'local-')+engine+'-'+str(width)+'-'+lang+'.png');page.screenshot(path=str(file),full_page=False)
     # Native modal traps focus, and the two closing controls are reachable.
     poster.locator('.welcome-poster-close').focus();page.keyboard.press('Shift+Tab');assert page.evaluate("document.activeElement.closest('#international-welcome')!==null")
     page.keyboard.press('Escape');expect(poster).to_have_count(0)
     assert page.evaluate("localStorage.getItem('nodeno.international-welcome.hidden')")is None
     if not args.live or lang=='tr':
      page.reload(wait_until='networkidle');catalogue_ready(page);expect(poster).to_be_visible(timeout=10000)
      poster.locator('#welcome-dont-show').check();poster.locator('.welcome-poster-close').click();page.reload(wait_until='networkidle');catalogue_ready(page);page.wait_for_timeout(700);expect(poster).to_have_count(0)
     assert not errors,(engine,width,lang,errors)
     checks.append({'engine':engine,'width':width,'language':lang,'viewportFits':True,'tenCountries':True,'escape':True,'reopensUnlessOptedOut':not args.live or lang=='tr','explicitOptOutPersists':not args.live or lang=='tr','legacySeenIgnored':True,'screenshot':file.relative_to(R).as_posix(),'screenshotSha256':hashlib.sha256(file.read_bytes()).hexdigest()});context.close()
     (OUT/('live-browser-progress.json'if args.live else'local-browser-progress.json')).write_text(json.dumps({'releaseHash':expected,'checks':checks},ensure_ascii=False,indent=2),encoding='utf8')
    # Real 30-second timer tested with the browser clock, without changing production timing.
    if not args.live or (engine=='chromium' and width==1440):
     context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':width,'height':height});page=context.new_page()
     if not args.live:page.clock.install()
     page.add_init_script("new MutationObserver((_,observer)=>{if(document.querySelector('#international-welcome[open]')){window.welcomeTestOpenedAt=Date.now();observer.disconnect();}}).observe(document,{subtree:true,childList:true,attributes:true,attributeFilter:['open']})")
     navigate(page,origin+'/?lang=tr');expect(page.locator('#international-welcome')).to_be_visible(timeout=10000)
     elapsed=page.evaluate('Date.now()-window.welcomeTestOpenedAt');assert 0<=elapsed<29_500,elapsed
     if args.live:page.wait_for_timeout(int(29_500-elapsed))
     else:page.clock.fast_forward(int(29_500-elapsed))
     expect(page.locator('#international-welcome')).to_be_visible()
     if args.live:page.wait_for_timeout(600)
     else:page.clock.fast_forward(600)
     expect(page.locator('#international-welcome')).to_have_count(0);context.close()
    # Country names also work by tap/list selection on mobile, without hover.
    context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':width,'height':height},is_mobile=width<768,has_touch=width<768);page=context.new_page();navigate(page,origin+'/?lang=en');expect(page.locator('#international-welcome')).to_be_visible(timeout=10000)
    page.locator('[data-country-select="DE"]').click();map=page.locator('.welcome-poster-map');expect(map).to_have_attribute('data-active-country','DE');expect(page.locator('.welcome-map-tooltip strong')).to_have_text('Germany');expect(page.locator('[data-country-select="DE"]')).to_have_attribute('aria-pressed','true')
    page.screenshot(path=str(OUT/(('live-'if args.live else'local-')+engine+'-'+str(width)+'-country-selected.png')),full_page=False)
    page.locator('#welcome-dont-show').check();page.locator('#welcome-dont-show').uncheck();page.locator('.welcome-poster-close').click();page.reload(wait_until='networkidle');expect(page.locator('#international-welcome')).to_be_visible(timeout=10000);context.close()
   finally:browser.close()
  # A real country polygon is raised, named and coloured; all other polygons fade.
  browser=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'))
  try:
   context=browser.new_context(ignore_https_errors=not args.live,viewport={'width':1440,'height':1000},reduced_motion='no-preference');page=context.new_page();navigate(page,origin+'/?lang=tr');expect(page.locator('#international-welcome')).to_be_visible(timeout=10000)
   map=page.locator('.welcome-poster-map');germany=map.locator('[data-map-code="DE"]');germany.hover();expect(map).to_have_attribute('data-active-country','DE');expect(map.locator('.welcome-map-tooltip strong')).to_have_text('Almanya');page.wait_for_timeout(350)
   original=germany.bounding_box();raised=map.locator('.welcome-map-emphasis path').bounding_box();assert raised['width']>original['width']*1.07 and raised['height']>original['height']*1.07,(original,raised)
   assert map.locator('.welcome-map-emphasis path').evaluate("e=>getComputedStyle(e).fill")=='rgb(216, 236, 129)'
   assert float(map.locator('[data-map-code="FR"]').evaluate("e=>getComputedStyle(e).opacity"))<.4
   assert map.locator('svg').evaluate("e=>getComputedStyle(e).transform")=='none'
   page.screenshot(path=str(OUT/('live-desktop-hover.png'if args.live else'local-desktop-hover.png')),full_page=False)
   map.locator('[data-map-code="KZ"]').hover();expect(map).to_have_attribute('data-active-country','KZ');expect(map.locator('.welcome-map-tooltip strong')).to_have_text('Kazakistan')
   map.locator('[data-map-code="FR"]').hover();expect(map.locator('.welcome-map-tooltip strong')).to_have_text('Fransa');expect(map.locator('.welcome-map-tooltip span')).to_have_text('Bu ülke için bizimle görüşebilirsiniz')
   page.mouse.move(20,20);expect(map).not_to_have_attribute('data-active-country', 'FR');expect(map.locator('.welcome-map-tooltip')).not_to_be_visible()
   page.emulate_media(reduced_motion='reduce');germany.hover();expect(map).to_have_attribute('data-active-country','DE');assert map.locator('.welcome-map-emphasis path').evaluate("e=>getComputedStyle(e).animationName")=='none'
   map.locator('svg').focus();page.keyboard.press('ArrowRight');assert map.locator('svg').get_attribute('aria-activedescendant');page.keyboard.press('Escape');expect(page.locator('#international-welcome')).to_have_count(0);context.close()
   # Blocked storage still allows the greeting; another fresh browser remains independent.
   for mode in ['blocked-storage','cart']:
    context=browser.new_context(ignore_https_errors=not args.live);page=context.new_page()
    if mode=='blocked-storage':page.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('blocked','SecurityError')}})")
    navigate(page,origin+('/?page=cart&lang=tr'if mode=='cart'else'/?lang=tr'))
    if mode=='cart':page.wait_for_timeout(900);expect(page.locator('#international-welcome')).to_have_count(0)
    else:
     expect(page.locator('#international-welcome')).to_be_visible(timeout=10000);page.locator('#welcome-dont-show').check();expect(page.locator('.welcome-preference-error')).to_be_visible()
    context.close()
  finally:browser.close()
  if args.live:
   request=p.request.new_context();health=request.get(origin+'/api/health');assert health.ok and health.json()['releaseHash']==expected;request.dispose()
 result={'passed':True,'live':args.live,'releaseHash':expected,'scenarios':len(checks),'checks':checks,'autoCloseAfter30Seconds':True,'reopensByDefault':True,'explicitOptOutPersists':True,'uncheckedOptOutShowsAgain':True,'legacyAutomaticSeenIgnored':True,'nativeFocusTrap':True,'blockedStorageStillShows':True,'checkoutUninterrupted':True,'individualCountryHover':True,'selectedPolygonRaisedAndGreen':True,'otherCountriesDimmed':True,'localizedTooltip':True,'touchListSelection':True,'reducedMotionRespected':True,'physicalPhoneTested':False}
 (OUT/('live-acceptance.json'if args.live else'local-acceptance.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='checks'}))
finally:
 for process in [proxy,server]:
  if process:process.terminate();process.wait(timeout=10)
 if log:log.close()
 if temp:
  assert temp.resolve().parent==Path(tempfile.gettempdir()).resolve() and temp.name.startswith('nodeno-welcome-');shutil.rmtree(temp)
