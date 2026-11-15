"""Actual PHP + SQLite, responsive paint catalogue, cart and supplier alerts."""
from pathlib import Path
import base64,hashlib,hmac,json,os,socket,struct,subprocess,time,sys
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];evidence=os.environ.get('NODENO_PAINT_EVIDENCE','artifacts/bianca-20261112');assert evidence in ['artifacts/bianca-20261112','artifacts/paint-completion-20261112','artifacts/paint-resolution-20261112','artifacts/paint-alternatives-20261112'];E=R/evidence;W=E/'preview';P=W/'public';W.mkdir(exist_ok=True);P.mkdir(exist_ok=True);(W/'storage').mkdir(exist_ok=True)
proof=json.loads((E/'release.json').read_bytes());C=R/proof['release'];prepared=json.loads((E/'catalogue-prepared.json').read_bytes())
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def otp():
 d=hmac.new(base64.b32decode('JBSWY3DPEHPK3PXP'),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=d[-1]&15;return str((struct.unpack('>I',d[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
def q(p):return "'"+str(p).replace('\\','/').replace("'","\\'")+"'"
for f in (C/'public').rglob('*'):
 if not f.is_file():continue
 dest=P/f.relative_to(C/'public');dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():
  if dest.read_bytes()==f.read_bytes():continue
  dest.unlink()
 os.link(f,dest)
(W/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(C/'private')+",'storageRoot'=>"+q(W/'storage')+",'mediaRoot'=>"+q(R/'artifacts/social-engine-20261112/preview/media')+"];",encoding='utf-8')
php="require $argv[1].'/control-http.php';$db=nodenoControlDatabase($argv[2]);$id='paint-qa';$now=time();$db->prepare('INSERT OR REPLACE INTO control_users(id,email,role,password_hash,totp_secret,last_totp_counter,recovery_json,created_at,updated_at) VALUES(?,?,?,?,?,-1,?,?,?)')->execute([$id,'paint-qa@example.test','owner',password_hash('Isolated-Paints-QA-2026',PASSWORD_BCRYPT),nodenoControlEncrypt($argv[2],'JBSWY3DPEHPK3PXP',$id),'[]',$now,$now]);$seed=nodenoSupplierSeed();$p=array_values(array_filter($seed['products'],fn($p)=>$p['id']===$argv[3]))[0];if(!hash_equals($p['sourceWatchIdentity'],nodenoPaintWatchIdentity($p)))exit(3);nodenoPaintWatchObserve($db,$p,['priceMinor'=>$p['sourcePriceMinor']+1000,'currency'=>'TRY'],null,$now);"
subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',php,str(C/'private'),str(W/'storage'),prepared['products'][0]['id']],check=True,capture_output=True)
cert=E/'cert.pem';key=E/'key.pem'
if not cert.exists():subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
up,tls=port(),port();origin='https://127.0.0.1:'+str(tls);env={**os.environ,'NODENO_TEST_PUBLIC':str(P),'NODENO_TEST_HTTPS':'loopback-tls-only','NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(up),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)};log=(E/'browser-php.log').open('w',encoding='utf-8')
server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-d','extension=gd','-S','127.0.0.1:'+str(up),'-t',str(P),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
report={'passed':False,'testOnly':True,'releaseHash':proof['releaseHash'],'engines':[]}
try:
 with sync_playwright()as p:
  for engine in ['chromium','webkit']:
   executable=Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe';b=getattr(p,engine).launch(executable_path=str(executable),headless=True)
   try:
    context=b.new_context(ignore_https_errors=True,viewport={'width':390,'height':844},has_touch=True);context.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false');");page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));checks=[]
    product=prepared['products'][0];(E/'browser-progress.json').write_text(json.dumps({'engine':engine,'status':'starting'}))
    for lang in (['tr','ar']if '--ui-only'in sys.argv else['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']):
     page.goto(origin+'/?lang='+lang+'&product='+product['id'],wait_until='networkidle');expect(page.locator('#product-title')).to_be_visible();expect(page.locator('.supplier-detail-status')).to_have_count(0);assert page.locator('#product-title').inner_text()==product['name'][lang]
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),lang;checks.append({'locale':lang,'paintProduct':True,'noOverflow':True});(E/'browser-progress.json').write_text(json.dumps({'engine':engine,'locale':lang,'checks':len(checks)}))
    page.goto(origin+'/?lang=tr&product='+product['id'],wait_until='networkidle');page.screenshot(path=str(E/(engine+'-paint-mobile.png')))
    page.locator('[data-detail-add="'+product['id']+'"]').last.click();page.goto(origin+'/?lang=tr&page=cart',wait_until='networkidle');expect(page.locator('#page')).to_contain_text(product['name']['tr'])
    raw=next((v['id']for v in json.loads((C/'private/catalog.json').read_bytes())['products']if v['id']in prepared['unpaintedWoodIds']and 'masa'in v['name']['tr'].lower()),prepared['unpaintedWoodIds'][0]);page.goto(origin+'/?lang=tr&product='+raw,wait_until='networkidle');expect(page.locator('#paint-recommendations')).to_be_visible();page.locator('#paint-recommendations').scroll_into_view_if_needed();page.wait_for_function("() => Array.from(document.querySelectorAll('#paint-recommendations img')).filter(i=>{const r=i.getBoundingClientRect();return r.left<innerWidth&&r.right>0}).every(i=>i.complete&&i.naturalWidth>0)");page.screenshot(path=str(E/(engine+'-raw-paint-mobile.png')));assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.set_viewport_size({'width':1440,'height':1000});page.locator('#paint-recommendations').scroll_into_view_if_needed();page.wait_for_function("() => Array.from(document.querySelectorAll('#paint-recommendations img')).filter(i=>{const r=i.getBoundingClientRect();return r.left<innerWidth&&r.right>0}).every(i=>i.complete&&i.naturalWidth>0)");page.screenshot(path=str(E/(engine+'-raw-paint-desktop.png')))
    subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',"require $argv[1].'/control-http.php';nodenoControlDatabase($argv[2])->exec(\"UPDATE control_users SET last_totp_counter=-1 WHERE id='paint-qa'\");nodenoControlDatabase($argv[2])->exec('UPDATE supplier_price_alerts SET ack_at=NULL');",str(C/'private'),str(W/'storage')],check=True,capture_output=True);page.goto(origin+'/yonetim',wait_until='networkidle');page.get_by_role('textbox',name='E-posta',exact=True).fill('paint-qa@example.test');page.get_by_role('textbox',name='Parola',exact=True).fill('Isolated-Paints-QA-2026');page.get_by_role('button',name='Devam et',exact=True).click();page.get_by_role('textbox',name='Doğrulama veya kurtarma kodu',exact=True).fill(otp());page.get_by_role('button',name='Giriş yap',exact=True).click();expect(page.locator('#main h1')).to_be_visible()
    page.goto(origin+'/yonetim#suppliers',wait_until='networkidle');expect(page.locator('#main h1')).to_have_text('Tedarikçiler ve alışlar');page.wait_for_load_state('networkidle');page.locator('#supplier-filter').select_option(prepared['seed'][0]['supplierId']);page.locator('#supplier-search').fill(prepared['seed'][0]['code']);expect(page.locator('.supplier-product')).to_have_count(1);assert page.get_by_role('link',name='Trendyol’da satın al',exact=True).get_attribute('href')==prepared['seed'][0]['sourceUrl']
    page.get_by_role('tab',name='Fiyat kontrolleri',exact=False).click();expect(page.locator('[data-supplier-results]')).to_contain_text('önerilen satış fiyatı');page.locator('[data-supplier-results]').scroll_into_view_if_needed();page.screenshot(path=str(E/(engine+'-admin-watch-desktop.png')))
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(350);page.locator('[data-supplier-results]').scroll_into_view_if_needed();page.screenshot(path=str(E/(engine+'-admin-watch-mobile.png')));assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.get_by_role('button',name='Okundu olarak işaretle',exact=True).first.click();expect(page.locator('[data-supplier-results]')).to_contain_text('Okundu')
    if evidence.endswith('paint-completion-20261112'):
     page.get_by_role('tab',name='Boya incelemeleri',exact=True).click();page.locator('[data-review-group]').select_option('conflict');expect(page.locator('.supplier-product')).not_to_have_count(0);expect(page.locator('[data-supplier-results]')).to_contain_text('ambalaj');assert page.locator('.supplier-product small').filter(has_text='Renk / ambalaj').count()==page.locator('.supplier-product').count();page.locator('[data-supplier-results]').scroll_into_view_if_needed();page.screenshot(path=str(E/(engine+'-admin-conflicts-mobile.png')));assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.set_viewport_size({'width':1440,'height':1000});page.wait_for_timeout(350);page.locator('[data-supplier-results]').scroll_into_view_if_needed();page.screenshot(path=str(E/(engine+'-admin-conflicts-desktop.png')))
    assert not errors,errors;report['engines'].append({'engine':engine,'checks':checks,'sourceLinkExact':True,'cart':True,'paintCrossSell':True,'adminAlertAcknowledge':True,'reviewGroups':evidence.endswith('paint-completion-20261112'),'javascriptErrors':errors})
   finally:b.close()
 report['passed']=True
finally:
 proxy.terminate();proxy.wait(timeout=10);server.terminate();server.wait(timeout=10);log.close();(E/'browser-local.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
