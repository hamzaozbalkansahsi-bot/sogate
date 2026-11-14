#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-public-browser.py
# Açıklama   : Hesapsız yetişkin girişini, görünür kredinin yokluğunu ve gerçek uygulama ikonlarını iki motorda sınar.
import json,struct,sys
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent;remote='--remote' in sys.argv
base='https://sexogate.com/test' if remote else 'http://127.0.0.1:3183/test'
folder=root/('docs/screenshots/php-public-remote' if remote else 'docs/screenshots/php-public-local');folder.mkdir(parents=True,exist_ok=True);results=[]
with sync_playwright() as p:
    for engine in ['chromium','webkit']:
        browser=getattr(p,engine).launch(headless=True)
        try:
            for width in [360,390,430,768,1440]:
                context=browser.new_context(viewport={'width':width,'height':900 if width>=768 else 844},reduced_motion='reduce');page=context.new_page();page.set_default_navigation_timeout(60000 if remote else 30000)
                try:
                    response=page.goto(base+'/');assert response.status==200;page.wait_for_load_state('networkidle');page.locator('#age-notice[open]').wait_for()
                    assert page.locator('form[action$="/_access"]').count()==0
                    assert page.locator('#age-notice').evaluate('(n)=>n.scrollWidth<=n.clientWidth+1'),'Age dialog overflows horizontally'
                    assert page.locator('#age-accept').is_visible();assert page.locator('#age-exit').is_visible()
                    assert 'PTYS Technoligess' not in page.locator('body').inner_text();assert 'Hamza ÖZBALKAN' not in page.locator('body').inner_text()
                    page.screenshot(path=str(folder/f'{engine}-age-{width}.png'),full_page=False)
                    page.locator('#age-accept').click();assert not page.locator('#age-notice').is_visible();assert page.url==base+'/';assert page.evaluate('scrollY')==0,'Age confirmation must keep the header in view';page.locator('h1').wait_for();assert page.locator('h1').inner_text()=='Tutkunu Keşfet.'
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Storefront overflows horizontally'
                    if width in [390,1440]:page.screenshot(path=str(folder/f'{engine}-home-{width}.png'),full_page=True)
                    page.reload();page.wait_for_load_state('networkidle');assert not page.locator('#age-notice').is_visible();assert not any(c['name']=='sg_stage' for c in context.cookies())
                    manifest=page.request.get(base+'/manifest.webmanifest');assert manifest.status==200;data=manifest.json();assert data['display']=='standalone';assert data['scope']=='/test/'
                    for icon in data['icons']:
                        image=page.request.get(urljoin(base+'/',icon['src']));assert image.status==200;raw=image.body();assert raw[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',raw[16:24]);assert icon['sizes']==f'{w}x{h}'
                    assert page.locator('link[rel="apple-touch-icon"]').get_attribute('sizes')=='180x180'
                    assert page.request.get(base+'/api/admin/catalog').status==401
                    results.append({'engine':engine,'width':width,'publicWithoutAccount':True,'ageRemembered':True,'creditHidden':True,'manifestAndPngIcons':True,'adminProtected':True})
                finally:context.close()
        finally:browser.close()
(root/('.local/php-public-browser-remote.json' if remote else '.local/php-public-browser-local.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results))
