#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-languages.py
# Açıklama   : Doğrudan kopyada dil seçimini, boş katalog yanıtını ve RTL yönünü doğrular.
import argparse,json,ssl,urllib.error,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://127.0.0.1:3186'
results = []
parser = argparse.ArgumentParser()
parser.add_argument('--locales', nargs='+', default=['tr', 'en', 'ru', 'ar', 'de', 'az', 'kk', 'tk', 'uz', 'ky', 'fa'])
args = parser.parse_args()
request = urllib.request.Request(BASE + '/api/account/state', data=b'{}', headers={'Content-Type': 'application/json', 'Origin': BASE}, method='PUT')
try:
    urllib.request.urlopen(request, context=ssl._create_unverified_context(), timeout=15)
    raise AssertionError('Unauthenticated state mutation was accepted')
except urllib.error.HTTPError as error:
    assert error.code in [401, 403], error.code
    print(json.dumps({'unauthenticatedPutStatus': error.code, 'proxyForwardsPut': True}), flush=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    context.add_init_script("window.__nativeTranslationErrors=[];for(const type of ['error','unhandledrejection'])addEventListener(type,e=>{const error=e.error||e.reason;if(error?.translationSource)window.__nativeTranslationErrors.push(error.translationSource);});")
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        for locale in args.locales:
            response = page.goto(BASE + '/?page=categories&lang=' + locale)
            assert response.status == 200, (locale, response.status)
            page.wait_for_load_state('networkidle')
            assert page.locator('#language').input_value() == locale, locale
            expected = 'rtl' if locale in ['ar', 'fa'] else 'ltr'
            assert page.locator('html').get_attribute('dir') == expected, locale
            results.append({'locale': locale, 'status': response.status, 'selected': True, 'direction': expected})
            print(json.dumps(results[-1]), flush=True)
            missing = page.evaluate('() => window.__nativeTranslationErrors')
            if missing: print(json.dumps({'missingTranslation': locale, 'source': missing}), flush=True)
        assert not errors, errors
    finally:
        context.close()
        browser.close()
report = {'locales': results, 'pageErrors': len(errors), 'emptyCatalogOnly': True}
(ROOT / '.local/native-languages.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(report, ensure_ascii=False))
