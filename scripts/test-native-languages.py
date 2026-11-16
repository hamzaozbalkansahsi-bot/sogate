#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-languages.py
# Açıklama   : Kataloglu vitrinde dil seçimini, sunucu/istemci metaverisini ve RTL yönünü doğrular.
import argparse,hashlib,html,json,os,re,ssl,sys,time,urllib.error,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_test_errors import safe_error
from native_browser_ready import NativePageReadiness
sys.excepthook=safe_error
ROOT=Path(__file__).resolve().parent.parent
BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3186').rstrip('/')
scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','local')
assert re.fullmatch('[a-z-]+',scope)
assert BASE in ['https://127.0.0.1:3186','https://127.0.0.1:3188/test','https://sexogate.com/test']or re.fullmatch(r'https://(?:sexogate.com|127.0.0.1:3188)/test/native-preview-[a-f0-9]{16}',BASE)
parser=argparse.ArgumentParser();parser.add_argument('--locales',nargs='+',default=['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']);parser.add_argument('--retry-failed',action='store_true');args=parser.parse_args()
path=ROOT/('.local/native-languages'+(''if scope=='local'else'-'+scope)+'.json')
script_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
copy=json.loads((ROOT/'native-store/theme/store-copy.json').read_text('utf8'))
tls=ssl._create_unverified_context()if BASE.startswith('https://127.')else ssl.create_default_context()
def read_status():
 for attempt in range(2):
  try:
   with urllib.request.urlopen(BASE+('/api/deployment-status'if'/test'in BASE else'/api/catalog'),context=tls,timeout=15)as response:data=json.load(response)
   if'/test'in BASE:
    assert data['database']is True and data['checkoutEnabled']is False and data['products']>0
    return data
   return {'release':'unmounted-original','products':len(data.get('catalog',data)['products'])}
  except urllib.error.HTTPError:raise
  except OSError:
   if attempt:raise
initial=read_status()
report={'base':BASE,'scope':scope,'release':initial['release'],'scriptSha256':script_hash,'locales':[],'clientSwitches':[],'failedAttempts':[],'attempts':{},'pageErrors':0,'finalized':False,'readiness':'critical_requests_and_rendered_ui','execution':'isolated_locale_entries_and_client_switches','optionalFxObserved':False}
if args.retry_failed:
 previous=json.loads(path.read_text('utf8'))
 assert all(previous.get(key)==report[key]for key in ['base','scope','release','scriptSha256']),'STALE_LANGUAGE_CHECKPOINT'
 report=previous;report['finalized']=False
assert all(row['status']==200 and row['selected']and row['adultMetadata']and row['clientAdultMetadata']and row['catalogUiReady']for row in report['locales'])
def save():path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
request=urllib.request.Request(BASE+'/api/account/state',data=b'{}',headers={'Content-Type':'application/json','Origin':BASE},method='PUT')
try:
 urllib.request.urlopen(request,context=tls,timeout=15);raise AssertionError('Unauthenticated state mutation accepted')
except urllib.error.HTTPError as error:
 assert error.code in [401,403];print(json.dumps({'unauthenticatedPutStatus':error.code,'proxyForwardsPut':True}),flush=True)
save()
def entry(page,ready,locale):
 response=page.goto(BASE+'/?page=categories&lang='+locale);assert response.status==200
 ready.wait();assert page.locator('#root-links a').count()>0
 assert page.locator('#language').input_value()==locale
 expected='rtl'if locale in ['ar','fa']else'ltr'
 assert page.locator('html').get_attribute('dir')==expected
 document=page.context.request.get(BASE+'/?lang='+locale,max_retries=1);assert document.status==200
 title=re.search(r'<title>(.*?)</title>',document.text()).group(1);assert copy[locale]['slogan']in html.unescape(title)
 page.goto(BASE+'/?lang='+locale);ready.wait();assert page.locator('#root-links a').count()>0
 assert copy[locale]['slogan']in page.title()
 missing=page.evaluate('()=>window.__nativeTranslationErrors');assert not missing,('missing-translation',locale)
 return {'locale':locale,'status':200,'selected':True,'direction':expected,'adultMetadata':True,'clientAdultMetadata':True,'catalogUiReady':True}
def switch(page,ready):
 page.goto(BASE+'/?lang=tr');ready.wait()
 gate=page.locator('#sexogate-age-gate')
 if gate.count():gate.locator('.sexogate-age-accept').click();gate.wait_for(state='detached')
 button=page.get_by_role('button',name='Yalnız gerekli',exact=True)
 if button.count()and button.first.is_visible():button.first.click()
 rows=[]
 for locale in ['en','de','ar']:
  page.locator('#language').select_option(locale);ready.wait()
  page.wait_for_function('(value)=>document.documentElement.lang===value.lang&&document.title.includes(value.slogan)',arg={'lang':locale,'slogan':copy[locale]['slogan']})
  assert page.locator('#root-links a').count()>0 and page.locator('#language').input_value()==locale
  assert page.locator('html').get_attribute('dir')==('rtl'if locale=='ar'else'ltr')
  rows.append({'locale':locale,'selected':True,'clientMetadata':True,'catalogUiReady':True})
 return rows
with sync_playwright()as p:
 browser=p.chromium.launch()
 cases=[locale for locale in args.locales if locale not in {row['locale']for row in report['locales']}]
 if not report['clientSwitches']:cases.append('client-switches')
 for case in cases:
  report['attempts'][case]=report['attempts'].get(case,0)+1
  context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.'))
  context.add_init_script("window.__nativeTranslationErrors=[];for(const type of ['error','unhandledrejection'])addEventListener(type,e=>{const error=e.error||e.reason;if(error?.translationSource)window.__nativeTranslationErrors.push(error.translationSource);});")
  page=context.new_page();page.set_default_navigation_timeout(60000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  ready=NativePageReadiness(page,BASE,45000)
  try:
   if case=='client-switches':row=switch(page,ready)
   else:row=entry(page,ready,case)
   ready.wait();assert not errors,errors
   if case=='client-switches':report['clientSwitches']=row
   else:report['locales'].append(row)
   print(json.dumps({'passed':case,'result':row},ensure_ascii=False),flush=True)
  except Exception as error:
   report['failedAttempts'].append({'case':case,'attempt':report['attempts'][case],'errorClass':type(error).__name__})
   print(json.dumps({'failed':case,'errorClass':type(error).__name__}),flush=True)
  finally:
   report['optionalFxObserved']|=ready.optional_observed;context.close();save()
 browser.close()
if {row['locale']for row in report['locales']}!=set(args.locales)or len(report['clientSwitches'])!=3:raise SystemExit(1)
final=read_status();assert final['release']==initial['release'],'RELEASE_CHANGED_DURING_TEST'
report.update(finalized=True,catalogProductsObserved=final['products'],catalogCountSource='deployment-status'if'/test'in BASE else'catalog');save();print(json.dumps(report,ensure_ascii=False),flush=True)
