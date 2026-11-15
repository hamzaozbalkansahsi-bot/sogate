#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-category-brand.py
# Açıklama   : Logo hizaları, sosyal ikon hareketi ve tam kategori sayfasını tarayıcıda doğrular.
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent.parent
remote = '--remote' in sys.argv
base = 'https://sexogate.com/test' if remote else 'http://127.0.0.1:3183/test'
results = []
with sync_playwright() as p:
    for engine in ['chromium', 'webkit']:
        browser = getattr(p, engine).launch(headless=True)
        try:
            for width in [360, 390, 430, 768, 1440]:
                context = browser.new_context(viewport={'width': width, 'height': 844}, reduced_motion='no-preference')
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                try:
                    page.goto(base + '/')
                    page.wait_for_load_state('networkidle')
                    page.locator('#age-accept').click()
                    header = page.locator('.header-main')
                    brand = header.locator('.brand img')
                    assert abs(brand.bounding_box()['x'] - header.bounding_box()['x']) <= 2, ('Header logo not left aligned', engine, width)
                    padding = brand.evaluate('''async n=>{const text=await(await fetch(n.currentSrc)).text(),svg=new DOMParser().parseFromString(text,'image/svg+xml').documentElement;svg.style.cssText='position:fixed;visibility:hidden;width:100px;height:100px';document.body.append(svg);try{const b=svg.getBBox(),v=svg.viewBox.baseVal;return(b.x-v.x)/v.width}finally{svg.remove()}}''')
                    assert padding <= .04, ('Logo artwork has too much left padding', engine, width, padding)
                    folder = root / ('docs/screenshots/php-category-brand-remote' if remote else 'docs/screenshots/php-category-brand-local')
                    folder.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(folder / f'{engine}-header-{width}.png'))
                    intro = page.locator('.footer-intro')
                    logo = intro.locator('a').first
                    boxes = [n.bounding_box() for n in [intro, logo]]
                    assert abs((boxes[0]['x'] + boxes[0]['width']/2) - (boxes[1]['x'] + boxes[1]['width']/2)) <= 2, ('Footer logo not centered', engine, width)
                    intro.screenshot(path=str(folder / f'{engine}-footer-logo-{width}.png'))
                    social = page.locator('.footer-social a')
                    assert social.count() == 4
                    for a in social.all():
                        assert a.locator('svg[aria-hidden="true"]').count() == 1, a.inner_text()
                        assert not a.inner_text().strip(), 'Social links must contain icons only'
                        assert a.get_attribute('aria-label') in ['Instagram','Facebook','X','TikTok']
                        assert a.get_attribute('rel') == 'noopener noreferrer'
                    first = social.first
                    first.hover()
                    page.wait_for_timeout(300)
                    assert first.evaluate('n=>getComputedStyle(n).transform') != 'none', 'Missing hover movement'
                    first.focus()
                    page.keyboard.press('Tab')
                    page.keyboard.press('Shift+Tab')
                    first.focus()
                    assert first.evaluate('n=>getComputedStyle(n).outlineStyle') != 'none'
                    context_reduced = browser.new_context(viewport={'width': width, 'height': 844}, reduced_motion='reduce')
                    try:
                        reduced = context_reduced.new_page()
                        reduced.goto(base + '/')
                        reduced.locator('#age-accept').click()
                        reduced.locator('.footer-social a').first.hover()
                        assert reduced.locator('.footer-social a').first.evaluate('n=>getComputedStyle(n).transform') == 'none'
                    finally:
                        context_reduced.close()
                    page.evaluate('window.__categoryProbe=321')
                    if width <= 700:
                        nav = page.locator('.mobile-bottom-nav')
                        assert nav.locator(':scope > a').count() == 5
                        assert nav.locator('button').count() == 0
                        assert nav.locator('a').nth(4).get_attribute('href').endswith('/hesap')
                        nav.locator('a').nth(1).click()
                    else:
                        page.locator('.category-nav a[href$="/kategoriler"]').click()
                    page.wait_for_url('**/kategoriler')
                    page.locator('.category-tile-grid').wait_for()
                    assert page.locator('h1').inner_text() == 'Tüm kategoriler'
                    assert not page.locator('dialog[open]').count()
                    assert page.evaluate('window.__categoryProbe') == 321
                    assert page.locator('body').get_attribute('data-page') == 'categories'
                    assert page.locator('.category-view-all').inner_text().strip().startswith('Tüm ürünler')
                    assert page.locator('.category-tile-grid a').count() > 0
                    if width <= 700:
                        assert len(page.locator('.category-tile-grid').evaluate('n=>getComputedStyle(n).gridTemplateColumns').split()) == 2
                        assert not page.locator('.site-header .brand').is_visible()
                        assert not page.locator('footer').is_visible()
                        assert page.locator('.mobile-bottom-nav a').nth(1).get_attribute('aria-current') == 'page'
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    folder = root / ('docs/screenshots/php-category-brand-remote' if remote else 'docs/screenshots/php-category-brand-local')
                    folder.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(folder / f'{engine}-categories-{width}.png'))
                    page.go_back()
                    page.wait_for_url(base + '/')
                    page.locator('.php-hero').wait_for()
                    assert page.locator('.site-header .brand').is_visible()
                    if width <= 700:
                        assert page.locator('.mobile-bottom-nav a').first.get_attribute('aria-current') == 'page'
                    page.evaluate("scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})")
                    page.screenshot(path=str(folder / f'{engine}-footer-{width}.png'))
                    results.append({'engine': engine, 'width': width, 'logoAlignment': True, 'socialIconsMotion': True, 'reducedMotion': True, 'fullCategoryPage': True, 'history': True})
                finally:
                    context.close()
        finally:
            browser.close()
(root / ('.local/php-category-brand-remote.json' if remote else '.local/php-category-brand-local.json')).write_text(json.dumps(results, indent=2), encoding='utf8')
print(json.dumps(results))
