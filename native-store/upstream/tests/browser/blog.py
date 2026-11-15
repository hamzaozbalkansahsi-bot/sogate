"""Real PHP and Playwright acceptance for the isolated blog release or live HTTPS."""
from pathlib import Path
import argparse,json,os,socket,subprocess,time,urllib.request,secrets,hashlib,base64,hmac,struct
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/blog-20261112'
def otp(secret):
 digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15
 return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def main():
 p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--preview',action='store_true');args=p.parse_args();proof=json.loads((E/('preview-release.json'if args.preview else'release.json')).read_bytes());report={'passed':False,'live':args.live,'releaseHash':proof['releaseHash'],'checks':[]};server=None;proxy=None;log=None
 if args.live:base='https://nodenohome.com';candidate=R/proof['release']
 else:
  candidate=R/proof['release'];Q=E/('qa-'+proof['releaseHash'][:12]+'-'+secrets.token_hex(4));P=Q/'public';P.mkdir(parents=True,exist_ok=True);storage=Q/'storage';storage.mkdir(exist_ok=True)
  for f in(candidate/'public').rglob('*'):
   if f.is_file():
    target=P/f.relative_to(candidate/'public');target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():os.link(f,target)
  config="<?php return ['privateRoot'=>"+repr(str(candidate/'private').replace('\\','/'))+",'storageRoot'=>"+repr(str(storage).replace('\\','/'))+",'mediaRoot'=>"+repr(str(R/'artifacts/social-engine-20261112/preview/media').replace('\\','/'))+"];"
  (Q/'nodeno-runtime.php').write_text(config,encoding='utf8')
  seed="<?php require "+repr(str(candidate/'private/blog-worker.php').replace('\\','/'))+"; echo json_encode(nodenoBlogTick("+repr(str(storage).replace('\\','/'))+","+repr(str(candidate/'private').replace('\\','/'))+","+repr(str(P).replace('\\','/'))+",strtotime('2026-11-12T20:00:00+03:00')));"
  (Q/'seed.php').write_text(seed,encoding='utf8');result=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),str(Q/'seed.php')],capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
  assert json.loads(result.stdout)['status']=='ok',result.stdout
  token=secrets.token_hex(32);email='blog-qa@example.test';(storage/'admin-bootstrap.json').write_text(json.dumps({'schema':1,'email':email,'tokenHash':hashlib.sha256(token.encode()).hexdigest(),'expiresAt':int(time.time())+1800}))
  with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  env={**os.environ,'NODENO_TEST_PUBLIC':str(P),'NODENO_TEST_HTTPS':'loopback-tls-only'};log=(Q/'php.log').open('w',encoding='utf8');server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-S','127.0.0.1:'+str(port),'-t',str(P),str(R/'hosting/dev-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  with socket.socket()as s:s.bind(('127.0.0.1',0));tls=s.getsockname()[1]
  cert=Q/'cert.pem';key=Q/'key.pem';subprocess.run(['C:/Program Files/Git/usr/bin/openssl.exe','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','2','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  proxy=subprocess.Popen(['node',str(R/'tests/fixtures/control-proxy.mjs')],env={**os.environ,'NODENO_QA_PORT':str(tls),'NODENO_QA_UPSTREAM':str(port),'NODENO_QA_KEY':str(key),'NODENO_QA_CERT':str(cert)},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);base='https://127.0.0.1:'+str(tls)
 try:
  with sync_playwright()as p:
   executable=Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe';browser=p.chromium.launch(executable_path=str(executable),headless=True);context=browser.new_context(ignore_https_errors=True,timezone_id='America/Los_Angeles');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for attempt in range(40):
    try:page.goto(base+'/blog',wait_until='networkidle');break
    except Exception:time.sleep(.2)
   for width in[390,1440]:
    page.set_viewport_size({'width':width,'height':950})
    for lang in['tr','en','ru','ar']:
     page.goto(base+'/blog?lang='+lang,wait_until='networkidle');assert page.locator('h1').is_visible();assert page.locator('html').get_attribute('dir')==('rtl'if lang=='ar'else'ltr');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert page.locator('.blog-logo img').evaluate('(e)=>e.complete&&e.naturalWidth>0');page.screenshot(path=str(E/(f'blog-{width}-{lang}-'+('live'if args.live else'local')+'.png')),full_page=True)
     cards=page.locator('.blog-card');count=cards.count();report['checks'].append({'page':'list','width':width,'locale':lang,'cards':count,'noOverflow':True})
     if count:
      cards.first.locator('h2 a').click();page.wait_for_load_state('networkidle');assert page.locator('.blog-prose section').count()>=4;assert page.locator('.blog-article-image img').evaluate('(e)=>e.complete&&e.naturalWidth===1200');assert page.locator('script[type="application/ld+json"]').count()==1;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(E/(f'article-{width}-{lang}-'+('live'if args.live else'local')+'.png')),full_page=True);report['checks'].append({'page':'article','width':width,'locale':lang,'imageVerified':True})
     elif not args.preview:raise AssertionError('published_translation_missing_'+lang)
     page.goto(base+'/blog?tool=paint&lang='+lang,wait_until='networkidle');output=page.locator('form[data-blog-tool="paint"] output');assert '7' in output.inner_text()or '٧' in output.inner_text();page.locator('select[name="basis"]').select_option('system');assert '3' in output.inner_text()or '٣' in output.inner_text();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');report['checks'].append({'page':'paint-tool','width':width,'locale':lang,'coverageBasisWorks':True})
     page.goto(base+'/blog?tool=surface&lang='+lang,wait_until='networkidle');surface=page.locator('[data-blog-surface]');assert surface.is_visible();surface.locator('[name=material]').select_option('mdf');surface.locator('[name=condition]').select_option('damp');assert surface.locator('[data-surface-steps] li').count()>1;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');report['checks'].append({'page':'surface-tool','width':width,'locale':lang,'planRendered':True})
    page.goto(base+'/blog?tool=palette',wait_until='networkidle');assert page.locator('.blog-swatch').count()==4
    page.goto(base+'/blog?q=zzzz-does-not-exist',wait_until='networkidle');assert page.locator('.blog-empty').is_visible();assert page.locator('meta[name="robots"]').get_attribute('content')=='noindex,follow'
    response=page.goto(base+'/blog/future-draft-does-not-exist',wait_until='networkidle');assert response.status==404
    page.goto(base+'/yonetim/blog',wait_until='networkidle');assert page.locator('#blog-admin-login').is_visible();assert page.locator('#blog-admin-content').is_hidden();report['checks'].append({'page':'admin-anonymous','width':width,'draftDataHidden':True})
   bank=json.loads((candidate/'private/blog-bank.json').read_bytes());draft=bank['articles'][-1];assert context.request.get(base+'/blog/'+draft['slug']).status==404
   for image in[draft['image'],*[x['image']for x in draft['locales'].values()]]:assert context.request.get(base+image['url']).status==404
   assert context.request.get(base+'/api/admin/blog/articles/'+draft['id']+'/image/tr').status==401;report['checks'].append({'futureArticleAndFourImages':404,'privatePreviewAnonymous':401})
   dates=page.evaluate("""async()=>{const m=await import('/date-time.js?v=20261112-r1');return ['TR','US','GB','DE','BR'].map(country=>({country,date:m.formatDate('2026-11-12',{country}),time:m.formatDateTime('2026-11-12T21:05:00Z',{country})}));}""");assert dates[0]['time']=='13/11/2026 00:05';assert [x['date']for x in dates]==['12/11/2026','11/12/2026','12/11/2026','12.11.2026','12/11/2026'];report['checks'].append({'countryDates':dates})
   if not args.live:
    page.goto(base+'/yonetim',wait_until='networkidle');page.locator('[name=email]').fill(email);page.locator('[name=password]').fill('Nodeno-Blog-QA-Only-2026');page.locator('[name=token]').fill(token);page.get_by_role('button',name='Doğrulamayı kur',exact=True).click();expect(page.locator('.secret')).to_be_visible();secret=page.locator('.secret').inner_text();page.locator('[name=code]').fill(otp(secret));page.get_by_role('button',name='Kurulumu tamamla',exact=True).click();page.get_by_role('button',name='Yönetime geç',exact=True).click();expect(page.locator('#main h1')).to_be_visible()
    for width in[390,1440]:
     page.set_viewport_size({'width':width,'height':950});page.goto(base+'/yonetim/blog',wait_until='networkidle');assert page.locator('#blog-admin-content').is_visible();assert '124 gün' in page.locator('#blog-admin-capacity').inner_text();page.screenshot(path=str(E/f'admin-{width}-local.png'),full_page=True);page.locator('[data-preview]').last.click();expect(page.locator('#blog-admin-preview')).to_be_visible()
     for lang in['tr','en','ru','ar']:
      page.locator('#blog-preview-locale').select_option(lang);image=page.locator('#blog-preview-body>img');expect(image).to_be_visible();page.wait_for_function('()=>{const e=document.querySelector("#blog-preview-body>img");return e&&e.complete&&e.naturalWidth===1200}');assert page.locator('#blog-preview-body .blog-checklist li').count()>=3;assert page.locator('#blog-preview-body').get_attribute('dir')==('rtl'if lang=='ar'else'ltr')
     page.screenshot(path=str(E/f'admin-preview-{width}-ar-local.png'));page.locator('#blog-preview-close').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');report['checks'].append({'authenticatedPreviewFourLanguages':True,'width':width,'capacityVisible':True})
   assert not errors,errors;browser.close()
  report['passed']=True
 finally:
  if server:server.terminate();server.wait(timeout=10)
  if proxy:proxy.terminate();proxy.wait(timeout=10)
  if log:log.close()
  (E/('browser-live.json'if args.live else'browser-preview.json'if args.preview else'browser-local.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'live':args.live,'releaseHash':report['releaseHash']}))
if __name__=='__main__':main()
