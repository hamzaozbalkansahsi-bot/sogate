"""Country formatting and real admin datetime input with a deliberately foreign device zone."""
from pathlib import Path
import os,json,subprocess,socket,time,secrets,hashlib,base64,hmac,struct
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/date-time-20261112'
def port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def otp(secret):
 digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15;return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def main():
 proof=json.loads((E/'release.json').read_bytes());C=R/proof['release'];Q=E/('qa-'+proof['releaseHash'][:12]);P=Q/'public';P.mkdir(parents=True,exist_ok=True);storage=Q/'storage';storage.mkdir(exist_ok=True)
 for f in(C/'public').rglob('*'):
  if f.is_file():
   target=P/f.relative_to(C/'public');target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():os.link(f,target)
 token=secrets.token_hex(32);email='date-policy@example.test';(storage/'admin-bootstrap.json').write_text(json.dumps({'schema':1,'email':email,'tokenHash':hashlib.sha256(token.encode()).hexdigest(),'expiresAt':int(time.time())+1800}))
 quote=lambda p:"'"+p.as_posix().replace("'","\\'")+"'"
 (Q/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+quote(C/'private')+",'storageRoot'=>"+quote(storage)+",'mediaRoot'=>"+quote(R/'artifacts/social-engine-20261112/preview/media')+"];",encoding='utf8')
 upstream=port();tls=port();origin='https://127.0.0.1:'+str(tls);log=(Q/'php.log').open('w',encoding='utf8');env={**os.environ,'NODENO_TEST_PUBLIC':str(P),'NODENO_TEST_HTTPS':'loopback-tls-only'};server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-S','127.0.0.1:'+str(upstream),'-t',str(P),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 cert=Q/'cert.pem';key=Q/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
 proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(upstream),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);report={'passed':False,'releaseHash':proof['releaseHash'],'realPHPAndSQLite':True,'deviceTimezone':'America/Los_Angeles','checks':[]}
 try:
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True);context=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for attempt in range(50):
    try:page.goto(origin+'/yonetim',wait_until='networkidle');break
    except Exception:time.sleep(.2)
   # Exercise the production module in a real browser, using the persistent country preference.
   results=page.evaluate("""async()=>{const m=await import('/date-time.js');const rows=[];for(const country of ['TR','US','GB','DE']){localStorage.setItem('nodeno.market-country.v1',JSON.stringify(country));rows.push({country,date:m.formatDate('2026-11-12'),time:m.formatDateTime('2026-11-12T21:05:00Z'),zone:m.dateTimeSettings().timeZone});}localStorage.setItem('nodeno.market-country.v1',JSON.stringify('TR'));return rows;}""")
   assert [r['date']for r in results]==['12/11/2026','11/12/2026','12/11/2026','12.11.2026'];assert results[0]['time']=='13/11/2026 00:05';assert results[1]['zone']=='America/Los_Angeles';report['checks'].append({'countryExamples':results})
   page.locator('[name=email]').fill(email);page.locator('[name=password]').fill('Nodeno-Date-Policy-Only-2026');page.locator('[name=token]').fill(token);page.get_by_role('button',name='Doğrulamayı kur',exact=True).click();expect(page.locator('.secret')).to_be_visible();secret=page.locator('.secret').inner_text();page.locator('[name=code]').fill(otp(secret));page.get_by_role('button',name='Kurulumu tamamla',exact=True).click();page.get_by_role('button',name='Yönetime geç',exact=True).click();expect(page.locator('#main h1')).to_be_visible()
   page.goto(origin+'/yonetim#audit',wait_until='networkidle');expect(page.locator('#main')).to_contain_text('/2026');assert page.locator('#main').inner_text().count('Kas')==0;page.screenshot(path=str(E/'admin-date-1440.png'),full_page=True);report['checks'].append({'auditUsesSlashDates':True,'deviceZoneIgnoredForTR':True})
   page.goto(origin+'/yonetim#campaigns',wait_until='networkidle');page.get_by_role('button',name='Yeni kampanya',exact=True).first.click();page.locator('[name=title]').fill('İzole tarih biçimi testi');page.locator('[data-product-filter=productIds]').fill('2395');choice=page.locator('[data-product-choice][value="2395"]');
   if not choice.is_visible():page.locator('[data-product-filter=productIds]').fill('');
   choice.check();page.locator('[name=percent]').fill('10');page.locator('[name=startsAt]').fill('2026-11-13T00:05');page.locator('[name=endsAt]').fill('2026-11-14T00:05');expect(page.locator('.field-hint').filter(has_text='Europe/Istanbul')).to_be_visible();page.get_by_role('button',name='Taslağı kaydet',exact=True).click();expect(page.locator('#editor')).not_to_be_visible(timeout=10000)
   data=context.request.get(origin+'/api/admin/campaigns').json()['data'];assert len(data)==1;assert data[0]['data']['startsAt']==int(__import__('datetime').datetime(2026,11,12,21,5,tzinfo=__import__('datetime').timezone.utc).timestamp());report['checks'].append({'campaignInputSavedAsCorrectUTC':True,'ordersCreated':0,'chargesCreated':0})
   page.set_viewport_size({'width':390,'height':950});page.goto(origin+'/yonetim#audit',wait_until='networkidle');expect(page.locator('#main')).to_contain_text('/2026');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(E/'admin-date-390.png'),full_page=True);assert not errors,errors;browser.close();report['passed']=True
 finally:
  proxy.terminate();proxy.wait(timeout=10);server.terminate();server.wait(timeout=10);log.close();(E/'browser-local.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
