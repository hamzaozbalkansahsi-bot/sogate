"""Packaged legal pages, preferences and membership UI in isolated local storage."""
from pathlib import Path
from contextlib import ExitStack
import hashlib,json,os,shutil,socket,subprocess,tempfile,time,urllib.request
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/legal-20261110';proof=json.loads((E/'release-preparation.json').read_bytes());SOURCE=R/proof['release'];PHP=R/'artifacts/runtime-php/php.exe';CHROME=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'
with tempfile.TemporaryDirectory(prefix='nodeno-legal-browser-')as temp,ExitStack()as stack:
 root=Path(temp);release=root/'release';shutil.copytree(SOURCE,release,copy_function=os.link);storage=root/'data';storage.mkdir()
 def pq(value):return "'"+str(value).replace('\\','\\\\').replace("'","\\'")+"'"
 (release/'nodeno-runtime.php').write_text('<?php return [\'privateRoot\'=>'+pq(release/'private')+',\'storageRoot\'=>'+pq(storage)+'];',encoding='utf8')
 seed="require "+pq(release/'private/payment-admin.php')+";$root=$argv[1];$db=nodenoControlDatabase($root);$seller=['name'=>'PTYS Technologies L.L.C.','address'=>'30 N Gould St Ste N, Sheridan, WY 82801, United States','email'=>'info@ptys.com.tr','termsVersion'=>'2026-11-10.3'];foreach(['tr','en','ru','ar']as $lang){$doc=json_decode(file_get_contents($argv[2].'/payment-documents.'.$lang.'.json'),true);$seller['terms'][$lang]=implode(\"\\n\\n\",$doc['terms']);$seller['returns'][$lang]=implode(\"\\n\\n\",$doc['returns']);}nodenoControlSetSetting($db,'payment:stripe',['version'=>1,'enabled'=>false,'mode'=>'test','seller'=>$seller]);"
 subprocess.run([str(PHP),'-r',seed,str(storage),str(R/'data/legal')],check=True,capture_output=True)
 with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 origin='http://127.0.0.1:'+str(port);log=stack.enter_context(open(root/'php.log','w',encoding='utf8'));server=subprocess.Popen([str(PHP),'-S','127.0.0.1:'+str(port),'-t',str(release/'public'),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(release/'public')},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 stack.callback(lambda:server.wait(timeout=8));stack.callback(server.terminate)
 for _ in range(100):
  try:
   with urllib.request.urlopen(origin+'/legal?lang=tr',timeout=1)as response:assert response.status==200
   break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('legal_test_server_unavailable')
 checks=[]
 with sync_playwright()as pw:
  browser=pw.chromium.launch(headless=True,executable_path=str(CHROME))
  for locale,width in [('tr',1440),('en',390),('ru',390),('ar',390)]:
   context=browser.new_context(viewport={'width':width,'height':920},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for doc in ['','kvkk','privacy','cookies','membership','data-request','wholesale','sales','pre-information','returns','seller']:
    response=page.goto(origin+'/legal'+('/'+doc if doc else'')+'?lang='+locale,wait_until='networkidle');assert response.status==200;expect(page.locator('h1')).to_be_visible();assert page.locator('html').get_attribute('dir')==('rtl'if locale=='ar'else'ltr');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   page.goto(origin+'/legal/kvkk?lang='+locale,wait_until='networkidle');page.screenshot(path=str(E/('legal-'+locale+'-'+str(width)+'.png')),full_page=True)
   with page.expect_download()as pending:page.locator('.legal-actions a[download]').click()
   download=pending.value;file=root/('legal-'+locale+'.html');download.save_as(file);body=file.read_text(encoding='utf8');assert '<style>'in body and'<script'not in body
   page.goto(origin+'/legal/cookies?lang='+locale,wait_until='networkidle');page.evaluate("localStorage.setItem('nodeno.recent.v1','[\"fixture\"]');localStorage.setItem('nodeno.searches.v1','[\"fixture\"]')");page.locator('[data-legal-preferences]').click();page.locator('.legal-preference-choice').last.click();expect(page.locator('.legal-feedback button')).to_have_count(0);assert page.evaluate("localStorage.getItem('nodeno.recent.v1')===null&&localStorage.getItem('nodeno.searches.v1')===null")
   page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1')");page.goto(origin+'/?page=register&lang='+locale,wait_until='networkidle');expect(page.locator('#register-form')).to_be_visible();expect(page.locator('#register-form')).to_have_attribute('data-membership-version','2026-11-10.3');expect(page.locator('#register-form [name=membership]')).not_to_be_checked();expect(page.locator('#register-form [type=submit]')).to_be_enabled();assert page.locator('#register-form a[href*="/legal/kvkk"]').count()>0
   assert not errors,errors;checks.append({'locale':locale,'width':width,'documents':11,'noOverflow':True,'downloadSelfContained':True,'optionalHistoryCleared':True,'membershipHashLoaded':True,'noRuntimeErrors':True});context.close()
  browser.close()
 (E/'browser-local.json').write_text(json.dumps({'passed':True,'releaseHash':proof['releaseHash'],'checks':checks,'productionWrites':0},indent=2)+'\n')
 print(json.dumps({'passed':True,'locales':len(checks),'legalPageChecks':44,'productionWrites':0}))
