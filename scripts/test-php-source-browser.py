#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-source-browser.py
# Açıklama   : Gerçek kaynak kataloglarını MFA ile yalnız /test incelemesine aktarır ve doğrular.
import argparse,base64,hashlib,hmac,json,os,struct,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--remote',action='store_true');parser.add_argument('--import-catalogs',action='store_true');parser.add_argument('--catalog-root',type=Path);args=parser.parse_args()
base='https://sexogate.com/test' if args.remote else 'http://127.0.0.1:3183/test'
access=json.loads((root/('.local/php-stage-access.json' if args.remote else '.local/php-access.json')).read_text(encoding='utf8'))
source_report=json.loads((root/'docs/php-source-catalog-report.json').read_text(encoding='utf8'))
expected={r['vendor']:(r['products'],r['categories']) for r in source_report['suppliers']}
def otp(secret):
 key=base64.b32decode(secret+'='*((8-len(secret)%8)%8));digest=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15
 return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)

def main():
 results=[];folder=root/('docs/screenshots/php-source-remote' if args.remote else 'docs/screenshots/php-source-local');folder.mkdir(parents=True,exist_ok=True)
 axe=(root/'node_modules/axe-core/axe.min.js').read_text(encoding='utf8')
 with sync_playwright() as p:
  for engine in ['chromium','webkit']:
   browser=getattr(p,engine).launch(headless=True);context=browser.new_context(viewport={'width':1440 if engine=='chromium' else 390,'height':900});page=context.new_page();page.set_default_timeout(20000);page.set_default_navigation_timeout(60000)
   try:
    page.goto(base+'/');page.wait_for_load_state('networkidle');page.locator('#age-accept').click();page.goto(base+'/yonetim/giris')
    gate=page.locator('form[action$="/_access"]')
    if gate.count():
     gate.locator('[name=username]').fill(access['stageUser']);gate.locator('[name=password]').fill(access['stagePassword'])
     with page.expect_navigation(wait_until='networkidle'):gate.locator('button').click()
    login=page.locator('form[data-api="/api/auth/login"]');login.locator('[name=email]').fill(access['email']);login.locator('[name=password]').fill(access['password']);login.locator('button').click();mfa=page.locator('form[data-api="/api/auth/mfa/login"]');mfa.wait_for()
    time.sleep(30.5-time.time()%30);mfa.locator('[name=code]').fill(otp(access['totpSecret']));mfa.locator('button').click();page.wait_for_url('**/yonetim')
    if args.import_catalogs and engine=='chromium':
     if not args.catalog_root:raise ValueError('CATALOG_ROOT_REQUIRED')
     for vendor in expected:
      file=args.catalog_root/vendor/(vendor+'.ndjson.gz');assert file.is_file() and file.stat().st_size<2000000
      page.goto(base+'/yonetim/tedarikci-katalogu');form=page.locator('form[action$="/api/admin/source-upload"]');form.locator('[name=vendor]').select_option(vendor);form.locator('[name=file]').set_input_files(str(file));form.locator('[name=key]').evaluate('(node,value)=>{node.value=value;}','source-ui:'+vendor+':'+hashlib.sha256(file.read_bytes()).hexdigest())
      with page.expect_navigation(wait_until='networkidle') as nav:form.locator('button').click()
      assert nav.value.status==200,'Source import did not return a successful review page'
    page.goto(base+'/yonetim/tedarikci-katalogu');response=context.request.get(base+'/api/admin/source-catalog');assert response.status==200;rows=response.json()['rows'];assert len(rows)==3
    for row in rows:
     assert (int(row['product_count']),int(row['category_count']))==expected[row['vendor']]
     assert int(row['parsed_count'])==sum(expected[row['vendor']]) and int(row['access_required_count'])==0
    page.screenshot(path=str(folder/(engine+'-catalog-batches.png')),full_page=True)
    for row in rows:
     page.goto(base+'/yonetim/tedarikci-katalogu/'+row['id']+'?kind=category');assert page.locator('tbody tr').count()>0;page.locator('tbody a').first.click();page.locator('.source-detail h2').wait_for();assert not page.locator('form[data-api="/api/admin/source-catalog/draft"]').count()
    row=next(r for r in rows if r['vendor']=='liona');page.goto(base+'/yonetim/tedarikci-katalogu/'+row['id']+'?kind=product');page.locator('tbody a').first.click();page.locator('form[data-api="/api/admin/source-catalog/draft"]').wait_for();page.screenshot(path=str(folder/(engine+'-product-review.png')),full_page=True)
    for path in ['/yonetim/tedarikci-katalogu','/yonetim/kategoriler','/yonetim/gorseller']:
     response=page.goto(base+path);assert response.status==200;page.wait_for_load_state('networkidle');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),path
     page.evaluate(axe);issues=page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))");assert not issues,(path,issues)
    results.append({'engine':engine,'actualProducts':sum(v[0] for v in expected.values()),'actualCategories':sum(v[1] for v in expected.values()),'allMetadataParsed':True,'privateReview':True,'adminPages':3,'axeViolations':0})
   finally:context.close();browser.close()
 (root/('.local/php-source-browser-remote.json' if args.remote else '.local/php-source-browser-local.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results))

try:main()
except Exception as e:
 message=str(e)
 for secret in [access.get(k) for k in ['password','totpSecret','stagePassword']]+access.get('recoveryCodes',[]):
  if secret:message=message.replace(secret,'[redacted]')
 print(type(e).__name__+': '+message[:1800],file=sys.stderr);sys.exit(1)
