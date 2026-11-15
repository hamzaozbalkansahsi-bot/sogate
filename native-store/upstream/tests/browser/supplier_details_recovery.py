"""Read-only product-detail failure/retry acceptance; no checkout mutations."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright, expect

R = Path(__file__).resolve().parents[2]

def verify_recovery(page, origin, locale, supplier, paragraph, translations=None):
    attempts = []
    def details(route):
        attempts.append(route.request.url)
        if len(attempts) == 1:
            route.fulfill(status=503, json={'error': 'temporarily_unavailable'})
        elif len(attempts) == 2:
            route.fulfill(status=200, json={'id': supplier['id'], 'sha256': 'invalid', 'description': {}})
        else:
            route.continue_()
    pattern = '**/api/supplier-products/' + supplier['id'] + '*'
    page.route(pattern, details)
    try:
        page.goto(origin + '/?lang=' + locale + '&product=' + supplier['id'], wait_until='networkidle')
        retry = page.locator('[data-action="retry-supplier-details"]')
        expect(retry).to_be_visible(timeout=12000)
        expect(page.locator('.supplier-detail-status')).to_have_attribute('role', 'alert')
        base_errors={'tr':'Ürün ayrıntıları şu an yüklenemedi.','en':'The product details could not be loaded.','ru':'Не удалось загрузить сведения о товаре.','ar':'تعذّر تحميل تفاصيل المنتج.'}
        expected_error=base_errors.get(locale) or translations['The product details could not be loaded.']
        expect(page.locator('.supplier-detail-status>span')).to_have_text(expected_error)
        assert len(attempts) == 1, 'unexpected automatic retry'
        minimum = supplier.get('quantityPolicy', {}).get('minimum', 1)
        step = supplier.get('quantityPolicy', {}).get('step', 1)
        quantity = minimum + step
        page.locator('#detail-quantity').fill(str(quantity))
        page.locator('#detail-quantity').dispatch_event('change')
        page.locator('#display-currency').select_option('EUR' if locale != 'de' else 'USD')
        expect(retry).to_be_visible()
        assert len(attempts) == 1, 'rerender must not retry without user action'
        retry.click()
        expect(retry).to_be_visible()
        assert len(attempts) == 2, 'invalid response must remain retryable'
        expect(page.locator('#detail-quantity')).to_have_value(str(quantity))
        page.locator('.supplier-detail-status').screenshot(path=str(R/'artifacts/storefront-followup-20261112'/('retry-'+locale+'.png')))
        retry.click()
        expect(page.locator('.product-about')).to_contain_text(paragraph[-70:], timeout=30000)
        expect(page.locator('.supplier-detail-status')).to_have_count(0)
        expect(page.locator('#detail-quantity')).to_have_value(str(quantity))
        assert len(attempts) == 3
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        return {'http503Retry': True, 'invalidResponseRetry': True, 'noAutomaticRetry': True, 'quantityPreserved': True}
    finally:
        page.unroute(pattern, details)

if __name__ == '__main__':
    output = R/'artifacts/storefront-followup-20261112'
    output.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'))
        page = browser.new_page(viewport={'width': 390, 'height': 900}, is_mobile=True)
        page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false')")
        page.route('**/*', lambda route: route.continue_() if route.request.method in ['GET','HEAD'] else route.abort())
        catalog = page.request.get('https://nodenohome.com/api/catalog').json()
        supplier = next(p for p in catalog['products'] if p.get('productType') == 'supplier-item' and p['code'].startswith('ND-ALT'))
        data = page.request.get('https://nodenohome.com/api/supplier-products/'+supplier['id']).json()
        paragraph = next(p.strip() for p in data['description']['tr'].split('\n\n') if len(p.strip()) > 80)
        print(json.dumps(verify_recovery(page, 'https://nodenohome.com', 'tr', supplier, paragraph)), flush=True)
        browser.close()
