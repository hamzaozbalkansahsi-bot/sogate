"""Local frontend QA against public read-only catalogue data; never a publish gate."""
from pathlib import Path
import json,mimetypes
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/target-locales-20261111';checks=[]
with sync_playwright()as pw:
 exe=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'
 b=pw.chromium.launch(headless=True,executable_path=str(exe))
 for locale,currency in [('de','EUR'),('az','AZN'),('kk','KZT'),('tk','USD'),('uz','USD'),('ky','USD'),('fa','USD')]:
  c=b.new_context(viewport={'width':390,'height':950},is_mobile=True,has_touch=True);p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  p.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false');window.__draftErrors=[];for(const name of ['error','unhandledrejection'])addEventListener(name,e=>{const x=e.error||e.reason;window.__draftErrors.push({message:x?.message||'',source:x?.translationSource||''})})")
  def route(request):
   u=urlparse(request.request.url);path=unquote(u.path);f=(R/'web'/path.lstrip('/')).resolve()
   if request.request.method not in ['GET','HEAD']:request.abort('blockedbyclient');return
   if path=='/':request.fulfill(body=(R/'web/index.html').read_bytes(),content_type='text/html');return
   if f.is_relative_to((R/'web').resolve())and f.is_file()and(f.suffix in ['.js','.css']or path.startswith('/locales/')):request.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0]or'application/octet-stream');return
   request.continue_()
  p.route('https://nodenohome.com/**',route)
  p.goto('https://nodenohome.com/?lang='+locale,wait_until='networkidle');p.wait_for_timeout(1500)
  failures=p.evaluate('window.__draftErrors');(E/('draft-errors-'+locale+'.json')).write_text(json.dumps({'errors':errors,'details':failures},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  if errors or failures:
   print(json.dumps({'locale':locale,'errors':errors,'details':failures},ensure_ascii=False),flush=True);c.close();continue
  expect(p.locator('#language')).to_have_value(locale);expect(p.locator('#display-currency')).to_have_value(currency,timeout=20000)
  assert p.locator('html').get_attribute('dir')==('rtl'if locale=='fa'else'ltr')
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  p.screenshot(path=str(E/('draft-home-mobile-'+locale+'.png')));checks.append({'locale':locale,'currency':currency,'noRuntimeErrors':True,'noOverflow':True});c.close();print(json.dumps({'draftPassed':locale}),flush=True)
 b.close()
(E/'frontend-draft.json').write_text(json.dumps({'passed':len(checks)==7,'testOnly':True,'frontendOnly':True,'productionAcceptance':False,'checks':checks,'realCharges':0},indent=2)+'\n')
if len(checks)!=7:raise SystemExit(1)
