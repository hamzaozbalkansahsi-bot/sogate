#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-public-navigation.py
# Açıklama   : NODENO benzeri belgeyi sıfırlamayan kamu gezinmesi ve geri konumunu sınar.
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent;base='https://sexogate.com/test' if '--remote' in sys.argv else 'http://127.0.0.1:3183/test';results=[]
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch(headless=True);context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();page.set_default_navigation_timeout(60000)
  try:
   page.goto(base+'/');page.wait_for_load_state('networkidle');page.locator('#age-accept').click();assert page.locator('#header-query').evaluate('(n)=>parseFloat(getComputedStyle(n).fontSize)>=16'), 'Mobile input zoom risk';button=page.locator('.php-hero .button-light');button.hover();page.wait_for_timeout(250);ratio=button.evaluate('''n=>{const c=getComputedStyle(n),L=s=>{const v=s.match(/[0-9.]+/g).slice(0,3).map(x=>{x=Number(x)/255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4});return .2126*v[0]+.7152*v[1]+.0722*v[2]},a=L(c.color),b=L(c.backgroundColor);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)}''');assert ratio>=4.5,('Hero hover contrast',ratio);page.evaluate('window.__navigationProbe=1234');page.locator('.category-nav a[href$="/urunler"]').click();page.wait_for_url('**/urunler');page.locator('h1').wait_for();assert page.evaluate('window.__navigationProbe')==1234,'Public link reset the document'
   page.get_by_role('button',name='Hızlı incele',exact=True).first.click();page.locator('#quick-product[open]').get_by_role('link',name='Ürünü ve seçenekleri incele',exact=True).wait_for();page.keyboard.press('Escape');assert not page.locator('#quick-product').is_visible()
   page.locator('.product-image-wrap').first.click();page.wait_for_url('**/urun/**');page.locator('[data-image-zoom]').click();page.locator('#image-zoom[open]').wait_for();page.keyboard.press('Escape');assert not page.locator('#image-zoom').is_visible();assert page.evaluate('window.__navigationProbe')==1234
   page.go_back();page.wait_for_url('**/urunler');page.locator('.product-grid').wait_for();assert page.evaluate('window.__navigationProbe')==1234
   page.locator('footer a[href$="/blog"]').click();page.wait_for_url('**/blog');page.locator('.blog-search').wait_for();assert page.evaluate('window.__navigationProbe')==1234
   page.locator('footer a[href$="/yasal/iade"]').first.click();page.wait_for_url('**/yasal/iade');page.locator('.information-prose').wait_for();assert page.evaluate('window.__navigationProbe')==1234
   assert not page.locator('form[action$="/_access"]').count();results.append({'engine':engine,'sameDocument':True,'quickViewAfterNavigation':True,'zoomAfterNavigation':True,'back':True,'blog':True,'legal':True})
  finally:context.close();browser.close()
(root/('.local/php-public-navigation-remote.json' if '--remote' in sys.argv else '.local/php-public-navigation-local.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results))
