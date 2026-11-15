#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-languages.py
# Açıklama   : Kataloglu vitrinde dil seçimini, sunucu/istemci metaverisini ve RTL yönünü doğrular.
import argparse,html,json,os,re,ssl,urllib.error,urllib.request
from urllib.parse import urlsplit
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3186').rstrip('/')
scope = os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','local')
assert re.fullmatch('[a-z-]+',scope)
assert BASE in ['https://127.0.0.1:3186','https://127.0.0.1:3188/test','https://sexogate.com/test'] or re.fullmatch('https://(?:sexogate.com|127.0.0.1:3188)/test/native-preview-[a-f0-9]{16}',BASE)
results = []
store_copy=json.loads((ROOT/'native-store/theme/store-copy.json').read_text('utf8'))
parser = argparse.ArgumentParser()
parser.add_argument('--locales', nargs='+', default=['tr', 'en', 'ru', 'ar', 'de', 'az', 'kk', 'tk', 'uz', 'ky', 'fa'])
args = parser.parse_args()
request = urllib.request.Request(BASE + '/api/account/state', data=b'{}', headers={'Content-Type': 'application/json', 'Origin': BASE}, method='PUT')
try:
    urllib.request.urlopen(request, context=ssl._create_unverified_context() if BASE.startswith('https://127.0.0.1') else ssl.create_default_context(), timeout=15)
    raise AssertionError('Unauthenticated state mutation was accepted')
except urllib.error.HTTPError as error:
    assert error.code in [401, 403], error.code
    print(json.dumps({'unauthenticatedPutStatus': error.code, 'proxyForwardsPut': True}), flush=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'))
    context.add_init_script("window.__nativeTranslationErrors=[];for(const type of ['error','unhandledrejection'])addEventListener(type,e=>{const error=e.error||e.reason;if(error?.translationSource)window.__nativeTranslationErrors.push(error.translationSource);});")
    page = context.new_page()
    errors = []
    pending = set()
    failed = []
    page.on('request', lambda request: pending.add(request))
    page.on('requestfinished', lambda request: pending.discard(request))
    page.on('requestfailed', lambda request: (pending.discard(request), failed.append({'path':urlsplit(request.url).path,'error':request.failure})))
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        for locale in args.locales:
            response = page.goto(BASE + '/?page=categories&lang=' + locale)
            assert response.status == 200, (locale, response.status)
            page.wait_for_load_state('networkidle')
            assert page.locator('#language').input_value() == locale, locale
            expected = 'rtl' if locale in ['ar', 'fa'] else 'ltr'
            assert page.locator('html').get_attribute('dir') == expected, locale
            document=context.request.get(BASE+'/?lang='+locale)
            assert document.status==200,('metadata',locale,document.status)
            title=re.search(r'<title>(.*?)</title>',document.text()).group(1)
            assert store_copy[locale]['slogan']in html.unescape(title),('adult-metadata',locale,title)
            page.goto(BASE+'/?lang='+locale);page.wait_for_load_state('networkidle')
            assert store_copy[locale]['slogan']in page.title(),('client-adult-metadata',locale,page.title())
            results.append({'locale': locale, 'status': response.status, 'selected': True, 'direction': expected,'adultMetadata':True,'clientAdultMetadata':True})
            print(json.dumps(results[-1]), flush=True)
            missing = page.evaluate('() => window.__nativeTranslationErrors')
            if missing: print(json.dumps({'missingTranslation': locale, 'source': missing}), flush=True)
        assert not errors, errors
    except Exception:
        try:
            print(json.dumps({'diagnostic':True,'locale':locale,'path':urlsplit(page.url).path,'pending':[{'path':urlsplit(request.url).path,'type':request.resource_type}for request in pending],'failed':failed[-12:],'pageErrors':errors,'ready':page.evaluate('()=>({document:document.readyState,language:document.querySelector("#language")?.value,currency:!!document.querySelector("#currency")})')},ensure_ascii=False),flush=True)
        except Exception: print('Language diagnostic unavailable',flush=True)
        raise
    finally:
        context.close()
        browser.close()
request=urllib.request.Request(BASE+'/api/catalog');observed=json.load(urllib.request.urlopen(request,context=ssl._create_unverified_context()if BASE.startswith('https://127.0.0.1')else ssl.create_default_context(),timeout=30));catalog=observed.get('catalog',observed)
report = {'locales': results, 'pageErrors': len(errors), 'catalogProductsObserved':len(catalog['products'])}
(ROOT / ('.local/native-languages'+('' if scope=='local' else '-'+scope)+'.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(report, ensure_ascii=False))
