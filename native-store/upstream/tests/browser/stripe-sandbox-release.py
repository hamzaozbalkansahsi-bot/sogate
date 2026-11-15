"""Read-only live browser smoke for the provider-tested release. Never clicks Pay."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright, expect

R = Path(__file__).resolve().parents[2]
OUT = R / 'artifacts/stripe-sandbox-20261110'
expected = json.loads((OUT / 'release-preparation.json').read_bytes())['releaseHash']
checks = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=str(Path.home() / 'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'))
    for host, width, locale in [('nodenohome.com', 1440, 'tr'), ('nodenohome.com.tr', 390, 'en'), ('nodenohome.com', 390, 'ar')]:
        context = browser.new_context(viewport={'width': width, 'height': 1000 if width > 768 else 844}, is_mobile=width < 768, has_touch=width < 768)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        health = context.request.get('https://' + host + '/api/health').json()
        assert health['releaseHash'] == expected and health['checkoutEnabled'] is True
        page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'));localStorage.setItem('nodeno.cart.v1',JSON.stringify([{id:'2395',quantity:2},{id:'2393',quantity:1}]))")
        page.goto('https://' + host + '/?lang=' + locale + '&page=checkout', wait_until='domcontentloaded')
        expect(page.locator('[data-action=guest-start]')).to_be_visible(timeout=25000)
        expect(page.locator('.payment-totals')).to_be_visible(timeout=25000)
        necessary = page.locator('#insights-banner .insights-actions button').last
        if necessary.is_visible():
            necessary.click()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        page.wait_for_function('() => Array.from(document.querySelectorAll(".checkout-product-photo img")).every(i=>i.complete&&i.naturalWidth>0)')
        assert page.locator('.checkout-product-photo img').count() > 0
        assert not errors, errors
        page.screenshot(path=str(OUT / ('live-' + locale + '-' + str(width) + '.png')), full_page=True)
        checks.append({'host': host, 'width': width, 'locale': locale, 'checkoutRendered': True, 'liveQuoteRendered': True,
                       'noRuntimeErrors': True, 'noOverflow': True, 'productImagesLoaded': True,
                       'direction': page.locator('html').get_attribute('dir')})
        context.close()
    browser.close()
(OUT / 'live-browser.json').write_text(json.dumps({'passed': True, 'checks': checks, 'ordersCreated': 0, 'realCharges': 0}, indent=2) + '\n', encoding='utf8')
print(json.dumps({'passed': True, 'scenarios': len(checks), 'ordersCreated': 0, 'realCharges': 0}))
